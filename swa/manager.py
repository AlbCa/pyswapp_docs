import sys
import time
import copy

from .utils import *
from .stream import SeismicStream
from .curve import DispersionCurve
from .curves import CombineCurves

# TODO: test on field data
# TODO: error handling: e.g., when requesting data from database always check whether its empty or not!
# TODO: dynamic/static plotting (?)
# TODO: documentation
# TODO: simplify the use of the procsets?
# TODO: keep copy of raw dispersion curves before filtering [check]
# TODO: read/save curves to provide individual procsets! [check] -> parameter new_procset can be set

class BaseManager:
    def __init__(self, prjdir, path2raw, path2geom, settings=None, database='swa.db'):
        """
        Base manager class for surface wave analysis

        Parameters
        ----------
        prjdir : str, project directory
        path2raw : str, path to the raw seismic data
        path2geom : str, path to the geometry file
        settings : DataFrame, settings for the processing and visualisation
        database : str, name of the database
        """

        self.prjdir = prjdir
        self.path2raw = path2raw
        self.path2geom = path2geom

        self.settings = settings

        self.fileList, self.ext = get_fileList(self.path2raw)

        self.database = database

        self._init_params()

        self.path2db = os.path.join(self.prjdir, self.database)

        # create/load project
        if os.path.isfile(self.path2db):
            self._load_project()
        else:
            self._create_project()

    def _create_project(self):
        """Create the project directory and database"""

        print('Creating project:')
        # set up project directory
        subdirs = ['proc','plot']

        for sd in subdirs:
            safe_makedirs(os.path.join(self.prjdir, sd))

        self._sql = SQL(database=self.path2db)

        # survey geometry
        self._sql.read_geometry(self.path2geom)

        # processing settings
        if self.settings is None:
            self.settings = create_settings()
        self._sql.read_setting(self.settings)

        # seismic data
        self._read_data()

        print('\nExisting procsets:', *self._sql.get_proc_labels())

        # set procset
        self.set_procset_label(procset='proc1')
        self._sql.show_tables()

        print('')

    def _load_project(self):
        """Load the project"""

        print('Loading project:')
        self._sql = SQL(database=self.path2db)
        self.settings = self._sql.get_table('settings')
        # self._sql.show_tables()
        self._read_data()

        prc_sets = self._sql.get_proc_labels()
        print('\nExisting procsets:', *prc_sets)

        # set/load procset label
        if 'amps' in self._sql.get_tables():
            if len(prc_sets) > 1:
                self.set_procset_label(procset=prc_sets[-1])
            else:
                self.set_procset_label(procset='proc1')
        else:
            self.set_procset_label(procset='proc1')

        # load processed data
        if 'amps' in self._sql.get_tables():
            if len(prc_sets) > 1:
                self.load_procset(prc_sets[-1])
            else:
                self.load_procset('raw')

        print('')

    def _init_params(self):
        """initialize some parameters"""

        # dictionary storing stream stream data
        self.data = {}

        # procset label
        self._procset = None

        # current stream
        self.current_stream = None
        self.selected_ids = (1, 1)

    def set_procset_label(self, procset, verbose = True):
        """set the active processing name"""
        if procset != 'raw':
            self._procset = procset
            if verbose:
                print('Active procset label: %s' % procset)
        else:
            self._procset = 'proc1'
            if verbose:
                print('Active procset label should be different from "raw". Setting to default label "proc1".')

    def load_procset(self, procset, **kwargs):
        """load processed data from database"""

        print('Loading amplitude data from "%s" ..... ' % procset, end="")
        starttime = time.time()

        # data = self.data
        shots = self._sql.get_table('shots')

        for i in range(len(shots)):

            sin = shots.loc[i, 'sin']
            rep = shots.loc[i, 'rep']

            data = self.data
            if sin in data.keys():
                if rep in data[sin].keys():
                    self._set_data(self.data[sin][rep], sin, rep, procset=procset)
                    self._set_FV(self.data[sin][rep], sin, rep, procset=procset, **kwargs)

        endtime = time.time()
        print(f'{np.round(endtime - starttime, 2)} s')

    def _get_filepath(self, sin, rep=1):
        """Return the file path corresponding to the indices sin and rep as string"""
        if self.fileList is not None:
            sn = self._sql.get_shotfile(sin, rep).shots.item()
            for i, fn in enumerate(self.fileList):
                sfn = re.findall(r'\d+', fn.replace(self.ext, ''))[0]
                if str(sn) == str(sfn):
                    return fn
        return None

    def _read_data(self):
        """Initialize stream objects for all seismic shot files in the geometry file and apply the survey geometry"""

        shts = self._sql.get_table('shots')
        self.data = {}

        print('Reading seismic shot files .....', end="")
        starttime = time.time()

        nfiles = 0
        for i in shts.index:
            sin = shts.loc[i, 'sin']
            rep = shts.loc[i, 'rep']
            fn = self._get_filepath(sin, rep)

            if fn is not None:
                sht_geom, rec_geom = self._sql.get_geometry(sin, rep)
                st = SeismicStream(fn, settings=self.settings)
                st.apply_geometry(sht_geom, rec_geom)

                if sin not in self.data.keys():
                    self.data[sin] = {}

                self.data[sin][rep] = st
                nfiles += 1

                if sin in self.data.keys():
                    if rep in self.data[sin].keys():
                        self._write_data(self.data[sin][rep], sin, rep, 'raw')

        endtime = time.time()
        print(f' {np.round(endtime - starttime, 2)} s')
        print(f'Read {nfiles} files and applied geometry and settings.')

    def print_stats(self, which = 'stream'):
        """print stream information"""

        stream = self.current_stream
        stream.print_stats(which)

    def _write_data(self, data, sin, rep, procset, wid=-1):
        """write processed data to database"""
        self._sql.write_data(data, sin, rep, procset, wid)

    def _write_FV(self, data, sin, rep, procset, wid=-1):
        """write FV to database"""
        self._sql.write_FV(data, sin, rep, procset, wid)

    def _get_data(self, sin, rep, procset, wid=-1):
        """get processed data from database"""
        par, amps, recs, sht = self._sql.read_data(sin, rep, procset=procset, wid=wid)

        return par, amps, recs, sht

    def _get_FV(self, sin, rep, procset, wid=-1, method='phaseshift'):
        """get FV data from database"""

        vel, kw, freq, FV = self._sql.read_FV(sin, rep, procset=procset, wid=wid, method=method)
        return vel, kw, freq, FV

    def _set_data(self, data, sin, rep, procset, wid=-1):
        """set processed data from database to current stream"""

        par, amps, recs, sht = self._get_data(sin, rep, procset=procset, wid=wid)
        amps_ari = amps.values.transpose()
        if not amps.empty:
            data.update_pst(amps_ari, sht, recs, par)

    def _set_FV(self, data, sin, rep, procset, wid=-1, method='phaseshift'):
        """set FV data from database to current stream"""

        vel, kw, freq, FV = self._get_FV(sin, rep, procset=procset, wid=wid, method=method)
        if FV is not None:
            data.update_FV(method, vel, kw, freq, FV)

    # %% Processing
    def select_data(self, sin=1, rep=1, inplace=True, verbose = True):
        """Select one stream object based on source location and shot repetition indices"""

        data = self.data

        if sin in data.keys():
            if rep in data[sin].keys():
                selection = data[sin][rep]

                self.selected_ids = (sin, rep)

                if inplace:
                    self.current_stream = selection
                    if verbose:
                        print(f'Currently selected data: (SIN,REP) = ({self.selected_ids[0]}, {self.selected_ids[1]})')
                return selection
            else:
                raise KeyError(f'The key rep = {rep} does not exist for sin = {sin}.')
        else:
            raise KeyError(f'The key sin = {sin} does not exist.')

    def preprocess(self, attr, procset = None, use_windows = False, **kwargs):
        """apply preprocessing steps to current selection or all data sets"""

        if procset is None:
            procset = self._procset
        elif procset != self._procset:
            self.set_procset_label(procset)

        sin = self.selected_ids[0]
        rep = self.selected_ids[1]
        stream = self.current_stream

        wids = self._sql.get_wids(sin, rep, procset)
        if use_windows:
            if len(wids) > 0:
                for wid in wids:
                    tmp = copy.deepcopy(stream)
                    self._set_data(tmp, sin, rep, procset, wid)
                    func = getattr(tmp, attr)
                    func(**kwargs)
                    self._write_data(tmp, sin,rep, procset, wid)
        else:
            func = getattr(stream, attr)
            func(**kwargs)
            self.data[sin][rep] = stream
            self._write_data(stream, sin, rep, procset, wid = -1)

    def transform(self, method, procset = None, use_windows = False, **kwargs):
        """apply wavefield transformation to current selection or all data sets"""

        if procset is None:
            procset = self._procset
        elif procset != self._procset:
            self.set_procset_label(procset)

        sin = self.selected_ids[0]
        rep = self.selected_ids[1]
        stream = self.current_stream

        wids = self._sql.get_wids(sin, rep, procset)
        if use_windows:
            if len(wids) > 0:
                for wid in wids:

                    tmp = copy.deepcopy(stream)
                    self._set_data(tmp, sin, rep, procset, wid)
                    tmp.transform(method=method, **kwargs)
                    self._write_FV(tmp,  sin, rep, procset, wid)
        else:
            stream.transform(method=method, **kwargs)
            self.data[sin][rep] = stream
            self._write_FV(stream, sin, rep, procset, wid = -1)

    def _extract(self, stream, pck_mode, sin, rep, procset, wid, **kwargs):
        """extract a dispersion curve and write to database"""

        try:
            stream.dcpicking(pck_mode=pck_mode, **kwargs)
        except:
            warnings.warn('No dispersion image generated prior to dispersion curve extraction. '
                          'Dispersion curve extraction not possible.')
            pass

        method = stream.trafo_type
        xmid = stream.midpoint

        for pck_mode in stream.picks.keys():
            for dc_mode in stream.picks[pck_mode].keys():
                dc = {
                    'xmid': xmid,
                    'method': method,
                    'dc_mode': dc_mode,
                    'f': stream.picks[pck_mode][dc_mode]['f'],
                    'v': stream.picks[pck_mode][dc_mode]['v'],
                    'err': np.zeros(len(stream.picks[pck_mode][dc_mode]['v']))}

                self._sql.write_curve(dc, sin, rep, procset, wid, xmid)

    def extract(self, procset = None, use_windows = False,  pck_mode = 'auto', **kwargs):
        """apply dispersion curve picking to a stream"""

        if procset is None:
            procset = self._procset
        elif procset != self._procset:
            self.set_procset_label(procset)

        sin = self.selected_ids[0]
        rep = self.selected_ids[1]
        stream = self.current_stream

        method = stream.trafo_type
        self._set_data(stream, sin, rep, procset)
        self._set_FV(stream, sin, rep, procset=procset, method=method)

        wids = self._sql.get_wids(sin, rep, procset)
        if use_windows:
            for wid in wids:
                tmp = copy.deepcopy(stream)
                self._set_data(tmp, sin, rep, procset, wid)
                self._set_FV(tmp, sin, rep, procset, wid)
                self._extract(tmp,pck_mode, sin = sin, rep = rep, wid = wid, procset=procset, **kwargs)
        else:
            self._extract(stream, pck_mode, sin=sin, rep=rep, wid=-1, procset=procset, **kwargs)

    def _process_curve(self, attr, params, method = 'method', procset = None, new_procset = None, **kwargs):
        """apply a process to the dispersion curve data"""

        if procset is None:
            procset = self._procset

        if (new_procset is None) or (new_procset == 'raw'):
            new_procset = procset
        # elif procset != self._procset:
        #     self.set_procset_label(procset)

        curve_data = self._sql.read_curve(params)

        dc = DispersionCurve()
        dc.init_data(curve_data['frequency'], curve_data['velocity'], curve_data['error'])
        func = getattr(dc, attr)
        dc = func(**kwargs)

        xmids = curve_data['xmid'].unique()#item()

        for xmid in xmids:
            dc = {
                'xmid': xmid,
                'method': method,
                'dc_mode': params['dc_mode'],
                'f': dc.frequency,
                'v': dc.velocity,
                'err': dc.error}

            self._sql.write_curve(dc, params['sin'], params['rep'], new_procset, params['wid'], xmid)

    def process_curve(self, attr, procset=None, method='tomo2D', dc_mode=0, use_windows = False, **kwargs):
        """apply a process to a dispersion curve"""

        if procset is None:
            procset = self._procset
        # elif procset != self._procset:
        #     self.set_procset_label(procset)

        sin = self.selected_ids[0]
        rep = self.selected_ids[1]

        wids = self._sql.get_wids(sin, rep, procset)
        if use_windows:
            for wid in wids:

                params = {'procset': "'%s'" % procset, 'method': "'%s'" % method, 'dc_mode': dc_mode,
                          'sin': sin, 'rep': rep, 'wid': wid}
                self._process_curve(attr, params, method, procset=procset, **kwargs)
        else:
            params = {'procset': "'%s'" % procset, 'method': "'%s'" % method, 'dc_mode': dc_mode,
                      'sin': sin, 'rep': rep, 'wid': -1}
            self._process_curve(attr, params, method, procset=procset, **kwargs)

    def _save_curve(self, path2dc, name, params, format = 'csv', **kwargs):
        """save a dispersion curve"""

        curve_data = self._sql.read_curve(params)

        if curve_data.empty:
            return None
        else:
            dc = DispersionCurve()
            dc.init_data(curve_data['frequency'], curve_data['velocity'], curve_data['error'])
            dc.save(path2dc, name, format=format, **kwargs)
            return curve_data['xmid'].unique().item()

    def save_curve(self, procset=None, method='tomo2D', dc_mode=0, use_windows = False, **kwargs):
        """save a dispersion curve for a defined source location, repetition and window id"""

        if procset is None:
            procset = self._procset

        sin = self.selected_ids[0]
        rep = self.selected_ids[1]

        dir = os.path.join(self.prjdir, f'proc/{procset}/{method}')

        xmids = []
        wids = self._sql.get_wids(sin, rep, procset)
        if use_windows:
            for wid in wids:
                name = 'dc_sin%d-rep%d-wid%d' % (sin,rep,wid)
                params = {'procset': "'%s'" % procset, 'method': "'%s'" % method, 'dc_mode': dc_mode,
                          'sin': sin, 'rep': rep, 'wid': wid}
                xmid = self._save_curve(dir, name, params, **kwargs)
                if xmid is not None:
                    xmids.append(xmid)
        else:
            name = 'dc_sin%d-rep%d' % (sin, rep)
            params = {'procset': "'%s'" % procset, 'method': "'%s'" % method, 'dc_mode': dc_mode,
                      'sin': sin, 'rep': rep, 'wid': -1}
            xmid = self._save_curve(dir, name, params, **kwargs)
            if xmid is not None:
                xmids.append(xmid)

        return xmids

    def plot(self, attr='seismogram', procset = None, use_windows = False, **kwargs):
        """plot portions of the stream data"""

        if procset is None:
            procset = self._procset

        sin = self.selected_ids[0]
        rep = self.selected_ids[1]
        stream = self.current_stream

        method = kwargs.pop('method', 'phaseshift')
        if attr in ['dispersionImage', 'dispersionImageComposite']:
            self._set_FV(stream, sin, rep, procset=procset, method=method)

        wids = self._sql.get_wids(sin, rep, procset)
        if use_windows:
            for wid in wids:
                tmp = copy.deepcopy(stream)
                self._set_data(tmp, sin, rep, procset, wid)

                if attr in ['dispersionImage','dispersionImageComposite']:
                    self._set_FV(tmp, sin, rep, procset=procset, method=method, wid=wid)

                tmp.plot(attr, **kwargs)
        else:
            stream.plot(attr, **kwargs)

    def plot_curve(self, procset=None, method='phaseshift', dc_mode=0, use_windows = False, **kwargs):
        """plot a dispersion curve"""

        if procset is None:
            procset = self._procset

        sin = self.selected_ids[0]
        rep = self.selected_ids[1]

        wids = self._sql.get_wids(sin, rep, procset)
        if use_windows:
            for wid in wids:
                params = {'procset': "'%s'" % procset, 'method': "'%s'" % method, 'dc_mode': "%d" % dc_mode,
                          'sin': sin, 'rep': rep, 'wid': wid}
                curve_data = self._sql.read_curve(params)
                dc = DispersionCurve()
                dc.init_data(curve_data['frequency'], curve_data['velocity'], curve_data['error'])
                dc.plot(**kwargs)
        else:
            params = {'procset': "'%s'" % procset, 'method': "'%s'" % method, 'dc_mode': "%d" % dc_mode,
                      'sin': sin, 'rep': rep, 'wid': -1}
            curve_data = self._sql.read_curve(params)
            dc = DispersionCurve()
            dc.init_data(curve_data['frequency'], curve_data['velocity'], curve_data['error'])
            dc.plot(**kwargs)

    def plot_pseusodsection(self, procset=None, method='tomo2D', dc_mode=0, cmap='viridis', **kwargs):
        """plot the Rayleigh wave phase velocity pseudosection"""

        if procset is None:
            procset = self._procset

        _, recs_all = self._sql.get_geometry(sin = '*')
        params = {'procset': "'%s'" % procset, 'method': "'%s'" % method, 'dc_mode': "%d" % dc_mode}

        curves = self._sql.read_curve(params)

        if not curves.empty:

            xmids = curves['xmid'].unique()

            vmin = kwargs.pop('vmin', 200)
            vmax = kwargs.pop('vmax', 500)

            fmin = curves['frequency'].min()
            fmax = curves['frequency'].max()

            title = kwargs.pop('title', '')

            fig, ax = plt.subplots()
            for xmid in xmids:
                params = {'procset': "'%s'" % procset, 'method': "'%s'" % method, 'dc_mode': "%d" % dc_mode,
                          'xmid': xmid}
                sub = self._sql.read_curve(params)

                dc = DispersionCurve()
                dc.init_data(sub['frequency'], sub['velocity'], sub['error'])

                dc.plotColumn(axes=ax,
                              xmid=xmid,
                              vmin=vmin, vmax=vmax,
                              cmap=cmap, y_value='f',
                              width=0.5, **kwargs)

            plot_colorBar(ax, vmin, vmax, cmap=cmap, orientation='vertical')
            ax.set_xlim([recs_all['rx'].min(), recs_all['rx'].max()])
            ax.set_ylim([fmin, fmax])

            ax.set_title(title)
            plt.show()
        else:
            warnings.warn('No dispersion curves in data base. Pseudosection not visualised')

class MASW2DManager(BaseManager):
    def __init__(self, prjdir, path2raw, path2geom, settings = None, database = 'swa.db'):
        """
        MASW 2D manager class for surface wave analysis

        Parameters
        ----------
        prjdir : str, project directory
        path2raw : str, path to the raw seismic data
        path2geom : str, path to the geometry file
        settings : DataFrame, settings for the processing and visualisation
        database : str, name of the database
        """

        super().__init__(prjdir, path2raw, path2geom, settings, database)
        self.CC = None

    def plot_streams(self, attr='seismogram', procset = None, apply_to = 'all', use_windows=False, **kwargs):
        """Plot the stream data"""

        # Apply process to current selection only
        if apply_to == 'cur':
            if self.current_stream is None:
                self.select_data(inplace = True, verbose=False)

            self.plot(attr,procset=procset, use_windows=use_windows, **kwargs)

        # Apply process to all data sets
        elif apply_to == 'all':
            for sin in self.data.keys():
                for rep in self.data[sin].keys():
                    self.select_data(sin, rep, inplace=True, verbose=False)
                    self.plot(attr, procset=procset, use_windows=use_windows,**kwargs)

    def preprocess_streams(self, attr='trim', procset = None, apply_to = 'all', use_windows=False, **kwargs):
        """apply preprocessing steps to current selection or all data sets"""

        # # check if process exists
        # if attr not in ['filter', 'trim']:
        #     raise AttributeError(f'Attribute can be "filter" or "trim" not {attr}.')

        # Apply process to current selection only
        if apply_to == 'cur':
            if self.current_stream is None:
                self.select_data(inplace = True, verbose=False)

            starttime = time.time()
            print(f'Applying {attr} to (SIN,REP) = ({self.selected_ids[0]}, {self.selected_ids[1]}) ..... ', end='')

            self.preprocess(attr,procset=procset, use_windows=use_windows, **kwargs)

            endtime = time.time()
            print(f'{np.round(endtime - starttime, 2)} s')

        # Apply process to all data sets
        elif apply_to == 'all':
            starttime = time.time()

            for sin in self.data.keys():
                for rep in self.data[sin].keys():

                    self.select_data(sin, rep, inplace=True, verbose=False)

                    sys.stdout.write(f'\rApplying {attr} to (SIN,REP) = ({sin}, {rep}) ..... ')
                    sys.stdout.flush()

                    self.preprocess(attr,procset=procset, use_windows=use_windows, **kwargs)

            endtime = time.time()
            print(f'{np.round(endtime - starttime, 2)} s')

    def transform_streams(self, attr='phaseshift', procset = None, apply_to = 'all', use_windows=False, **kwargs):
        """apply wavefield transformation to current selection or all data sets"""

        # Apply process to current selection only
        if apply_to == 'cur':
            if self.current_stream is None:
                self.select_data(inplace = True, verbose=False)

            starttime = time.time()
            print(f'Applying {attr} transformation to (SIN,REP) = ({self.selected_ids[0]}, {self.selected_ids[1]})'
                  f' ..... ', end = '')
            self.transform(attr,procset=procset, use_windows=use_windows, **kwargs)

            endtime = time.time()
            print(f'{np.round(endtime - starttime, 2)} s')

        # Apply process to all data sets
        elif apply_to == 'all':
            starttime = time.time()

            for sin in self.data.keys():
                for rep in self.data[sin].keys():

                    self.select_data(sin, rep, inplace=True, verbose=False)

                    sys.stdout.write(f'\rApplying {attr} transformation to (SIN,REP) = ({sin}, {rep}) ..... ')
                    sys.stdout.flush()

                    self.transform(attr, procset=procset, use_windows=use_windows,**kwargs)

            endtime = time.time()
            print(f'{np.round(endtime - starttime, 2)} s')

    def extract_curves(self, procset = None, pck_mode='auto', apply_to = 'all', use_windows=False, **kwargs):

        # Apply process to current selection only
        if apply_to == 'cur':
            if self.current_stream is None:
                self.select_data(inplace = True, verbose=False)

            starttime = time.time()
            print(f'Dispersion curve extraction of (SIN,REP) = ({self.selected_ids[0]}, {self.selected_ids[1]})'
                  f' ..... ', end = '')
            self.extract(procset=procset,use_windows=use_windows, pck_mode = pck_mode, **kwargs)

            endtime = time.time()
            print(f'{np.round(endtime - starttime, 2)} s')

        # Apply process to all data sets
        elif apply_to == 'all':
            starttime = time.time()

            for sin in self.data.keys():
                for rep in self.data[sin].keys():

                    self.select_data(sin, rep, inplace=True, verbose=False)

                    sys.stdout.write(f'\rDispersion curve extraction of (SIN,REP) = ({sin}, {rep}) ..... ')
                    sys.stdout.flush()

                    self.extract(procset=procset,use_windows=use_windows, pck_mode=pck_mode, **kwargs)

            endtime = time.time()
            print(f'{np.round(endtime - starttime, 2)} s')

    def process_curves(self, attr='smooth', procset = None, method = 'phaseshift',
                       dc_mode = 0, apply_to = 'all', use_windows=False, **kwargs):
        """process the dispersion curves"""

        # Apply process to current selection only
        if apply_to == 'cur':
            if self.current_stream is None:
                self.select_data(inplace = True, verbose=False)

            starttime = time.time()
            print(f'Applying {attr} to dispersion curve of (SIN,REP) = ({self.selected_ids[0]}, {self.selected_ids[1]})'
                  f' ..... ', end = '')
            self.process_curve(attr=attr, procset=procset, method=method,
                               dc_mode=dc_mode, use_windows = use_windows, **kwargs)
            endtime = time.time()
            print(f'{np.round(endtime - starttime, 2)} s')

        # Apply process to all data sets
        elif apply_to == 'all':
            starttime = time.time()

            for sin in self.data.keys():
                for rep in self.data[sin].keys():

                    self.select_data(sin, rep, inplace=True, verbose=False)

                    sys.stdout.write(f'\rApplying {attr} to dispersion curve of (SIN,REP) = ({sin}, {rep}) ..... ')
                    sys.stdout.flush()

                    self.process_curve(attr=attr, procset=procset, method=method,
                                       dc_mode=dc_mode, use_windows=use_windows, **kwargs)

            endtime = time.time()
            print(f'{np.round(endtime - starttime, 2)} s')

    def plot_curves(self, procset = None, method = 'phaseshift',
                       dc_mode = 0, apply_to = 'all', use_windows=False,**kwargs):
        """process the dispersion curves"""

        # Apply process to current selection only
        if apply_to == 'cur':
            if self.current_stream is None:
                self.select_data(inplace = True, verbose=False)

            self.plot_curve(procset=procset, method=method,dc_mode=dc_mode, use_windows=use_windows,**kwargs)

        # Apply process to all data sets
        elif apply_to == 'all':
            for sin in self.data.keys():
                for rep in self.data[sin].keys():
                    self.select_data(sin, rep, inplace=True, verbose=False)

                    self.plot_curve(procset=procset, method=method,
                                       dc_mode=dc_mode, use_windows=use_windows,**kwargs)

    def save_curves(self, procset = None, method = 'phaseshift',
                       dc_mode = 0, apply_to = 'all', use_windows=False, **kwargs):
        """process the dispersion curves"""

        dir = os.path.join(self.prjdir, f'proc/{procset}/{method}')
        path2geom = os.path.join(dir, '1_geom')
        safe_makedirs(path2geom)

        xmids = []

        # Apply process to current selection only
        if apply_to == 'cur':
            if self.current_stream is None:
                self.select_data(inplace = True, verbose=False)

            starttime = time.time()
            print(f'Save dispersion curves corresponding to (SIN,REP) = ({self.selected_ids[0]}, {self.selected_ids[1]})'
                  f' to file ..... ', end = '')
            xmid = self.save_curve(procset=procset, method=method,dc_mode=dc_mode, use_windows=use_windows, **kwargs)
            xmids += xmid
            endtime = time.time()
            print(f'{np.round(endtime - starttime, 2)} s')

        # Apply process to all data sets
        elif apply_to == 'all':
            starttime = time.time()

            for sin in self.data.keys():
                for rep in self.data[sin].keys():

                    self.select_data(sin, rep, inplace=True, verbose=False)

                    sys.stdout.write(f'\rSave dispersion curves corresponding to (SIN,REP) = '
                          f'({sin}, {rep}) to file ..... ')
                    sys.stdout.flush()

                    xmid = self.save_curve(procset=procset, method=method,dc_mode=dc_mode, use_windows=use_windows, **kwargs)
                    xmids += xmid

            endtime = time.time()
            print(f'{np.round(endtime - starttime, 2)} s')

        # save the xmids to file
        np.savetxt(os.path.join(path2geom, 'xmid.txt'), xmids)

    # %% WINDOWING
    def moving_window(self, procset = None, apply_to = 'all', **kwargs):
        """apply windowing to current selection or all data sets"""

        if procset is None:
            procset = self._procset
        elif procset != self._procset:
            self.set_procset_label(procset)

        # Apply process to current selection only
        if apply_to == 'cur':
            if self.current_stream is None:
                self.select_data(inplace = True, verbose=False)

            starttime = time.time()
            print(f'Moving window along (SIN,REP) = ({self.selected_ids[0]}, {self.selected_ids[1]}) ..... ', end='')

            windows = self.current_stream.moving_window(**kwargs)

            for wid in windows.keys():
                self._write_data(windows[wid], self.selected_ids[0],self.selected_ids[1], procset, wid)

            endtime = time.time()
            print(f'{np.round(endtime - starttime, 2)} s')

        # Apply process to all data sets
        elif apply_to == 'all':
            starttime = time.time()

            for sin in self.data.keys():
                for rep in self.data[sin].keys():

                    sys.stdout.write(f'\rMoving window along (SIN,REP) = ({sin}, {rep}) ..... ')
                    sys.stdout.flush()

                    current_stream = self.select_data(sin=sin, rep=rep, inplace=False, verbose=False)
                    windows = current_stream.moving_window(**kwargs)

                    for wid in windows.keys():
                        self._write_data(windows[wid], sin, rep, procset, wid)

            endtime = time.time()
            print(f'{np.round(endtime - starttime, 2)} s')

    # %% curve combination
    def prepare_CC(self, procset = None, dc_mode = 0, use_windows=False, **kwargs):
        """prepare data for curve combination"""

        if procset is None:
            procset = self._procset
        elif procset != self._procset:
            self.set_procset_label(procset)

        color = kwargs.pop('color', 'dodgerblue')

        params = {'procset': "'%s'" % procset, 'dc_mode': dc_mode}

        if 'method' in kwargs:
            params['method'] = "'%s'" % kwargs['method']
            kwargs.pop('method')

        path2cmb = os.path.join(self.prjdir, f'proc/{procset}/cmb')
        safe_makedirs(path2cmb)

        self.CC = CombineCurves(path2cmb=path2cmb)  # location where combined dcs shall be stored

        for sin in self.data.keys():
            for rep in self.data[sin].keys():

                wids = self._sql.get_wids(sin, rep, procset)
                if use_windows:
                    for wid in wids:
                        params['sin'] = sin
                        params['rep'] = rep
                        params['wid'] = wid

                        curve_data = self._sql.read_curve(params)

                        dc = DispersionCurve()
                        dc.init_data(curve_data['frequency'], curve_data['velocity'], curve_data['error'])

                        for xmid in curve_data['xmid'].unique():
                            self.CC.append(dc, xmid, source=None, color=color)

                else:
                    params['sin'] = sin
                    params['rep'] = rep
                    params['wid'] = -1

                    curve_data = self._sql.read_curve(params)

                    dc = DispersionCurve()
                    dc.init_data(curve_data['frequency'], curve_data['velocity'], curve_data['error'])
                    self.CC.append(dc, curve_data['xmid'].unique().item(), source=None, color=color)

    def combine(self, procset = None, dc_mode = 0, use_windows=False, **kwargs):
        """combine dispersion curves with same receiver spread location"""

        if self.CC is None:
            self.prepare_CC(procset, dc_mode, use_windows, **kwargs)

        starttime = time.time()
        print(f'Combining dispersion curves ..... ', end='')

        self.CC.combine_all(**kwargs)

        endtime = time.time()
        print(f'{np.round(endtime - starttime, 2)} s')

        # write data to database
        for key in self.CC.data.keys():
            # mean dispersion curve after combination
            dc = self.CC.data[key]['cmb']
            data = {
                'xmid': key,
                'method': 'tomo2D',
                'dc_mode': 0,
                 'f': dc.frequency,
                 'v': dc.velocity,
                 'err': dc.error}

            self._sql.write_curve(data, -1, -1, procset=procset, wid=-1, xmid=key)

    def process_CC(self, attr='smooth', procset=None, method='phaseshift', dc_mode=0, **kwargs):
        """process the dispersion curves"""

        if procset is None:
            procset = self._procset

        starttime = time.time()
        print(f'Applying {attr} to dispersion curves ..... ', end='')

        params = {'sin': -1, 'rep': -1, 'wid': -1, 'procset': "'%s'" % procset,
                  'method': "'%s'" % method, 'dc_mode': dc_mode}

        curves = self._sql.read_curve(params)
        xmids = curves['xmid'].unique()

        for i, xmid in enumerate(xmids):
            params = {'sin': -1, 'rep': -1, 'wid': -1, 'procset': "'%s'" % procset,
                      'method': "'%s'" % method, 'dc_mode': dc_mode, 'xmid': xmid}

            self._process_curve(attr, params, method, procset=procset, **kwargs)
            curve_data = self._sql.read_curve(params)
            dc = DispersionCurve()
            dc.init_data(curve_data['frequency'], curve_data['velocity'], curve_data['error'])
            dc.plot(**kwargs)

        endtime = time.time()
        print(f'{np.round(endtime - starttime, 2)} s')

    def plot_CC(self, procset=None, method='phaseshift', dc_mode=0, **kwargs):
        """plot the dispersion curves"""

        if procset is None:
            procset = self._procset

        params = {'sin': -1, 'rep': -1, 'wid': -1, 'procset': "'%s'" % procset,
                  'method': "'%s'" % method, 'dc_mode': dc_mode}

        curves = self._sql.read_curve(params)
        xmids = curves['xmid'].unique()

        for i, xmid in enumerate(xmids):
            params = {'sin': -1, 'rep': -1, 'wid': -1, 'procset': "'%s'" % procset,
                      'method': "'%s'" % method, 'dc_mode': dc_mode, 'xmid': xmid}
            curve_data = self._sql.read_curve(params)
            dc = DispersionCurve()
            dc.init_data(curve_data['frequency'], curve_data['velocity'], curve_data['error'])
            dc.plot(**kwargs)

    def save_CC(self, procset=None, method='phaseshift', dc_mode=0, format='csv', **kwargs):
        """save the dispersion curves based on receiver spread midpoint"""

        if procset is None:
            procset = self._procset

        params = {'sin': -1, 'rep': -1, 'wid': -1, 'procset': "'%s'" % procset,
                  'method': "'%s'" % method, 'dc_mode': dc_mode}

        curves = self._sql.read_curve(params)
        xmids = curves['xmid'].unique()

        # save the receiver spread midpoints
        path2dc = os.path.join(self.prjdir, f'proc/{procset}/{method}')
        path2geom = os.path.join(path2dc, '1_geom')
        safe_makedirs(path2geom)
        np.savetxt(os.path.join(path2geom, 'xmid.txt'), xmids)

        # save the dispersion curves
        for i, xmid in enumerate(xmids):
            params = {'sin': -1, 'rep': -1, 'wid': -1, 'procset': "'%s'" % procset,
                      'method': "'%s'" % method, 'dc_mode': dc_mode, 'xmid': xmid}
            self._save_curve(path2dc, 'dc%d' % i, params, format=format, **kwargs)


class Tomo2DManager(BaseManager):
    def __init__(self, prjdir, path2raw, path2geom, settings = None, database = 'swa.db'):
        """
        Manager to run the tomographic-like approach from Barone et al. (2019)

        Parameters
        ----------
        prjdir : str, project directory
        path2raw : str, path to the raw seismic data
        path2geom : str, path to the geometry file
        settings : DataFrame, settings for the processing and visualisation
        database : str, name of the database
        """
        super().__init__(prjdir, path2raw, path2geom, settings, database)

    def plot_streams(self, attr='seismogram', procset = None, apply_to = 'all', use_windows=False, **kwargs):
        """Plot the stream data"""

        # Apply process to current selection only
        if apply_to == 'cur':
            if self.current_stream is None:
                self.select_data(inplace = True, verbose=False)

            self.plot(attr,procset=procset, use_windows=use_windows, **kwargs)

        # Apply process to all data sets
        elif apply_to == 'all':
            for sin in self.data.keys():
                for rep in self.data[sin].keys():
                    self.select_data(sin, rep, inplace=True, verbose=False)
                    self.plot(attr, procset=procset, use_windows=use_windows,**kwargs)

    def prepare_streams(self, min_offset, max_offset, min_rec = 6, procset = None):
        """retrieve subsets of the data based on forward and reverse offset shots"""

        if procset is None:
            procset = self._procset
        elif procset != self._procset:
            self.set_procset_label(procset)

        if procset != self._procset:
            self.set_procset_label(procset)

        starttime = time.time()

        for sin in self.data.keys():
            for rep in self.data[sin].keys():

                windows = []
                sys.stdout.write(f'\rTrimming data based on offset (SIN,REP) = ({sin}, {rep}) ..... ')
                sys.stdout.flush()

                current_stream = self.select_data(sin=sin, rep=rep, inplace=False, verbose=False)

                # forward shots
                stream_fw = copy.deepcopy(current_stream)
                oids = stream_fw.trim_by_offset(min_offset, max_offset)

                if len(oids) >= min_rec:
                    windows.append(stream_fw)

                # reverse shots
                stream_rw = copy.deepcopy(current_stream)
                oids = stream_rw.trim_by_offset( -max_offset, -min_offset)

                if len(oids) >= min_rec:
                    windows.append(stream_rw)

                for wid, st in enumerate(windows):
                    self._write_data(st, sin, rep, procset, wid)

        endtime = time.time()
        print(f'{np.round(endtime - starttime, 2)} s')

    def preprocess_streams(self, attr = 'filter', by = 'FK', procset = None, **kwargs):
        """run a preprocessing step on all windows"""

        starttime = time.time()

        for sin in self.data.keys():
            for rep in self.data[sin].keys():

                self.select_data(sin, rep, inplace=True, verbose=False)

                sys.stdout.write(f'\rApplying {attr} by {by} to (SIN,REP) = 'f'({sin}, {rep}) ..... ')
                sys.stdout.flush()

                self.preprocess(attr, procset=procset, use_windows=True, by = by, **kwargs)

        endtime = time.time()
        print(f'{np.round(endtime - starttime, 2)} s')

    def compute_phasediff(self, procset = None):
        """compute phase differences and store in database"""

        if procset is None:
            procset = self._procset
        elif procset != self._procset:
            self.set_procset_label(procset)

        # compute the phase differences
        starttime = time.time()
        for sin in self.data.keys():
            for rep in self.data[sin].keys():

                sys.stdout.write(f'\rCalculating phase differences for (SIN,REP) = '
                                 f'({sin},{rep}) ..... ')
                sys.stdout.flush()

                current_stream = self.select_data(sin=sin, rep=rep, inplace=False, verbose=False)
                wids = self._sql.get_wids(sin, rep, procset)

                recs = self._sql.get_table('recs')
                columns = []
                for i in recs.rin.iloc[:-1]:
                    columns.append('pd%d' % i)
                df = pd.DataFrame(columns=columns)

                for wid in wids:

                    tmp = copy.deepcopy(current_stream)
                    self._set_data(tmp, sin, rep, procset, wid)

                    cur_pd, cur_fids, cur_freq = tmp.compute_phasediffs()
                    cur_rec = tmp.receiver

                    cur_sht_geom, cur_rec_geom = self._sql.get_geometry(sin, rep)
                    rin = np.zeros(len(cur_rec) - 1)
                    for i, rec in enumerate(cur_rec[:-1]):
                        rin[i] = cur_rec_geom['rin'].loc[cur_rec_geom['rx'] == rec].item()
                    pd_hdr = ['pd%d' % i for i in rin]

                    df1 = pd.DataFrame({'procset': procset,
                                        'calc': 'NONE',
                                        'sin': sin,
                                        'rep': rep,
                                        'wid': -1,         # wid is -1 as reverse and forward sections are put together
                                        'fids': cur_fids,
                                        'frequency': cur_freq})
                    df2 = pd.DataFrame(cur_pd, columns=pd_hdr)

                    cur_df = pd.concat([df1, df2], axis=1)
                    df = pd.concat([df, cur_df])

                self._sql.write_pd(df, sin, rep, procset)

        endtime = time.time()
        print(f'{np.round(endtime - starttime, 2)} s')

        # compute mean and std of phase differences for repeated shots
        starttime = time.time()
        fprint = False

        for sin in self.data.keys():
            if len(self.data[sin]) > 1:
                fprint = True
                sys.stdout.write(f'\rCalculating mean and std of phase differences for (SIN) = '
                                 f'({sin}) ..... ')
                sys.stdout.flush()

                self._sql.group_pd(sin, procset, by = 'AVG')
                self._sql.group_pd(sin, procset, by = 'STDEV')

        if fprint:
            endtime = time.time()
            print(f'{np.round(endtime - starttime, 2)} s')

    def run(self, min_offset=3, max_offset=1e6, lam = 1, rel_err = None, procset = None):
        """run the tomographic like approach"""

        if procset is None:
            procset = self._procset
        elif procset != self._procset:
            self.set_procset_label(procset)

        np.set_printoptions(threshold=sys.maxsize)

        starttime = time.time()
        print(f'Running tomographic-like approach ..... ', end='')

        # compute the phase differences if the table does not exist
        if 'pd' not in self._sql.get_tables():
            self.compute_phasediff(procset)

        # obtain the frequencies from the database
        sql = (f"""SELECT DISTINCT frequency
                 FROM pd
                 WHERE procset=='%s'AND sin==%d AND calc=='%s'"""
               % (procset, 1, 'NONE'))
        freq = self._sql.read_sql(sql)['frequency'].values

        # obtain the shot parameters
        _,recs = self._sql.get_geometry(1)
        dx = np.mean(np.diff(recs['rx'].iloc[:-1].values))
        nrec = len(recs)
        nshot = len(self.data)

        # set up the system of equations
        phi_vel_all = np.zeros((nrec - 1, len(freq)))
        for jj, f in enumerate(freq):

            A = np.zeros((2 * nshot * nrec - 1, nrec - 1))  # design matrix
            dphi = np.zeros((2 * nshot * nrec - 1,1))  # phase vector
            error = np.zeros((2 * nshot * nrec - 1,1))  # error vector
            iii = 0

            for sin in self.data.keys():

                _, _, _, sht = self._sql.read_data(sin,1, procset = 'raw')

                # %% process forward shots
                offset = recs['rx'].iloc[:-1].values - sht['sx'].item()  # signed offset vector
                oids = np.argwhere((offset >= min_offset) & (offset <= max_offset))[:, 0]

                columns = ['pd%d'%i for i in range(1,len(offset)+1)]

                if len(self.data[sin]) > 1:
                    pd_mean = self._sql.read_pd(sin, procset, calc = 'AVG', columns=columns)
                    pd_std = self._sql.read_pd(sin, procset, calc = 'STDEV', columns=columns)
                else:
                    pd_mean = self._sql.read_pd(sin, procset, calc = 'NONE', columns=columns)
                    pd_std = pd.DataFrame()

                # fill A, dphi, error
                for ii in oids:
                    if pd_mean.iloc[jj, ii] < 0:
                        iii += 1
                        A[iii, ii] = dx
                        dphi[iii] = pd_mean.iloc[jj, ii]
                        if rel_err is not None:
                            abs_err = rel_err * pd_mean.iloc[jj, ii]
                            error[iii] = abs_err
                        elif not pd_std.empty:
                            error[iii] = pd_std.iloc[jj, ii]**2
                        else:
                            error[iii] = 1

                # %% process reverse shots
                oids = np.argwhere((offset >= -max_offset) & (offset <= -min_offset))[:, 0]

                # fill A, dphi, error
                for ii in oids:
                    if pd_mean.iloc[jj, ii] > 0:
                        iii += 1
                        A[iii, ii] = -dx
                        dphi[iii] = pd_mean.iloc[jj, ii]
                        if rel_err is not None:
                            abs_err = rel_err * pd_mean.iloc[jj, ii]
                            error[iii] = abs_err
                        elif not pd_std.empty:
                            error[iii] = pd_std.iloc[jj, ii]**2
                        else:
                            error[iii] = 1

            # solve equations
            A = A[~np.all(A == 0, axis=1)]
            dphi = dphi[~np.all(dphi == 0, axis=1)].reshape((-1,))
            error = error[~np.all(error == 0, axis=1)].reshape((-1,))

            if rel_err is not None:
                error = np.ones_like(error)*np.var(error)

            weights = 1 / error
            w = np.diag(weights)

            phi_vel, phi_model = tomo2D_phasediff(lam=lam, f=f, A=A, dphi=dphi, w=w)
            phi_vel_all[:, jj] = phi_vel

        # add dispersion curves to database
        xmids = recs['rx'].iloc[:-1].values + dx / 2

        for i in range(len(phi_vel_all)):

            data = {
            'xmid': xmids[i],
            'method': 'tomo2D',
            'dc_mode': 0,
            'f': freq,
            'v': phi_vel_all[i,:],
            'err': np.zeros_like(phi_vel_all[i,:])}

            #params = {'sin': -1, 'rep': -1, 'procset': "'%s'" % procset, 'wid': -1, 'xmid': data['xmid']}
            self._sql.write_curve(data, -1, -1, wid=-1, procset=procset, xmid = data['xmid'])

        endtime = time.time()
        print(f'{np.round(endtime - starttime, 2)} s')


    def process_curves(self, attr='smooth', procset = None, method = 'tomo2D',dc_mode = 0,  **kwargs):
        """process the dispersion curves"""

        if procset is None:
            procset = self._procset

        starttime = time.time()
        print(f'Applying {attr} to dispersion curves ..... ', end = '')

        params = {'sin': -1, 'rep': -1, 'wid': -1, 'procset': "'%s'" % procset,
                  'method': "'%s'" % method, 'dc_mode': dc_mode}

        curves = self._sql.read_curve(params)
        xmids = curves['xmid'].unique()

        for i,xmid in enumerate(xmids):

            params = {'sin': -1, 'rep': -1, 'wid': -1, 'procset': "'%s'" % procset,
                      'method': "'%s'" % method, 'dc_mode': dc_mode, 'xmid': xmid}

            self._process_curve(attr, params, method, procset=procset, **kwargs)
            curve_data = self._sql.read_curve(params)
            dc = DispersionCurve()
            dc.init_data(curve_data['frequency'], curve_data['velocity'], curve_data['error'])
            dc.plot(**kwargs)

        endtime = time.time()
        print(f'{np.round(endtime - starttime, 2)} s')

    def plot_curves(self, procset = None, method = 'tomo2D',dc_mode = 0, **kwargs):
        """plot the dispersion curves"""

        if procset is None:
            procset = self._procset

        params = {'sin': -1, 'rep': -1, 'wid': -1, 'procset': "'%s'" % procset,
                  'method': "'%s'" % method, 'dc_mode': dc_mode}

        curves = self._sql.read_curve(params)
        xmids = curves['xmid'].unique()

        for i,xmid in enumerate(xmids):

            params = {'sin': -1, 'rep': -1, 'wid': -1, 'procset': "'%s'" % procset,
                      'method': "'%s'" % method, 'dc_mode': dc_mode,'xmid': xmid}
            curve_data = self._sql.read_curve(params)
            dc = DispersionCurve()
            dc.init_data(curve_data['frequency'], curve_data['velocity'], curve_data['error'])
            dc.plot(**kwargs)

    def save_curves(self, procset=None, method='tomo2D', dc_mode=0, format = 'csv', **kwargs):
        """save the dispersion curves based on receiver spread midpoint"""

        if procset is None:
            procset = self._procset

        params = {'sin': -1, 'rep': -1, 'wid': -1, 'procset': "'%s'" % procset,
                  'method': "'%s'" % method, 'dc_mode': dc_mode}

        curves = self._sql.read_curve(params)
        xmids = curves['xmid'].unique()

        # save the receiver spread midpoints
        path2dc = os.path.join(self.prjdir, f'proc/{procset}/{method}')
        path2geom = os.path.join(path2dc, '1_geom')
        safe_makedirs(path2geom)
        np.savetxt(os.path.join(path2geom,'xmid.txt'), xmids)

        # save the dispersion curves
        for i,xmid in enumerate(xmids):

            params = {'sin': -1, 'rep': -1, 'wid': -1, 'procset': "'%s'" % procset,
                      'method': "'%s'" % method, 'dc_mode': dc_mode,'xmid': xmid}
            self._save_curve(path2dc, 'dc%d' % i, params, format=format, **kwargs)
