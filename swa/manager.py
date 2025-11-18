
import sys
import time
import copy

import matplotlib.pyplot as plt

from .utils import *
from .stream import SeismicStream
from .curve import DispersionCurve
from .curves import CombineCurves
from .qtapps import *

# TODOs
# TODO: optimization
# TODO: do not save raw to db or instead of reading files read from db
# TODO: test on field data
# TODO: basic sanity checks
# TODO: error handling!!! : e.g., when requesting data from database always check whether its empty or not!
# --> change warnings to logging!
# TODO: documentation!!!
# TODO: change settings midprocessing
# TODO: check what is happening with roll-along data
# TODO: stacking technique SWIP??
# TODO: avoid unnessesary dicts

class BaseManager:
    def __init__(self, prjdir, path2raw=None, path2geom=None, settings=None, database='swa.db',**kwargs):
        """
        Base manager class for surface wave analysis

        Parameters
        ----------
        prjdir : str, project directory
        path2raw : str, optional, path to the raw seismic data
        path2geom : str, optional, path to the geometry file
        settings : DataFrame, settings for the processing and visualisation
        database : str, name of the database
        """

        self.logger = create_logging(name='Manager')
        self.app = QApplication(sys.argv)

        self.prjdir = prjdir
        self.path2raw = path2raw
        self.path2geom = path2geom

        self.settings = settings

        self.database = database

        self._init_params()

        self.path2db = os.path.join(self.prjdir, self.database)

        # create/load project
        if os.path.isfile(self.path2db):
            self._load_project(**kwargs)
        else:
            self._create_project(**kwargs)

    def _create_project(self,**kwargs):
        """Create the project directory and database"""

        print('Creating project:')
        # set up project directory
        create_projectdir(self.prjdir)

        # check if data exists in project directory
        if (len(os.listdir(os.path.join(self.prjdir,'01_data/raw'))) == 0):
            if (self.path2raw is not None):

                rename = kwargs.pop('rename', False)
                print('Copying and renaming raw data into project directory ..... ' , end="")
                starttime = time.time()
                _, self.ext = get_fileList(self.path2raw)
                rename_files(self.path2raw, extension=self.ext, prjdir=self.prjdir,rename = rename)
                endtime = time.time()
                print(f'{np.round(endtime - starttime, 2)} s')

            else:
                raise FileNotFoundError('Raw data not found.')

        self.path2raw = os.path.join(self.prjdir, '01_data/raw')
        self.fileList, self.ext = get_fileList(self.path2raw)

        # check if geometry exists in project directory
        geometry_path = os.path.join(self.prjdir, '02_geom', 'geometry.csv')

        # Check if geometry.csv exists in project directory
        if not os.path.isfile(geometry_path):
            if self.path2geom is not None and os.path.isfile(self.path2geom):
                print('Copying geometry into project directory ..... ', end="")
                starttime = time.time()
                shutil.copy(self.path2geom, geometry_path)
                endtime = time.time()
                print(f'{np.round(endtime - starttime, 2)} s')
            else:
                print('geometry.csv file not provided or found. Trying to create from data ..... ', end="")
                starttime = time.time()
                try:
                    create_geometry(self.fileList, geometry_path)
                    endtime = time.time()
                    print(f'{np.round(endtime - starttime, 2)} s')

                except Exception:

                    endtime = time.time()
                    print(f'{np.round(endtime - starttime, 2)} s')

                    #self.logger.info('No geometry file found or created.')

                    print('No geometry.csv file found or created. '
                          'Creating figures for data preview mode ..... ', end="")
                    starttime = time.time()
                    figures = self.get_figures()
                    endtime = time.time()
                    print(f'{np.round(endtime - starttime, 2)} s')

                    # data preview
                    self.data_preview(figures)

                    # raise FileNotFoundError(
                    #     'Geometry file not found and data does not contain source/receiver information.')

        self.path2geom = os.path.join(self.prjdir, '02_geom/geometry.csv')

        self._sql = SQL(database=self.path2db)

        # survey geometry
        self._sql.read_geometry(self.path2geom)

        # processing settings
        if self.settings is None:
            self.settings = create_settings()
        self._sql.read_setting(self.settings)

        # seismic data
        self.create = True
        self._read_data()

        print('\nExisting procsets:', *self._sql.get_proc_labels())

        # set procset
        self.set_new_procset(procset='proc1')
        #self._sql.show_tables()

        print('')

    def _load_project(self,**kwargs):
        """Load the project"""

        self.path2raw = os.path.join(self.prjdir, '01_data/raw')
        self.fileList, self.ext = get_fileList(self.path2raw)
        self.path2geom = os.path.join(self.prjdir, '02_geom/geometry.csv')

        print('Loading project:')
        self._sql = SQL(database=self.path2db)

        # load settings
        self.settings = self._sql.get_table('settings')

        self.create = False
        self._read_data()

        for table in self._sql.get_tables():
            self._sql.delete_data(table, {'procset': "'%s'" % 'tmp'})

        # set/load procset label
        prc_sets = self._sql.get_proc_labels()

        if len(prc_sets) > 1:
            self.set_new_procset(procset=prc_sets[-1])
        else:
            self.set_new_procset(procset='proc1')

        print('\nExisting procsets:', *prc_sets)

        if kwargs.pop('load', True):
            # load processed data
            if len(prc_sets) > 1:
                self.load_procset(prc_sets[-1])

        print('')

    def _init_params(self):
        """initialize some parameters"""

        # dictionary storing stream stream data
        self.data = {}

        # procset label
        self._procset = 'proc1' # procset to store new process
        self._loadset = 'proc1' # procset to load process from

        # current stream
        self.current_stream = None
        self.selected_ids = (1, 1)

    def set_new_procset(self, procset = None, verbose = True):
        """set the new active processing name"""
        if (procset != 'raw') & (isinstance(procset,str)):
            self._procset = procset
            if verbose:
                print('Active procset label: %s' % procset)
        else:
            self._procset = 'proc1'
            if verbose:
                self.logger.warning('Active procset label should be different from "raw". '
                                    'Setting to default label "proc1".')

    def set_procset_label(self, procset = None, verbose = True):
        """set the new active processing name"""
        self.set_new_procset(procset , verbose)

    def set_loadset(self, procset = None):
        """set the loadset label, i.e. which dataset to load"""
        if isinstance(procset,str):
            self._loadset = procset
        else:
            self._loadset = 'proc1'

    def load_procset(self, procset = None, **kwargs):
        """load processed data from database"""

        if not isinstance(procset, str):
            self.logger.warning('Procset label needs to be a string.')

        elif not procset in self._sql.get_proc_labels():
            self.logger.warning(f'Procset {procset} does not exist.')

        else:
            self._loadset = procset

            print('Loading amplitude data from "%s" ..... ' % self._loadset, end="")
            starttime = time.time()

            # data = self.data
            shots = self._sql.get_table('shots')

            for i in range(len(shots)):

                sin = shots.loc[i, 'sin']
                rep = shots.loc[i, 'rep']

                data = self.data
                if sin in data.keys():
                    if rep in data[sin].keys():
                        self._set_data(self.data[sin][rep], sin, rep, procset=self._loadset)
                        self._set_FV(self.data[sin][rep], sin, rep, procset=self._loadset, **kwargs)

            endtime = time.time()
            print(f'{np.round(endtime - starttime, 2)} s')

    def _get_filepath(self, sin, rep=1):
        """Return the file path corresponding to the indices sin and rep as string"""
        if self.fileList is not None:
            sn = self._sql.get_shotfile(sin, rep).shots.item()

            for i, fp in enumerate(self.fileList):
                path, fn = os.path.split(fp)
                sfn = re.findall(r'\d+', fn.replace(self.ext, ''))[0]

                if int(sn) == int(sfn):
                    return os.path.join(path,fn)

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
                        if self.create:
                            self._write_data(self.data[sin][rep], sin, rep, 'proc1')
            else:
                #pass
                self.logger.error(f'Shot file {fn} not found.')

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
        # else:
        #     self.logger.error(f'No data for ({sin},{rep})')

    def _set_FV(self, data, sin, rep, procset, wid=-1, method='phaseshift'):
        """set FV data from database to current stream"""
        vel, kw, freq, FV = self._get_FV(sin, rep, procset=procset, wid=wid, method=method)
        if FV is not None:
            data.update_FV(method, vel, kw, freq, FV)
            return True
        else:
            return False

    # %% Processing
    def select_data(self, sin=1, rep=1, inplace=True, verbose = True):
        """
        Select one stream object based on source location and shot repetition indices

        Parameters
        ----------
        sin : int, shot index number
        rep : int, repeated shot index number
        inplace : bool, default True, whether to modify the stream object rather than creating a new one
        verbose : print current selection to console

        Returns
        -------
        stream object

        """

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

    def _preprocess(self, type, procset=None, use_windows = False, **kwargs):
        """apply preprocessing steps to current selection or all data sets"""

        if procset is None:
            procset = self._procset

        sin, rep = self.selected_ids
        stream = self.current_stream

        wids = self._sql.get_wids(sin, rep, self._loadset)
        if use_windows:
            for wid in wids or []:
                tmp = copy.deepcopy(stream)
                self._set_data(tmp, sin, rep, self._loadset, wid)
                func = getattr(tmp, type)
                func(**kwargs)
                self._write_data(tmp, sin,rep, procset, wid)
        else:
            func = getattr(stream, type)
            func(**kwargs)
            self.data[sin][rep] = stream
            self._write_data(stream, sin, rep, procset, wid = -1)

    def preprocess(self, type, procset=None, use_windows = False, **kwargs):
        """
        apply preprocessing steps to current selection or all data sets

        Parameters
        ----------
        type : str, which processing method to call
        procset : str, identifier to set on which dataset the processing should be applied to
        use_windows : bool, default False, whether to apply the processing to windows
        kwargs : arguments for the processing

        """
        self._preprocess(type, procset, use_windows, **kwargs)

    def read_filter(self, ftype, procset=None, use_windows=False):
        """Read manual filter from database."""

        procset = procset or self._procset

        if ftype not in ("FK", "TX"):
            self.logger.error("Filter type not implemented.")
            return None, None

        sin, rep = self.selected_ids

        params_template = {
            "procset": f"'{procset}'",
            "sin": sin,
            "rep": rep,
            "type": f"'{ftype}'",
        }

        wids = self._sql.get_wids(sin, rep, procset)

        points_top = []
        points_bot = []

        if use_windows:
            for wid in wids or []:
                params = {**params_template, "wid": wid}
                df = self._sql.read_filter(params)
                pt, pb = filter_df2dict(df)
                points_top.append(pt)
                points_bot.append(pb)
        else:
            params = {**params_template, "wid": -1}
            df = self._sql.read_filter(params)

            print(df)

            points_top, points_bot = filter_df2dict(df)

        return points_top, points_bot

    def apply_filter(self,ftype, points_top = None, points_bot = None,procset=None, use_windows=False, **kwargs):
        """Apply manual filter from database."""

        procset = procset or self._procset

        if ftype not in ("FK", "TX"):
            self.logger.error("Filter type not implemented.")
            return None, None

        # if points_top is None or points_bot is None:
        #     points_top, points_bot = self.read_filter(ftype, procset,use_windows)

        sin, rep = self.selected_ids
        stream = self.current_stream

        wids = self._sql.get_wids(sin, rep, self._loadset) or []

        if use_windows:
            for i, wid in enumerate(wids):
                tmp_stream = copy.deepcopy(stream)
                self._set_data(tmp_stream, sin, rep, self._loadset, wid)

                if ftype == "FK":
                    # Validate list lengths
                    try:
                        pt = points_top[i]
                        pb = points_bot[i]
                    except IndexError:
                        self.logger.error(
                            f"Mismatch between number of windows ({len(wids)}) "
                            f"and provided filter point sets."
                        )
                        continue

                    for pts, key in zip([pt, pb], ["t", "b"]):
                        tmp_stream.apply_fk_filter(pts, key, **kwargs)
                else:
                    raise NotImplementedError

                self._write_data(tmp_stream, sin, rep, procset, wid)

        else:
            if ftype == "FK":
                for pts, key in zip([points_top, points_bot], ["t", "b"]):
                    stream.apply_fk_filter(pts, key, **kwargs)
            else:
                raise NotImplementedError

            self.data[sin][rep] = stream
            self._write_data(stream, sin, rep, procset, wid=-1)

    def _transform(self, method='phaseshift', procset=None, use_windows = False, **kwargs):
        """apply wavefield transformation to current selection or all data sets"""

        if procset is None:
            procset = self._procset

        sin, rep = self.selected_ids
        stream = self.current_stream

        wids = self._sql.get_wids(sin, rep, self._loadset)

        if use_windows:
            for wid in wids or []:
                tmp = copy.deepcopy(stream)
                self._set_data(tmp, sin, rep, self._loadset, wid)
                tmp.transform(method=method, **kwargs)
                self._write_FV(tmp,  sin, rep, procset, wid)
        else:
            stream.transform(method=method, **kwargs)
            self.data[sin][rep] = stream
            self._write_FV(stream, sin, rep, procset, wid = -1)

    def transform(self, method='phaseshift', procset=None, use_windows=False, **kwargs):
        """
        apply wavefield transformation to current selection or all data sets

        Parameters
        ----------
        method : str, default 'phaseshift', which transformation method to apply to the data
        procset : str, identifier to set on which dataset the processing should be applied to
        use_windows : bool, default False, whether to apply the processing to windows
        kwargs : arguments for the processing

        """
        self._transform(method, procset, use_windows, **kwargs)

    def _extract_dc(self, stream, sin, rep, procset, wid, method, **kwargs):
        """extract a dispersion curve and write to database"""

        pck_mode = 'auto'

        try:
            if method == 'MOPA':
                auto_method = method
            else:
                auto_method = 'max'
            stream.dcpicking(pck_mode=pck_mode, auto_method = auto_method, **kwargs)
        except:
            warnings.warn('No dispersion image generated prior to dispersion curve extraction'
                          'Dispersion curve extraction not possible.')
            pass

        #method = stream.trafo_type
        xmid = stream.midpoint

        for pck_mode in stream.picks.keys():
            for dc_mode in stream.picks[pck_mode].keys():
                dc = {
                    'xmid': xmid,
                    'method': stream.extraction_method,
                    'dc_mode': dc_mode,
                    'f': stream.picks[pck_mode][dc_mode]['f'],
                    'v': stream.picks[pck_mode][dc_mode]['v'],
                    'err': np.zeros(len(stream.picks[pck_mode][dc_mode]['v']))}

                self._sql.write_curve(dc, sin, rep, procset, wid, xmid)

    def _extract(self, procset=None, use_windows = False, method = None, **kwargs):
        """apply dispersion curve picking to a stream"""

        if procset is None:
            procset = self._procset

        sin, rep = self.selected_ids
        stream = self.current_stream

        wids = self._sql.get_wids(sin, rep, procset)
        if use_windows:
            for wid in wids or []:
                tmp = copy.deepcopy(stream)
                self._set_data(tmp, sin, rep, procset, wid)
                self._set_FV(tmp, sin, rep, self._procset, wid, method=method)
                self._extract_dc(tmp, sin = sin, rep = rep, wid = wid, procset=procset,
                              method = method, **kwargs)
        else:
            stream = copy.deepcopy(stream)
            self._set_data(stream, sin, rep, procset)
            self._set_FV(stream, sin, rep, procset=procset, method=method)
            self._extract_dc(stream,  sin=sin, rep=rep, wid=-1, procset=procset,
                          method = method, **kwargs)

    def extract(self, procset=None, use_windows=False, method='max', **kwargs):
        """
        apply dispersion curve extraction to a stream

        Parameters
        ----------
        procset : str, identifier to set on which dataset the processing should be applied to
        use_windows : bool, default False, whether to apply the processing to windows
        method : str, default 'max', extraction method
        kwargs : arguments for the extraction

        """
        self._extract(procset, use_windows, method, **kwargs)

    def _process_curve(self, type, params, method = None,
                       procset = None, **kwargs):
        """apply a process to the dispersion curve data"""

        if procset is None:
            procset = self._procset

        curve_data = self._sql.read_curve(params)

        if curve_data.empty:
            return

        # Initialize and process the dispersion curve
        dc_obj = DispersionCurve()
        dc_obj.init_data(curve_data['frequency'], curve_data['velocity'], curve_data['error'])
        func = getattr(dc_obj, type)
        dc_obj = func(**kwargs)  # processed DispersionCurve

        # Get unique xmid values
        xmids = curve_data['xmid'].unique()

        for xmid in xmids:
            dc_record = {
                'xmid': xmid,
                'method': method,
                'dc_mode': params['dc_mode'],
                'f': dc_obj.frequency,
                'v': dc_obj.velocity,
                'err': dc_obj.error
            }

            self._sql.write_curve(
                dc_record,
                params['sin'],
                params['rep'],
                procset,
                params['wid'],
                xmid
            )

    def _get_stream_kwargs(self, stream):
        """return some stream properties"""

        receiver = stream.receiver
        source = stream.source
        offsets = receiver - source
        stream_kwargs = {
            'offsets': offsets,
            'nchannels': len(receiver),
            'dx': abs(receiver[0] - receiver[1])
        }
        return stream_kwargs

    def process_curve(self, type, procset=None, method = None,
                      dc_mode=0, use_windows = False, **kwargs):
        """
        apply a process to a dispersion curve

        Parameters
        ----------
        type : str, which processing method to call
        procset : str, identifier to set on which dataset the processing should be applied to
        method : str, method used to obtain dispersion curve
        dc_mode : int, default 0, mode of propagation
        use_windows : bool, default False, whether to apply the processing to windows
        kwargs : arguments for the processing

        """

        if procset is None:
            procset = self._procset

        sin, rep = self.selected_ids
        stream = self.data[sin][rep]

        # Common params template
        params_template = {
            'procset': f"'{self._loadset}'",
            'method': f"'{method}'",
            'dc_mode': dc_mode,
            'sin': sin,
            'rep': rep
        }

        if use_windows:
            wids = self._sql.get_wids(sin, rep, self._loadset)
            for wid in wids or []:
                params = params_template.copy()
                params['wid'] = wid

                tmp_stream = copy.deepcopy(stream)
                self._set_data(tmp_stream, sin, rep, self._loadset, wid)

                if type == 'estimate_error':
                    stream_kwargs = self._get_stream_kwargs(tmp_stream)
                    kwargs.update(stream_kwargs)

                self._process_curve(type, params, method=method, procset=procset, **kwargs)
        else:
            params = params_template.copy()
            params['wid'] = -1

            if type == 'estimate_error':
                stream_kwargs = self._get_stream_kwargs(stream)
                kwargs.update(stream_kwargs)

            self._process_curve(type, params, method=method, procset=procset, **kwargs)

    def _save_dc(self, path2dc, name, params, format = 'csv', **kwargs):
        """save a dispersion curve"""

        curve_data = self._sql.read_curve(params)

        if curve_data.empty:
            return None

        dc = DispersionCurve()
        dc.init_data(curve_data['frequency'], curve_data['velocity'], curve_data['error'])
        dc.save(path2dc, name, format=format, **kwargs)

        return curve_data['xmid'].unique()[0]

    def _save(self, procset=None, method = None,
                   dc_mode=0, use_windows = False, **kwargs):

        """save a dispersion curve for a defined source location, repetition and window id"""

        if procset is None:
            procset = self._procset

        sin, rep = self.selected_ids

        # Directory to save processed curves
        dir_path = os.path.join(self.prjdir, f'03_proc/{procset}_{method}/Mode{int(dc_mode)}')
        safe_makedirs(dir_path)

        # Base params template
        params_template = {
            'procset': f"'{procset}'",
            'method': f"'{method}'",
            'dc_mode': dc_mode,
            'sin': sin,
            'rep': rep
        }

        # Determine wids to iterate
        wids = self._sql.get_wids(sin, rep, procset) if use_windows else [-1]

        xmids = [
            self._save_dc(
                dir_path,
                f"dc_sin{sin}-rep{rep}-wid{wid}" if wid != -1 else f"dc_sin{sin}-rep{rep}",
                {**params_template, 'wid': wid},
                **kwargs
            )
            for wid in wids
        ]

        # Filter out None values
        xmids = [xmid for xmid in xmids if xmid is not None]

        return xmids

    def save(self, procset=None, method = None,dc_mode=0, use_windows = False, **kwargs):
        """
        save a dispersion curve for a defined source location, repetition and window id

        Parameters
        ----------
        procset : str, identifier to set on which dataset the processing should be applied to
        method : str, method used to obtain dispersion curve
        dc_mode : int, default 0, mode of propagation
        use_windows : bool, default False, whether to apply the processing to windows

        """

        self._save(procset, method,dc_mode, use_windows, **kwargs)

    def _plot(self, type='seismogram', procset = None, use_windows = False, **kwargs):
        """plot portions of the stream data"""

        if procset is None:
            procset = self._procset

        sin, rep = self.selected_ids
        stream = self.current_stream
        stream = copy.deepcopy(stream)

        method = kwargs.pop('method', 'phaseshift')
        if type in ['dispersionImage', 'dispersionImageComposite']:
            self._set_FV(stream, sin, rep, procset=procset, method=method)

        wids = self._sql.get_wids(sin, rep, procset)
        window_axes = []

        if use_windows:
            for wid in wids or []:
                tmp = copy.deepcopy(stream)
                self._set_data(tmp, sin, rep, procset, wid)

                if type in ['dispersionImage','dispersionImageComposite']:
                    self._set_FV(tmp, sin, rep, procset=procset, method=method, wid=wid)

                fig = tmp.plot(type, **kwargs)
                window_axes.append(fig)
            return window_axes, wids
        else:
            self._set_data(stream, sin, rep, procset, -1)
            ax = stream.plot(type, show=True, **kwargs)
            return ax

    def plot_curve(self, procset=None, method='phaseshift',
                   use_windows = False, **kwargs):
        """
        plot a dispersion curve

        Parameters
        ----------
        procset : str, identifier to set on which dataset the processing should be applied to
        method : str, method used to obtain dispersion curve
        use_windows : bool, default False, whether to apply the processing to windows

        """

        if procset is None:
            procset = self._procset

        sin,rep = self.selected_ids

        params_template = {'procset': "'%s'" % procset,
                  'method': "'%s'" % method,
                  'sin': sin,
                  'rep': rep}

        cmap = getattr(plt.cm, 'Greys')
        color_map = cmap(np.linspace(0, 1, 10))

        wids = self._sql.get_wids(sin, rep, procset) if use_windows else [-1]

        for wid in wids:
            params = params_template.copy()
            params['wid'] = wid

            curve_data = self._sql.read_curve(params)
            if curve_data.empty:
                continue

            # handle dc_mode as array; ensure colors array indexing works
            dc_modes = curve_data['dc_mode'].astype(int)
            colors = color_map[dc_modes % len(color_map)]

            dc = DispersionCurve()
            dc.init_data(curve_data['frequency'], curve_data['velocity'], curve_data['error'])
            dc.plot(color=colors, edgecolor='k', **kwargs)

    def plot_pseudosection(self, procset=None, **kwargs):
        """
        plot the Rayleigh wave phase velocity pseudosection

        Parameters
        ----------
        procset : str, identifier to set on which dataset the processing should be applied to

        """

        if procset is None:
            procset = self._procset

        # Default kwargs
        method = kwargs.pop('method', 'phaseshift')
        dc_mode = kwargs.pop('dc_mode', 0)
        cmap = kwargs.pop('cmap', 'viridis')
        show = kwargs.pop('show', True)
        axes = kwargs.pop('axes', None)
        vmin = kwargs.pop('vmin', 200)
        vmax = kwargs.pop('vmax', 500)
        title = kwargs.pop('title', '')
        outfile = kwargs.pop('outfile', None)

        _, recs_all = self._sql.get_geometry(sin='*')
        params = {'procset': f"'{procset}'", 'method': f"'{method}'", 'dc_mode': f"{dc_mode}"}
        curves = self._sql.read_curve(params)

        if curves.empty:
            self.logger.warning('No dispersion curves in database. Pseudosection not visualized.')
            return None

        fmin = kwargs.pop('fmin', curves['frequency'].min())
        fmax = kwargs.pop('fmax', curves['frequency'].max())

        if axes is None:
            fig, ax = plt.subplots()
        else:
            ax = axes
            fig = ax.figure

        # Use groupby to avoid repeated filtering
        for xmid, sub in curves.groupby('xmid'):
            dc = DispersionCurve()
            dc.init_data(sub['frequency'], sub['velocity'], sub['error'])
            dc.plotColumn(
                axes=ax,
                xmid=xmid,
                vmin=vmin,
                vmax=vmax,
                cmap=cmap,
                y_value='f',
                **kwargs
            )

        plot_colorBar(ax, vmin, vmax, cmap=cmap, orientation='vertical')
        ax.set_xlim([recs_all['rx'].min(), recs_all['rx'].max()])
        ax.set_ylim([fmin, fmax])
        ax.set_title(title)

        if outfile:
            fig.savefig(outfile)

        if show:
            plt.tight_layout()
            plt.show()

        return ax


    def plot(self, type='seismogram', procset = None, use_windows = False, **kwargs):
        """
        plot portions of the stream data

        Parameters
        ----------
        type : str, plot type
        procset : str, identifier to set on which dataset the processing should be applied to
        use_windows : bool, default False, whether to apply the processing to windows

        """

        if procset is None:
            procset = self._procset

        if type == 'pseudosection':
            ax = self.plot_pseudosection(procset, **kwargs)
            return ax
        elif type == 'curve':
            self.plot_curve(procset, **kwargs)
        else:
            self._plot(type,procset,use_windows,**kwargs)

    def get_figures(self, type = ''):
        """return plot for each data set"""

        figures = []

        fileList = natural_sort(self.fileList)
        for i, fn in enumerate(fileList):
            st = SeismicStream(fn, settings=self.settings)
            fig = st.plot(type,show=False)
            figures.append(fig)

        return figures

    def data_preview(self, figures):
        """data preview modus"""

        window = FigureSwitcher(figures)
        window.resize(800, 600)
        window.show()
        sys.exit(self.app.exec())

    def _get_windows(self,procset):

        labels = []

        for sin in self.data.keys():
            for rep in self.data[sin].keys():
                wids = self._sql.get_wids(sin, rep, procset)
                labels.append([[sin, rep, x] for x in wids])

        return labels

    # TODO save point list or something?
    def gui_interact(self, type='', procset = None, use_windows = False,**kwargs):
        """
        interactive figure switcher

        Parameters
        ----------
        type : str, plot type
        procset : str, identifier to set on which dataset the processing should be applied to
        use_windows : bool, default False, whether to apply the processing to windows

        """

        if procset is None:
            procset = self._procset

        window_title = 'SWA - Interactive Figure Viewer'

        if type in ['', 'seismogram', 'TX']:
            DataSwitcher = DataSwitcherFilterSeis
        elif type in ['dispersionImage', 'FV']:
            DataSwitcher = DataSwitcherPick
        elif type == 'FK':
            DataSwitcher = DataSwitcherFilterFK
        else:
            self.logger.error(f'Interactive figure switcher does not exist for plot type "{type}"')
            return

        print('Loading the GUI ..... ', end="")
        starttime = time.time()

        if use_windows:
            window = DualDataSwitcher(self.data, self.path2db, plot=type,
                                        DataSwitcher=DataSwitcher,
                                        procset=procset,
                                        procsets=self._sql.get_proc_labels(),
                                        window_title=window_title,select_plot = False, **kwargs)

        else:
            window = DataSwitcher(self.data, self.path2db, plot=type,
                                    procset = procset,
                                    procsets = self._sql.get_proc_labels(),
                                    window_title=window_title,select_plot = False,**kwargs)

        window.resize(800, 600)
        endtime = time.time()
        print(f'{np.round(endtime - starttime, 2)} s')
        window.show()

        def handle_about_to_quit():
            window.clean()

        self.app.aboutToQuit.connect(handle_about_to_quit)
        self.app.exec()

        plt.close('all')

    def gui_view(self, type='', procset = None, use_windows = False,**kwargs):
        """
        figure switcher

        Parameters
        ----------
        type : str, plot type
        procset : str, identifier to set on which dataset the processing should be applied to
        use_windows : bool, default False, whether to apply the processing to windows

        """

        if type not in ['seismogram','','TX','spectrogram','FX','spectra',
                        'FK','SFR','dispersionImage','FV', 'curve', 'DC']:
            self.logger.error(f'AttributeError: {type} does not exist.')

        if type == '' or type == 'seismogram':
            type = 'TX'

        if type == 'spectrogram':
            type = 'FX'

        if type == 'dispersionImage':
            type = 'FV'

        if type == 'curve':
            type = 'DC'

        window_title = 'SWA - Figure Viewer'
        DataSwitcher = DataSwitcherBase

        print('Loading the GUI ..... ', end="")
        starttime = time.time()

        if use_windows:
            window = DualDataSwitcher(self.data, self.path2db, plot=type, DataSwitcher=DataSwitcher,
                                        procset=procset,
                                        procsets=self._sql.get_proc_labels(),
                                        window_title=window_title,**kwargs)

        else:
            window = DataSwitcher(self.data, self.path2db, plot=type,
                                    procset = procset,
                                    procsets = self._sql.get_proc_labels(),
                                    window_title=window_title,**kwargs)

        window.resize(800, 600)
        endtime = time.time()
        print(f'{np.round(endtime - starttime, 2)} s')
        window.show()

        def handle_about_to_quit():
            window.clean()

        self.app.aboutToQuit.connect(handle_about_to_quit)
        self.app.exec()

        plt.close('all')


class MASW2DManager(BaseManager):
    def __init__(self, prjdir, path2raw=None, path2geom=None, settings = None, database = 'swa.db',**kwargs):
        """
        MASW 2D manager class for surface wave analysis

        Parameters
        ----------
        prjdir : str, project directory
        path2raw : str, optional, path to the raw seismic data
        path2geom : str, optional, path to the geometry file
        settings : DataFrame, settings for the processing and visualisation
        database : str, name of the database
        """

        super().__init__(prjdir, path2raw, path2geom, settings, database,**kwargs)
        self.CC = None

    def plot_streams(self, type='seismogram', procset = None, apply_to = 'all', use_windows=False, **kwargs):
        """
        Plot the stream data

        Parameters
        ----------
        type : str, plot type
        procset : str, identifier to set on which dataset the processing should be applied to
        apply_to : str, default 'all', whether to apply function to all streams or just the current selection
        use_windows : bool, default False, whether to apply the processing to windows
        """

        if procset is None:
            procset = self._procset

        # Apply process to current selection only
        if apply_to == 'cur':
            if self.current_stream is None:
                self.select_data(inplace = True, verbose=False)

            self._plot(type,procset=procset, use_windows=use_windows, **kwargs)

        # Apply process to all data sets
        elif apply_to == 'all':
            for sin in self.data.keys():
                for rep in self.data[sin].keys():
                    self.select_data(sin, rep, inplace=True, verbose=False)
                    self._plot(type, procset=procset, use_windows=use_windows,**kwargs)

    def plot(self, type='seismogram', procset = None, apply_to = 'all', use_windows=False, **kwargs):
        """
        Plot the stream data

        Parameters
        ----------
        type : str, plot type
        procset : str, identifier to set on which dataset the processing should be applied to
        apply_to : str, default 'all', whether to apply function to all streams or just the current selection
        use_windows : bool, default False, whether to apply the processing to windows
        """

        if procset is None:
            procset = self._procset

        if type == 'pseudosection':
            ax = self.plot_pseudosection(procset, **kwargs)
            return ax

        else:
            self.plot_streams(type,procset,apply_to,use_windows,**kwargs)

    def preprocess_streams(self, type='trim', procset = None, apply_to = 'all', use_windows=False, **kwargs):
        """
        Apply preprocessing steps to current selection or all data sets

        Parameters
        ----------
        type : str, processing type
        procset : str, identifier to set on which dataset the processing should be applied to
        apply_to : str, default 'all', whether to apply function to all streams or just the current selection
        use_windows : bool, default False, whether to apply the processing to windows
        """

        # # check if process exists
        # if type not in ['filter', 'trim']:
        #     raise AttributeError(f'Attribute can be "filter" or "trim" not {type}.')

        if procset is None:
            procset = self._procset

        if procset != self._procset:
            self.set_new_procset(procset)

        # Apply process to current selection only
        if apply_to == 'cur':
            if self.current_stream is None:
                self.select_data(inplace = True, verbose=False)

            starttime = time.time()
            print(f'Applying {type} to (SIN,REP) = ({self.selected_ids[0]}, {self.selected_ids[1]}) ..... ', end='')

            self._preprocess(type,procset=procset, use_windows=use_windows, **kwargs)

            endtime = time.time()
            print(f'{np.round(endtime - starttime, 2)} s')

        # Apply process to all data sets
        elif apply_to == 'all':
            starttime = time.time()

            for sin in self.data.keys():
                for rep in self.data[sin].keys():

                    self.select_data(sin, rep, inplace=True, verbose=False)

                    sys.stdout.write(f'\rApplying {type} to (SIN,REP) = ({sin}, {rep}) ..... ')
                    sys.stdout.flush()

                    self._preprocess(type,procset=procset, use_windows=use_windows, **kwargs)

            endtime = time.time()
            print(f'{np.round(endtime - starttime, 2)} s')

        self.set_loadset(procset)

    def preprocess(self, type='trim', procset = None, apply_to = 'all', use_windows=False, **kwargs):
        """
        Apply preprocessing steps to current selection or all data sets

        Parameters
        ----------
        type : str, processing type
        procset : str, identifier to set on which dataset the processing should be applied to
        apply_to : str, default 'all', whether to apply function to all streams or just the current selection
        use_windows : bool, default False, whether to apply the processing to windows
        """

        self.preprocess_streams(type, procset, apply_to, use_windows, **kwargs)

    def transform_streams(self, method='phaseshift', procset = None, apply_to = 'all', use_windows=False, **kwargs):
        """
        Apply wavefield transformation to current selection or all data sets

        Parameters
        ----------
        method : str, transformation method
        procset : str, identifier to set on which dataset the processing should be applied to
        apply_to : str, default 'all', whether to apply function to all streams or just the current selection
        use_windows : bool, default False, whether to apply the processing to windows
        """

        if procset is None:
            procset = self._procset

        if procset != self._procset:
            self.set_new_procset(procset)

        # Apply process to current selection only
        if apply_to == 'cur':
            if self.current_stream is None:
                self.select_data(inplace = True, verbose=False)

            starttime = time.time()
            print(f'Applying {method} transformation to (SIN,REP) = ({self.selected_ids[0]}, {self.selected_ids[1]})'
                  f' ..... ', end = '')
            self._transform(method,procset=procset, use_windows=use_windows, **kwargs)

            endtime = time.time()
            print(f'{np.round(endtime - starttime, 2)} s')

        # Apply process to all data sets
        elif apply_to == 'all':
            starttime = time.time()

            for sin in self.data.keys():
                for rep in self.data[sin].keys():

                    self.select_data(sin, rep, inplace=True, verbose=False)

                    sys.stdout.write(f'\rApplying {method} transformation to (SIN,REP) = ({sin}, {rep}) ..... ')
                    sys.stdout.flush()

                    self._transform(method, procset=procset, use_windows=use_windows,**kwargs)

            endtime = time.time()
            print(f'{np.round(endtime - starttime, 2)} s')

        self.set_loadset(procset)

    def transform(self, method='phaseshift', procset = None, apply_to = 'all', use_windows=False, **kwargs):
        """
        Apply wavefield transformation to current selection or all data sets

        Parameters
        ----------
        type : str, transformation method
        procset : str, identifier to set on which dataset the processing should be applied to
        apply_to : str, default 'all', whether to apply function to all streams or just the current selection
        use_windows : bool, default False, whether to apply the processing to windows
        """

        self.transform_streams(method, procset, apply_to, use_windows, **kwargs)

    def extract_curves(self, procset = None, method = 'max',
                       apply_to = 'all', use_windows=False, **kwargs):
        """
        Extract dispersion curves

        Parameters
        ----------
        procset : str, identifier to set on which dataset the processing should be applied to
        method : str, default 'max', method for dispersion curve extraction
        apply_to : str, default 'all', whether to apply function to all streams or just the current selection
        use_windows : bool, default False, whether to apply the processing to windows
        """

        # Apply process to current selection only
        if apply_to == 'cur':
            if self.current_stream is None:
                self.select_data(inplace = True, verbose=False)

            starttime = time.time()
            print(f'Dispersion curve extraction of (SIN,REP) = ({self.selected_ids[0]}, {self.selected_ids[1]})'
                  f' ..... ', end = '')
            self._extract(procset=procset,use_windows=use_windows, method = method, **kwargs)

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

                    self._extract(procset=procset,use_windows=use_windows, method = method,**kwargs)

            endtime = time.time()
            print(f'{np.round(endtime - starttime, 2)} s')

    def extract(self, procset = None, method = 'max',apply_to = 'all', use_windows=False, **kwargs):
        """
        Extract dispersion curves

        Parameters
        ----------
        procset : str, identifier to set on which dataset the processing should be applied to
        method : str, default 'max', method for dispersion curve extraction
        apply_to : str, default 'all', whether to apply function to all streams or just the current selection
        use_windows : bool, default False, whether to apply the processing to windows
        """

        self.extract_curves(procset, method, apply_to, use_windows, **kwargs)

    def process_curves(self, type='smooth', procset = None, method = None,
                       dc_mode = 0, apply_to = 'all', use_windows=False, **kwargs):
        """
        Apply a process to a dispersion curve

        Parameters
        ----------
        type : str, which processing method to call
        procset : str, identifier to set on which dataset the processing should be applied to
        method : str, method used to obtain dispersion curve
        dc_mode : int, default 0, mode of propagation
        apply_to : str, default 'all', whether to apply function to all streams or just the current selection
        use_windows : bool, default False, whether to apply the processing to windows
        kwargs : arguments for the processing

        """

        # Apply process to current selection only
        if apply_to == 'cur':
            if self.current_stream is None:
                self.select_data(inplace = True, verbose=False)

            starttime = time.time()
            print(f'Applying {type} to dispersion curve of (SIN,REP) = ({self.selected_ids[0]}, {self.selected_ids[1]})'
                  f' ..... ', end = '')
            self.process_curve(type=type, procset=procset, method = method,
                               dc_mode=dc_mode, use_windows = use_windows, **kwargs)
            endtime = time.time()
            print(f'{np.round(endtime - starttime, 2)} s')

        # Apply process to all data sets
        elif apply_to == 'all':
            starttime = time.time()

            for sin in self.data.keys():
                for rep in self.data[sin].keys():

                    self.select_data(sin, rep, inplace=True, verbose=False)

                    sys.stdout.write(f'\rApplying {type} to dispersion curve of (SIN,REP) = ({sin}, {rep}) ..... ')
                    sys.stdout.flush()

                    self.process_curve(type=type, procset=procset, method = method,
                                       dc_mode=dc_mode, use_windows=use_windows, **kwargs)

            endtime = time.time()
            print(f'{np.round(endtime - starttime, 2)} s')

    def plot_curves(self, procset = None, method = None,
                       dc_mode = 0, apply_to = 'all', use_windows=False,**kwargs):
        """
        Plot a dispersion curve

        Parameters
        ----------
        procset : str, identifier to set on which dataset the processing should be applied to
        method : str, method used to obtain dispersion curve
        dc_mode : int, default 0, mode of propagation
        apply_to : str, default 'all', whether to apply function to all streams or just the current selection
        use_windows : bool, default False, whether to apply the processing to windows

        """

        # Apply process to current selection only
        if apply_to == 'cur':
            if self.current_stream is None:
                self.select_data(inplace = True, verbose=False)

            self.plot_curve(procset=procset, method = method,dc_mode=dc_mode, use_windows=use_windows,**kwargs)

        # Apply process to all data sets
        elif apply_to == 'all':
            for sin in self.data.keys():
                for rep in self.data[sin].keys():
                    self.select_data(sin, rep, inplace=True, verbose=False)

                    self.plot_curve(procset=procset, method = method,
                                       dc_mode=dc_mode, use_windows=use_windows,**kwargs)

    def save_curves(self, procset = None, method = None,
                       dc_mode = 0, apply_to = 'all', use_windows=False, **kwargs):
        """
        Save the dispersion curves based on receiver spread midpoint

        Parameters
        ----------
        procset : str, identifier to set on which dataset the processing should be applied to
        method : str, method used to obtain dispersion curve
        dc_mode : int, default 0, mode of propagation
        apply_to : str, default 'all', whether to apply function to all streams or just the current selection
        use_windows : bool, default False, whether to apply the processing to windows

        """

        if procset is None:
            procset = self._procset

        dir = os.path.join(self.prjdir, f'03_proc/{procset}_{method}/Mode{int(dc_mode)}')
        path2geom = os.path.join(dir, '02_geom')
        safe_makedirs(path2geom)

        xmids = []

        # Apply process to current selection only
        if apply_to == 'cur':
            if self.current_stream is None:
                self.select_data(inplace = True, verbose=False)

            starttime = time.time()
            print(f'Save dispersion curves corresponding to (SIN,REP) = ({self.selected_ids[0]}, {self.selected_ids[1]})'
                  f' to "{dir}" ..... ', end = '')
            xmid = self._save(procset=procset, method = method,dc_mode=dc_mode,
                                   use_windows=use_windows, **kwargs)
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
                          f'({sin}, {rep}) to "{dir}" ..... ')
                    sys.stdout.flush()

                    xmid = self._save(procset=procset, method = method,dc_mode=dc_mode,
                                           use_windows=use_windows, **kwargs)
                    xmids += xmid

            endtime = time.time()
            print(f'{np.round(endtime - starttime, 2)} s')

        # save the xmids to file
        np.savetxt(os.path.join(path2geom, 'xmid.txt'), xmids)

    def save(self, procset = None, method = None,
                       dc_mode = 0, apply_to = 'all', use_windows=False, **kwargs):
        """
        Save the dispersion curves based on receiver spread midpoint

        Parameters
        ----------
        procset : str, identifier to set on which dataset the processing should be applied to
        method : str, method used to obtain dispersion curve
        dc_mode : int, default 0, mode of propagation
        apply_to : str, default 'all', whether to apply function to all streams or just the current selection
        use_windows : bool, default False, whether to apply the processing to windows

        """

        self.save_curves(procset, method,dc_mode, apply_to, use_windows, **kwargs)

    # %% WINDOWING
    def moving_window(self, procset = None, apply_to = 'all', **kwargs):
        """
        Apply windowing to current selection or all data sets

        Parameters
        ----------
        procset : str, identifier to set on which dataset the processing should be applied to
        apply_to : str, default 'all', whether to apply function to all streams or just the current selection
        kwargs : window settings
        """

        if procset is None:
            procset = self._procset

        if procset != self._procset:
            self.set_new_procset(procset)

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

        self.set_loadset(procset)

    # %% curve combination
    def prepare_CC(self, procset = None, method = None,
                   dc_mode = 0, use_windows=False, **kwargs):
        """
        Prepare data for dispersion curve combination

        Parameters
        ----------
        procset : str, identifier to set on which dataset the processing should be applied to
        method : str, method used to obtain dispersion curves
        dc_mode : int, default 0, mode of propagation
        use_windows : bool, default False, whether to apply the processing to windows

        """

        if procset is None:
            procset = self._procset

        color = kwargs.pop('color', 'dodgerblue')

        params = {'procset': "'%s'" % procset, 'dc_mode': dc_mode}
        if method:
            params['method'] = "'%s'" % method

        self.CC = CombineCurves()  # location where combined dcs shall be stored

        for sin in self.data.keys():
            for rep in self.data[sin].keys():

                params['sin'] = sin
                params['rep'] = rep

                wids = self._sql.get_wids(sin, rep, procset)
                if use_windows:
                    for wid in wids or []:
                        params['wid'] = wid

                        curve_data = self._sql.read_curve(params)

                        dc = DispersionCurve()
                        dc.init_data(curve_data['frequency'], curve_data['velocity'], curve_data['error'])

                        for xmid in curve_data['xmid'].unique():
                            self.CC.append(dc, xmid, source=None, color=color)

                else:
                    params['wid'] = -1

                    curve_data = self._sql.read_curve(params)

                    dc = DispersionCurve()
                    dc.init_data(curve_data['frequency'], curve_data['velocity'], curve_data['error'])
                    self.CC.append(dc, curve_data['xmid'].unique()[0], source=None, color=color)

    def filter_CC(self):
        """Manually filter multiple dispersion curves"""

        self.CC.filter()

    def combine(self, procset = None, method = None, dc_mode = 0,
                use_windows=False, **kwargs):
        """
        Combine dispersion curves with same receiver spread location

        Parameters
        ----------
        procset : str, identifier to set on which dataset the processing should be applied to
        method : str, method used to obtain dispersion curves
        dc_mode : int, default 0, mode of propagation
        use_windows : bool, default False, whether to apply the processing to windows

        """

        if procset is None:
            procset = self._procset

        if self.CC is None:
            self.prepare_CC(procset, method = method, dc_mode = dc_mode, use_windows=use_windows, **kwargs)

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
                'method': method,
                'dc_mode': dc_mode,
                 'f': dc.frequency,
                 'v': dc.velocity,
                 'err': dc.error}

            self._sql.write_curve(data, -1, -1, procset=procset, wid=-1, xmid=key)

    def process_CC(self, type='smooth', procset=None, method = None, dc_mode=0, **kwargs):
        """
        Process the combined dispersion curves

        Parameters
        ----------
        type : str, which processing method to call
        procset : str, identifier to set on which dataset the processing should be applied to
        method : str, method used to obtain dispersion curve
        dc_mode : int, default 0, mode of propagation
        kwargs : arguments for the processing

        """

        if procset is None:
            procset = self._procset

        starttime = time.time()
        print(f'Applying {type} to dispersion curves ..... ', end='')

        params = {'sin': -1, 'rep': -1, 'wid': -1, 'procset': "'%s'" % procset,
                  'method': "'%s'" % method, 'dc_mode': dc_mode}

        curves = self._sql.read_curve(params)
        xmids = curves['xmid'].unique()

        for i, xmid in enumerate(xmids):
            params = {'sin': -1, 'rep': -1, 'wid': -1, 'procset': "'%s'" % procset,
                      'method': "'%s'" % method, 'dc_mode': dc_mode, 'xmid': xmid}

            self._process_curve(type, params, method, procset=procset, **kwargs)
            curve_data = self._sql.read_curve(params)
            dc = DispersionCurve()
            dc.init_data(curve_data['frequency'], curve_data['velocity'], curve_data['error'])

        endtime = time.time()
        print(f'{np.round(endtime - starttime, 2)} s')

    def plot_CC(self, procset=None, method = None, dc_mode = 0, pseudosection = True, **kwargs):
        """
        Plot the combined dispersion curves

        Parameters
        ----------
        procset : str, identifier to set on which dataset the processing should be applied to
        method : str, method used to obtain dispersion curve
        dc_mode : int, default 0, mode of propagation
        pseudosection : bool, plot as pseudosection
        kwargs : arguments for the processing

        """
        if procset is None:
            procset = self._procset

        params = {'sin': -1, 'rep': -1, 'wid': -1, 'procset': "'%s'" % procset,
                  'method': "'%s'" % method, 'dc_mode': dc_mode}

        _, recs_all = self._sql.get_geometry(sin='*')
        curves = self._sql.read_curve(params)

        if not curves.empty:

            xmids = curves['xmid'].unique()

            # plot dispersion curves individually
            if not pseudosection:
                for i, xmid in enumerate(xmids):
                    curve_data = curves[curves['xmid'] == xmid]
                    dc = DispersionCurve()
                    dc.init_data(curve_data['frequency'], curve_data['velocity'], curve_data['error'])
                    dc.plot(**kwargs)

            # plot pseudosection
            else:
                cmap = kwargs.pop('cmap', 'viridis')
                show = kwargs.pop('show', True)
                axes = kwargs.pop('axes', None)

                vmin = kwargs.pop('vmin', 200)
                vmax = kwargs.pop('vmax', 500)

                fmin = kwargs.pop('fmin', curves['frequency'].min())
                fmax = kwargs.pop('fmax', curves['frequency'].max())

                title = kwargs.pop('title', '')
                outfile = kwargs.pop('outfile', None)

                if axes is None:
                    fig, ax = plt.subplots()
                else:
                    ax = axes
                    fig = ax.figure

                for xmid in xmids:
                    curve_data = curves[curves['xmid'] == xmid]
                    dc = DispersionCurve()
                    dc.init_data(curve_data['frequency'], curve_data['velocity'], curve_data['error'])

                    dc.plotColumn(axes=ax,
                                  xmid=xmid,
                                  vmin=vmin, vmax=vmax,
                                  cmap=cmap, y_value='f', **kwargs)

                plot_colorBar(ax, vmin, vmax, cmap=cmap, orientation='vertical')
                ax.set_xlim([recs_all['rx'].min(), recs_all['rx'].max()])
                ax.set_ylim([fmin, fmax])

                ax.set_title(title)
                if outfile:
                    fig.savefig(outfile)

                if show:
                    plt.tight_layout()
                    plt.show()

                return ax


    def save_CC(self, procset=None, method = None, dc_mode=0, format='csv', **kwargs):
        """
        Save the dispersion curves based on receiver spread midpoint

        Parameters
        ----------
        procset : str, identifier to set on which dataset the processing should be applied to
        method : str, method used to obtain dispersion curve
        dc_mode : int, default 0, mode of propagation
        format : str, default 'csv', in which format the dispersion curve should be saved (dinver and ParkSeis support)

        """

        if procset is None:
            procset = self._procset

        params = {'sin': -1, 'rep': -1, 'wid': -1, 'procset': "'%s'" % procset,
                  'method': "'%s'" % method, 'dc_mode': dc_mode}

        curves = self._sql.read_curve(params)
        xmids = np.sort(curves['xmid'].unique())

        # save the receiver spread midpoints
        path2dc = os.path.join(self.prjdir, f'03_proc/{procset}_{method}_CC/Mode{int(dc_mode)}')
        path2geom = os.path.join(path2dc, '1_geom')

        starttime = time.time()
        print(f'Saving disperion curves to "{path2dc}" ..... ', end='')

        safe_makedirs(path2geom)
        np.savetxt(os.path.join(path2geom, 'xmid.txt'), xmids)

        # save the dispersion curves
        for i, xmid in enumerate(xmids):
            params = {'sin': -1, 'rep': -1, 'wid': -1, 'procset': "'%s'" % procset,
                      'method': "'%s'" % method, 'dc_mode': dc_mode, 'xmid': xmid}
            self._save_dc(path2dc, 'dc%d' % i, params, format=format, **kwargs)

        endtime = time.time()
        print(f'{np.round(endtime - starttime, 2)} s')


class Tomo2DManager(BaseManager):
    def __init__(self, prjdir, path2raw=None, path2geom=None, settings = None, database = 'swa.db',**kwargs):
        """
        Manager to run the tomographic-like approach from Barone et al. (2019)

        Parameters
        ----------
        prjdir : str, project directory
        path2raw : str, optional, path to the raw seismic data
        path2geom : str, optional, path to the geometry file
        settings : DataFrame, settings for the processing and visualisation
        database : str, name of the database
        """
        super().__init__(prjdir, path2raw, path2geom, settings, database,**kwargs)

    def plot_streams(self, type='seismogram', procset = None, apply_to = 'all', use_windows=False, **kwargs):
        """
        Plot the stream data

        Parameters
        ----------
        type : str, plot type
        procset : str, identifier to set on which dataset the processing should be applied to
        apply_to : str, default 'all', whether to apply function to all streams or just the current selection
        use_windows : bool, default False, whether to apply the processing to windows
        """

        if procset is None:
            procset = self._procset

        # Apply process to current selection only
        if apply_to == 'cur':
            if self.current_stream is None:
                self.select_data(inplace = True, verbose=False)

            self._plot(type,procset=procset, use_windows=use_windows, **kwargs)

        # Apply process to all data sets
        elif apply_to == 'all':
            for sin in self.data.keys():
                for rep in self.data[sin].keys():
                    self.select_data(sin, rep, inplace=True, verbose=False)
                    self._plot(type, procset=procset, use_windows=use_windows,**kwargs)

    def plot(self, type='seismogram', procset = None, apply_to = 'all', use_windows=False, **kwargs):
        """
        Plot the stream data

        Parameters
        ----------
        type : str, plot type
        procset : str, identifier to set on which dataset the processing should be applied to
        apply_to : str, default 'all', whether to apply function to all streams or just the current selection
        use_windows : bool, default False, whether to apply the processing to windows
        """

        if type == 'pseudosection':
            ax = self.plot_pseudosection(procset, **kwargs)
            return ax
        else:
            self.plot_streams(type,procset,apply_to,use_windows,**kwargs)

    def prepare_streams(self, min_offset=-np.inf, max_offset=np.inf, min_rec = 6, procset = None):
        """
        retrieve subsets of the data based on forward and reverse offset shots

        Parameters
        ----------
        min_offset : float, minimum offset to consider for trimming stream
        max_offset : float, maximum offset to consider for trimming stream
        min_rec : int, mininum number of receivers to keep for trimming down data
        procset : str, identifier to set on which dataset the processing should be applied to

        """

        if procset is None:
            procset = self._procset

        if procset != self._procset:
            self.set_new_procset(procset)

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

        self.set_loadset(procset)

    def preprocess_streams(self, type='trim', procset=None, apply_to='all', use_windows=False, **kwargs):
        """
        Apply preprocessing steps to current selection or all data sets

        Parameters
        ----------
        type : str, processing type
        procset : str, identifier to set on which dataset the processing should be applied to
        apply_to : str, default 'all', whether to apply function to all streams or just the current selection
        use_windows : bool, default False, whether to apply the processing to windows
        """

        # # check if process exists
        # if type not in ['filter', 'trim']:
        #     raise AttributeError(f'Attribute can be "filter" or "trim" not {type}.')

        if procset is None:
            procset = self._procset

        if procset != self._procset:
            self.set_new_procset(procset)

        # Apply process to current selection only
        if apply_to == 'cur':
            if self.current_stream is None:
                self.select_data(inplace=True, verbose=False)

            starttime = time.time()
            print(f'Applying {type} to (SIN,REP) = ({self.selected_ids[0]}, {self.selected_ids[1]}) ..... ', end='')

            self._preprocess(type, procset=procset, use_windows=use_windows, **kwargs)

            endtime = time.time()
            print(f'{np.round(endtime - starttime, 2)} s')

        # Apply process to all data sets
        elif apply_to == 'all':
            starttime = time.time()

            for sin in self.data.keys():
                for rep in self.data[sin].keys():
                    self.select_data(sin, rep, inplace=True, verbose=False)

                    sys.stdout.write(f'\rApplying {type} to (SIN,REP) = ({sin}, {rep}) ..... ')
                    sys.stdout.flush()

                    self._preprocess(type, procset=procset, use_windows=use_windows, **kwargs)

            endtime = time.time()
            print(f'{np.round(endtime - starttime, 2)} s')

        self.set_loadset(procset)

    def preprocess(self, type='trim', procset=None, apply_to='all', use_windows=False, **kwargs):
        """
        Apply preprocessing steps to current selection or all data sets

        Parameters
        ----------
        type : str, processing type
        procset : str, identifier to set on which dataset the processing should be applied to
        apply_to : str, default 'all', whether to apply function to all streams or just the current selection
        use_windows : bool, default False, whether to apply the processing to windows
        """

        self.preprocess_streams(type, procset, apply_to, use_windows, **kwargs)

    def compute_phasediff(self, procset = None, **kwargs):
        """
        Compute phase differences and store in database

        Parameters
        ----------
        procset : str, identifier to set on which dataset the processing should be applied to

        """

        if procset is None:
            procset = self._procset

        if procset != self._procset:
            self.set_new_procset(procset)

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

    def run(self, min_offset=3, max_offset=1e6, lam = 1, rel_err = None, procset = None, **kwargs):
        """
        Run the tomographic like approach

        Parameters
        ----------
        min_offset : float, minimum offset to consider for trimming stream
        max_offset : float, maximum offset to consider for trimming stream
        lam : int, regularization strength
        rel_err : float or None, default None, error to consider in the error-weighted least-squares approach
        procset : str, identifier to set on which dataset the processing should be applied to

        """

        if procset is None:
            procset = self._procset

        np.set_printoptions(threshold=sys.maxsize)
        starttime = time.time()
        print(f'Running tomographic-like approach ..... ', end='')

        # ensure phasediff table exists
        if 'pd' not in self._sql.get_tables():
            self.compute_phasediff(procset)

        # frequencies
        sql = (f"""SELECT DISTINCT frequency
                   FROM pd
                   WHERE procset=='%s' AND sin==%d AND calc=='%s'"""
               % (procset, 1, 'NONE'))

        freq = self._sql.read_sql(sql)['frequency'].values

        # geometry
        _, recs_all = self._sql.get_geometry(sin='*')
        dx = np.mean(np.diff(recs_all['rx'].iloc[:-1].values))
        nrec = len(recs_all)
        nshot = len(self.data)

        phi_vel_all = np.zeros((nrec - 1, len(freq)))

        # MAIN FREQUENCY LOOP
        for jj, f in enumerate(freq):

            # allocate generously; shrink later
            maxrows = 2 * nshot * (nrec - 1)
            A = np.zeros((maxrows, nrec - 1))
            dphi = np.zeros((maxrows,))
            variance = np.zeros((maxrows,))

            iii = 0  # row counter

            # loop over shots
            for sin in self.data.keys():

                _, _, _, sht = self._sql.read_data(sin, 1, procset='raw')
                _, recs = self._sql.get_geometry(sin=sin)

                shot_x = sht['sx'].item()
                rx_all = recs_all['rx'].iloc[:-1].values

                offset = rx_all - shot_x

                columns = ['pd%d' % i for i in range(1, len(offset) + 1)]

                if len(self.data[sin]) > 1:
                    pd_mean = self._sql.read_pd(sin, procset, calc='AVG', columns=columns)
                    pd_std = self._sql.read_pd(sin, procset, calc='STDEV', columns=columns)
                else:
                    pd_mean = self._sql.read_pd(sin, procset, calc='NONE', columns=columns)
                    pd_std = None

                # FORWARD (offset > 0)
                fwd_mask = (
                        (offset >= min_offset) &
                        (offset <= max_offset) &
                        (rx_all >= recs['rx'].iloc[:-1].min()) &
                        (rx_all <= recs['rx'].iloc[:-1].max()) &
                        (pd_mean.iloc[jj, :] < 0)
                )
                fwd_idx = np.where(fwd_mask)[0]

                for ii in fwd_idx:
                    A[iii, ii] = dx
                    dphi[iii] = pd_mean.iloc[jj, ii]

                    # variance
                    if rel_err is not None:
                        variance[iii] = (rel_err * dphi[iii]) ** 2
                    elif pd_std is not None:
                        variance[iii] = pd_std.iloc[jj, ii] ** 2
                    else:
                        variance[iii] = 1.0

                    iii += 1

                # REVERSE (offset < 0)
                rev_mask = (
                        (offset <= -min_offset) &
                        (offset >= -max_offset) &
                        (rx_all >= recs['rx'].iloc[:-1].min()) &
                        (rx_all <= recs['rx'].iloc[:-1].max()) &
                        (pd_mean.iloc[jj, :] > 0)
                )
                rev_idx = np.where(rev_mask)[0]

                for ii in rev_idx:
                    A[iii, ii] = -dx
                    dphi[iii] = pd_mean.iloc[jj, ii]

                    if rel_err is not None:
                        variance[iii] = (rel_err * dphi[iii]) ** 2
                    elif pd_std is not None:
                        variance[iii] = pd_std.iloc[jj, ii] ** 2
                    else:
                        variance[iii] = 1.0

                    iii += 1

            # trim system to actual rows
            A = A[:iii, :]
            dphi = dphi[:iii]
            variance = variance[:iii]

            # enforce non-zero variance
            variance = np.where(variance <= 0, np.median(variance[variance > 0]), variance)

            # Weight matrix
            weights = 1.0 / variance
            w = np.diag(weights)

            # Solve ystem
            phi_vel, phi_model = tomo2D_phasediff(lam=lam, f=f, A=A, dphi=dphi, w=w)
            phi_vel_all[:, jj] = phi_vel

            # plot results
            if kwargs.setdefault('showResults', False):
                recs_plot = np.asarray(recs_all['rx'].iloc[:-1])

                axes = kwargs.pop('axes', None)
                outfile = kwargs.pop('outfile', None)

                if axes is None:
                    fig, ax = plt.subplots(1,2, figsize=(6, 2))
                else:
                    ax = axes
                    fig = ax.figure

                ax[0].plot(dphi,color = 'k', marker = 'o', markersize=5)
                ax[0].plot(phi_model, color = 'r')
                ax[0].set_xlabel("offset (m)")
                ax[0].set_ylabel(f"phase differences (rad)")
                ax[0].grid()

                ax[1].scatter(recs_plot,phi_vel, s=15, c='darkgrey', marker ='o',
                          edgecolor='k', linewidth=0.2, zorder=-2, label = f'f = {round(f)} Hz')
                ax[1].set_xlim([np.min(recs_plot),np.max(recs_plot)])
                ax[1].set_ylim([10,600])
                ax[1].set_ylabel(f"phase velocity (m/s)")
                ax[1].set_xlabel("offset (m)")
                ax[1].legend(loc = 'lower right', frameon=True)
                ax[1].grid()

                if outfile:
                    parent = os.path.dirname(outfile)
                    safe_makedirs(parent)
                    fig.savefig(outfile)
                    plt.close()
                else:
                    plt.show()

        # Store curves
        xmids = recs_all['rx'].iloc[:-1].values + dx / 2

        for i in range(len(phi_vel_all)):
            data = {
                'xmid': xmids[i],
                'method': 'tomo2D',
                'dc_mode': 0,
                'f': freq,
                'v': phi_vel_all[i, :],
                'err': np.zeros_like(phi_vel_all[i, :])
            }

            self._sql.write_curve(data, -1, -1, wid=-1,
                                  procset=procset, xmid=data['xmid'])

        print(f'{np.round(time.time() - starttime, 2)} s')

    def process_curves(self, type='smooth', procset = None, method = 'tomo2D',dc_mode = 0,  **kwargs):
        """
        Apply a process to a dispersion curve

        Parameters
        ----------
        type : str, which processing method to call
        procset : str, identifier to set on which dataset the processing should be applied to
        method : str, method used to obtain dispersion curve
        dc_mode : int, default 0, mode of propagation
        kwargs : arguments for the processing

        """

        if procset is None:
            procset = self._procset

        starttime = time.time()
        print(f'Applying {type} to dispersion curves ..... ', end = '')

        params = {'sin': -1, 'rep': -1, 'wid': -1, 'procset': "'%s'" % procset,
                  'method': "'%s'" % method, 'dc_mode': dc_mode}

        curves = self._sql.read_curve(params)
        xmids = curves['xmid'].unique()

        for i,xmid in enumerate(xmids):

            params = {'sin': -1, 'rep': -1, 'wid': -1, 'procset': "'%s'" % procset,
                      'method': "'%s'" % method, 'dc_mode': dc_mode, 'xmid': xmid}

            self._process_curve(type, params, method = 'tomo2D', procset=procset, **kwargs)

        endtime = time.time()
        print(f'{np.round(endtime - starttime, 2)} s')

    def plot_curves(self, procset = None, method = 'tomo2D',dc_mode = 0, **kwargs):
        """
        Plot dispersion curves

        Parameters
        ----------
        procset : str, identifier to set on which dataset the processing should be applied to
        method : str, method used to obtain dispersion curve
        dc_mode : int, default 0, mode of propagation

        """

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
        """
        Save the dispersion curves based on receiver spread midpoint

        Parameters
        ----------
        procset : str, identifier to set on which dataset the processing should be applied to
        method : str, method used to obtain dispersion curve
        dc_mode : int, default 0, mode of propagation
        format : str, default 'csv', in which format the dispersion curve should be saved (dinver and ParkSeis support)

        """

        if procset is None:
            procset = self._procset

        params = {'sin': -1, 'rep': -1, 'wid': -1, 'procset': "'%s'" % procset,
                  'method': "'%s'" % method, 'dc_mode': dc_mode}

        curves = self._sql.read_curve(params)
        xmids = curves['xmid'].unique()

        # save the receiver spread midpoints
        path2dc = os.path.join(self.prjdir, f'03_proc/{procset}_{method}/Mode{int(dc_mode)}')
        path2geom = os.path.join(path2dc, '02_geom')

        starttime = time.time()
        print(f'Saving disperion curves to "{path2dc}" ..... ', end='')

        safe_makedirs(path2geom)
        np.savetxt(os.path.join(path2geom,'xmid.txt'), xmids)

        # save the dispersion curves
        for i,xmid in enumerate(xmids):

            params = {'sin': -1, 'rep': -1, 'wid': -1, 'procset': "'%s'" % procset,
                      'method': "'%s'" % method, 'dc_mode': dc_mode,'xmid': xmid}

            self._save_dc(path2dc, 'dc%d' % i, params, format=format, **kwargs)

        endtime = time.time()
        print(f'{np.round(endtime - starttime, 2)} s')


    def save(self, procset=None, method='tomo2D', dc_mode=0, format = 'csv', **kwargs):
        """
        Save the dispersion curves based on receiver spread midpoint

        Parameters
        ----------
        procset : str, identifier to set on which dataset the processing should be applied to
        method : str, method used to obtain dispersion curve
        dc_mode : int, default 0, mode of propagation
        format : str, default 'csv', in which format the dispersion curve should be saved (dinver and ParkSeis support)

        """

        self.save_curves(procset, method, dc_mode, format, **kwargs)
