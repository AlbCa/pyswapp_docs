"""python class for manipulating an Obspy stream"""
import copy
import os.path
from collections import OrderedDict

import obspy
import obspy.signal

from matplotlib.offsetbox import AnchoredText
from scipy import signal, special

from _curve import *
from interactive_tools import *
from utils import *

import warnings

warnings.simplefilter(action='ignore', category=FutureWarning)

# TODO: generalization; file names
# TODO: define a project structure and directory

# TODO remove channels, stacking, skip traces (done)
# TODO mute interactive filter choice and alpha
# TODO pick interactive; reset picks but keep boundaries?; mouse scrolling to tighten bounds? (done)
# TODO stacking (done)
# TODO F-K transformation and back transformation (done)
# TODO F-K filtering (done)
# TODO LRT
# TODO swept frequency plot (done)
# TODO Cross-Correlation (done)
# TODO Tomography-like approach
# TODO Backscatter analysis for anomaly detection
# TODO LMO (done)
# TODO DLMO
# TODO modify to work with 3D coordinates
# TODO plot excitability of modes

class SeismicStream:
    """class to manipulate a seismic record for the analysis of surface waves"""

    def __init__(self, fname, settings = None,
                 geometry_file = None, source_index = 0,
                 channel_nr=1001, pre_trigger=0):
        """
        initialize stream object and settings

        @param fname: str, containing a file name
        @param settings: dict, settings
        @param receiver_coordinates: list, optional
        @param source_coordinates: list, optional
        @param channel_nr: int, optional
        @param pre_trigger: float, optional
        """

        # seismic record filename
        self.fname = fname
        _, fi = os.path.split(self.fname)
        pre, ext = os.path.splitext(fi)
        self.pre = pre
        self.ext = ext

        # initialization of parameters
        self._init_params()

        # processing settings
        if settings is not None:
            self._settings = settings
        else:
            self._settings = create_settings_dict()

        # set processing settings
        self._apply_settings()

        # read the seismic record file and initialize the stream object
        self._read_data(fname=fname,
                       geometry_file = geometry_file,
                       source_index = source_index,
                       channel_nr = channel_nr,
                       pre_trigger=pre_trigger)

        # set shot parameters
        self._shot_params()

    def _apply_settings(self):
        """apply processing settings from settings dictionary
        for pre-processing, wave field transformation and picking"""

        preproc_settings = self._settings['preproc']
        trafo_settings = self._settings['trafo']
        pck_settings = self._settings['picking']
        plt_settings = self._settings['plotting']

        # preprocessing settings
        self.pad = preproc_settings['zero_padding']['apply'] # apply padding
        self.df = preproc_settings['zero_padding']['df'] # step length

        self.norm_amps = preproc_settings['normalize_amps']['apply']  # apply amplitude normalization
        self.use_local_max = preproc_settings['normalize_amps']['local_max'] # use local maxima

        # DC picking settings
        self._pck_mode = pck_settings['mode'] # picking mode

        # wave field transformation settings
        self.trafo_type = trafo_settings['type'] # transformation type
        self.fmin = trafo_settings['fmin']  # min frequency
        self.fmax = trafo_settings['fmax']  # max frequency
        self.vmin = trafo_settings['vmin']  # min testing velocity
        self.vmax = trafo_settings['vmax']  # max testing velocity
        self.vstep = trafo_settings['velstep']  # velocity increment
        self.SFR_time = trafo_settings['SFR_time']  # time for the SFR

        # plotting
        self.kmin = plt_settings['FK']['kmin'] # min wave number
        self.kmax = plt_settings['FK']['kmax'] # max wave number
        self.norm_power = plt_settings['normalize_amps']['apply']# apply amplitude normalization
        self.use_local_max_power = plt_settings['normalize_amps']['local_max']# use local maxima

    def _read_data(self, fname, geometry_file = None, source_index = 0,
                         channel_nr = 1001, pre_trigger=0):
        """
        read a shotfile and extract relevant information

        @param fname: str, file name
        @param receiver_coordinates: list, optional
        @param source_coordinates: list, optional
        @param channel_nr: int, optional
        @param pre_trigger: float, optional
        """

        # read and update the header of the .sg2 file
        if fname.endswith('.sg2') or fname.endswith('.dat'):
            self._read_sg2(fname,geometry_file,source_index,channel_nr)
        # read and update header of synthetic data
        elif fname.endswith('.syn') or fname.endswith('.mseed'):
            self._read_syn(fname, geometry_file,source_index, channel_nr, pre_trigger)
        # read and update header of the .sgy file
        elif fname.endswith('.sgy'):
            self._read_sgy(fname, geometry_file,source_index, channel_nr)
        else:
            raise NotImplementedError("File format not supported.")

    def _read_sg2(self, fname, geometry_file,source_index, channel_nr):
        """
        Read stream data with .sg2 file format
        @param fname: str, file name
        @param receiver_coordinates: list, optional
        @param source_coordinates: list, optional
        @param channel_nr: int, optional
        """

        st_new = obspy.Stream()
        st = obspy.read(fname)

        for ti, trace in enumerate(st):

            # %% VERSION 1: Geometry file is provided
            if (geometry_file is not None):

                if os.path.exists(geometry_file):
                    shot_files, source_coordinates, receiver_coordinates = read_geometry(geometry_file)
                else:
                    raise FileNotFoundError

                # check the length of the stream object
                if len(st) != len(receiver_coordinates):
                    raise ValueError(f'Receiver and trace number missmatch. {len(st)} != {len(receiver_coordinates)}')
                else:
                    # %% Get geometry information (position of shot and geophone)
                    rx = receiver_coordinates[ti, 0]  # set receiver location
                    sx = source_coordinates[source_index,0]  # set source location

            # %% VERSION 2: No geometry file is provided
            else:
                #  header does not contain geometry information
                if 'RECEIVER_LOCATION' not in trace.stats.seg2:
                    warnings.warn('Receiver location is missing. '
                          'Provide a geometry file or edit shot file header.\n'
                          'Using dummy geometry for now.')
                    rx = ti
                #  header contains geometry information
                else:
                    if len(trace.stats.seg2['RECEIVER_LOCATION'].split(' ')) > 1:
                        # trace.stats.seg2['RECEIVER_LOCATION'] = ti
                        rx = float(trace.stats.seg2['RECEIVER_LOCATION'].split(' ')[0])
                    else:
                        rx = float(trace.stats.seg2['RECEIVER_LOCATION'])

                #  header does not contain geometry information
                if 'SOURCE_LOCATION' not in trace.stats.seg2:
                    warnings.warn('Source location is missing. '
                          'Provide a geometry file or edit shot file header.\n'
                          'Using dummy geometry for now.')
                    sx = 0
                #  header contains geometry information
                else:
                    if len(trace.stats.seg2['SOURCE_LOCATION'].split(' ')) > 1:
                        sx = float(trace.stats.seg2['SOURCE_LOCATION'].split(' ')[0])
                    else:
                        sx = float(trace.stats.seg2['SOURCE_LOCATION'])

            # header information
            starttime = st[0].stats.starttime
            ch = str(channel_nr + ti)  # set channel number
            dt = trace.stats.delta  # sampling interval in s
            npts = trace.stats.npts  # number of samples
            sr = trace.stats.sampling_rate
            delay = float(trace.stats.seg2.DELAY)  # pre trigger
            sn = str(trace.stats.seg2.SHOT_SEQUENCE_NUMBER)  # shot sequence number

            # new trace
            header = {
                'starttime': starttime,
                'channel': ch,
                'delta': dt,
                'npts': npts,
                'delay': delay,
                'sampling_rate': sr,
                'station': sn,
                'rx': rx,
                'sx': sx}
            trace_new = obspy.core.trace.Trace(data=trace.data, header=header)
            st_new.append(trace_new)

        self._st = st_new

    def _read_sgy(self, fname, geometry_file,source_index, channel_nr):
        """Read stream data with .sg2 file format
        @param fname: str, file name
        @param receiver_coordinates: list, optional
        @param source_coordinates: list, optional
        @param channel_nr: int, optional
        """

        st_new = obspy.Stream()
        st = obspy.read(fname)

        for ti, trace in enumerate(st):

            # %% VERSION 1: Geometry file is provided
            if (geometry_file is not None):

                if os.path.exists(geometry_file):
                    shot_files, source_coordinates, receiver_coordinates = read_geometry(geometry_file)
                else:
                    raise FileNotFoundError

                # check the length of the stream object
                if len(st) != len(receiver_coordinates):
                    raise ValueError(f'Receiver and trace number missmatch. {len(st)} != {len(receiver_coordinates)}')
                else:
                    # %% Get geometry information (position of shot and geophone)
                    rx = receiver_coordinates[ti, 0]  # set receiver location
                    sx = source_coordinates[source_index, 0]  # set source location
                    sn = str(source_index)  # shot sequence number

            # %% VERSION 2: No geometry file is provided
            else:
                scale = trace.stats.segy['trace_header']['scalar_to_be_applied_to_all_coordinates']
                sx_int = int(trace.stats.segy['trace_header']['source_coordinate_x'])
                sy_int = int(trace.stats.segy['trace_header']['source_coordinate_y'])
                rx_int = int(trace.stats.segy['trace_header']['group_coordinate_x'])
                ry_int = int(trace.stats.segy['trace_header']['group_coordinate_y'])

                if sx_int != 0:
                    sx = sx_int / abs(scale) if scale < 0 else sx_int * scale
                elif sy_int != 0:
                    sx = sy_int / abs(scale) if scale < 0 else sy_int * scale
                else:
                    warnings.warn('Source location is missing. '
                          'Provide a geometry file or edit shot file header.\n'
                          'Using dummy geometry for now.')
                    sx = 0

                if rx_int != 0:
                    rx = sx_int / abs(scale) if scale < 0 else rx_int * scale
                elif ry_int != 0:
                    rx = ry_int / abs(scale) if scale < 0 else ry_int * scale
                else:
                    warnings.warn('Receiver location is missing. '
                          'Provide a geometry file or edit shot file header.\n'
                          'Using dummy geometry for now.')
                    rx = ti
                sn = str(trace.stats["station"])

            starttime = st[0].stats.starttime
            dt = trace.stats.delta  # sampling interval in s
            npts = trace.stats.npts  # number of samples
            sr = trace.stats.sampling_rate
            delay = trace.stats.segy['trace_header']['delay_recording_time']  # set the pre-trigger value
            ch = str(channel_nr + ti)  # set channel number

            # new trace
            header = {
                'starttime': starttime,
                'channel': ch,
                'delta': dt,
                'npts': npts,
                'delay': delay,
                'sampling_rate': sr,
                'station': sn,
                'rx': rx,
                'sx': sx}
            trace_new = obspy.core.trace.Trace(data=trace.data, header=header)
            st_new.append(trace_new)

        self._st = st_new

    def _read_syn(self, fname, geometry_file, source_index, channel_nr, pre_trigger):
        """Read synthetic data in .mseed format
        @param fname: str, file name
        @param receiver_coordinates: list, optional
        @param source_coordinates: list, optional
        @param channel_nr: int, optional
        @param pre_trigger: float, optional
        """

        st_new = obspy.Stream()
        st = obspy.read(fname)

        # %% VERSION 1: Geometry file is provided
        if (geometry_file is not None):

            if os.path.exists(geometry_file):
                shot_files, source_coordinates, receiver_coordinates = read_geometry(geometry_file)
            else:
                raise FileNotFoundError
            # check the length of the stream object
            if len(st) != len(receiver_coordinates):
                raise ValueError(f'Receiver and trace number missmatch. {len(st)} != {len(receiver_coordinates)}')
            else:
                for ti, trace in enumerate(st):

                    # %% Get geometry information (position of shot and geophone)
                    rx = receiver_coordinates[ti, 0]  # set receiver location
                    sx = source_coordinates[source_index, 0]  # set source location

                    starttime = st[0].stats.starttime
                    ch = str(channel_nr + ti)  # set channel number
                    dt = trace.stats.delta  # sampling interval in s
                    npts = trace.stats.npts  # number of samples
                    sr = trace.stats.sampling_rate
                    sn = str(trace.stats["station"])  # set the shot sequence number
                    if (sn is None) or (sn == ''):
                        sn = str(source_index)
                        #sn = int(re.findall(r'\d+', os.path.basename(fname))[0])
                    delay = pre_trigger  # set the pre-trigger value

                    # new trace
                    header = {
                        'starttime': starttime,
                        'channel': ch,
                        'delta': dt,
                        'npts': npts,
                        'delay': delay,
                        'sampling_rate': sr,
                        'station': sn,
                        'rx': rx,
                        'sx': sx}
                    trace_new = obspy.core.trace.Trace(data=trace.data, header=header)
                    st_new.append(trace_new)

                self._st = st_new

        # %% VERSION 2: No geometry file is provided
        else:
            raise ValueError('You need to provide additional information on the '
                          'receiver and source coordinates for files with the MiniSEED format.')

    def _shot_params(self):
        """set shot parameters"""
        try:
            self.aqu_date = self._st.stats.seg2.ACQUISITION_DATE # acquisition time and date
        except AttributeError:
            self.aqu_date = None

        self.dt = self._st[0].stats.delta  # sampling interval in s
        self.npts = self._st[0].stats.npts  # number of samples
        self.delay = float(self._st[0].stats.delay)  # pre trigger
        #self.sn = int(self._st[0].stats.sn)  # shot sequence number

        self.receiver = self._receiver() # receiver positions
        self.source = self._source() # source location
        self.midpoint = self._midpoint(self.receiver) # receiver spread midpoint
        self.nchannels = self._nchannels() # number of receivers
        self.dx_list = self._dx(self.receiver) # receiver separation
        self.dx = np.median(abs(self.dx_list)) # median receiver separation

    def _init_params(self):
        """initialize some parameters"""
        self._pst = None
        self._st_shift = None
        self.fstep = 1
        self.nstacks = 1
        self.tapered = False
        self.dispersive_energy = None
        self.velocity = None
        self.frequency = None
        self._pick = False
        self._picks = {}
        self.curve = None

    def _update_params_from_amps(self, amps):
        """update npts and nchannels"""
        nchannels,npts = amps.shape()
        self.npts = npts
        self.nchannels = nchannels

    def _update_params_from_stream(self, st):
        """update shot parameters"""
        self.npts = len(st[0].data)
        self.nchannels = len(st)

        self.receiver = self._receiver()
        self.midpoint = self._midpoint(self.receiver)
        self.dx_list = self._dx(self.receiver)  # receiver separation
        self.dx = np.median(abs(self.dx_list))

    def _return_stream(self):
        """return current stream object"""
        if self._pst is None:
            st = self._st.copy()
        else:
            st = self._pst.copy()
        return st

    def _print_stats(self):
        """print stream information"""

        if self._pst is None:
            for trace in self._st:
                print("#### RAW DATA STATS ####")
                print(trace.stats)
        else:
            for trace in self._pst:
                print("#### PROC DATA STATS ####")
                print(trace.stats)

    def _save_stream(self, fot, pre):
        """save stream in .mseed file format"""

        safe_makedirs(fot)
        outfile = os.path.join(fot, f"Shot_{pre}.syn")

        if self._pst is None:
            st = self._st.copy()
        else:
            st = self._pst.copy()

        for i, trace in enumerate(st):
            trace.stats["mseed"] = {'dataquality': 'D'}

        st.write(outfile, format='mseed')

    def _nchannels(self, st=None):
        """return number of channels"""

        if st is None:
            if self._pst is None:
                st = self._st.copy()
            else:
                st = self._pst.copy()
        else:
            st = st

        nreceiver = len(self.receiver)
        ntraces = len(st)

        if nreceiver == ntraces:
            return ntraces
        else:
            raise ValueError('Number of receiver and traces is not matching!')

    def _npts(self):
        """return number of samples"""
        return len(self._amps()[0])

    def _receiver(self, st=None):
        """return sensor positions"""

        if st is None:
            if self._pst is None:
                st = self._st.copy()
            else:
                st = self._pst.copy()
        else:
            st = st

        nchannels = len(st)
        gx = np.zeros(nchannels)
        for ti, trace in enumerate(st):
            gx[ti] = trace.stats.rx
        return gx

    def _source(self):
        """return source location (x-coordinate)"""
        return self._st[0].stats.sx

    def _midpoint(self, receiver):
        """compute midpoint of a receiver spread"""
        return (np.max(receiver)+np.min(receiver))/2

    def _offsets(self, receiver, source):
        """compute shot receiver offsets"""
        return source - receiver

    def _aoffsets(self, receiver, source):
        """compute absolute shot receiver offsets"""
        return abs(self._offsets(receiver, source))

    def _dx(self,receiver):
        """receiver separations"""
        return np.diff(receiver)

    def _check_traces(self, st=None):
        """check whether a trace only contains zeros and remove it"""
        if st is None:

            if self._pst is None:
                st = self._st.copy()
            else:
                st = self._pst.copy()

        trace_list = []
        for ti, trace in enumerate(st):

            if np.sum(trace.data) == 0:
                trace_list.append(ti)

        self._remove_trace(trace_list)

    def _amps(self, st=None):
        """store amplitudes in ndarray (nchannels,nsamples)"""

        if st is None:

            if self._pst is None:
                st = self._st.copy()
            else:
                st = self._pst.copy()

        amps = np.zeros((len(st), len(st[0].data)))
        for ti, trace in enumerate(st):
            amps[ti] = trace.data
        return amps

    def _amps2st(self,amps,st = None):
        """store amplitudes (nchannels,nsamples) as obspy stream data"""

        if st is None:
            if self._pst is None:
                st_proc = self._st.copy()
            else:
                st_proc = self._pst.copy()
        else:
            st_proc = st.copy()

        if len(amps) == len(st_proc):
            for i in range(len(st_proc)):

                st_proc[i].data = amps[i]
                st_proc[i].stats.npts = len(amps[i])

        self._pst = st_proc

    def _detrend_signal(self, amps):
        """remove linear trend"""

        detrend_amps = np.zeros_like(amps)

        for i in range(amps.shape[0]):

            amp = amps[i]
            detrend_amps[i] = signal.detrend(amp)

        return detrend_amps

    def _normalize_amps(self, amps):
        """amplitude normalization"""
        norm_amps = np.zeros_like(amps)
        global_max = np.max(np.abs(amps))

        for i in range(norm_amps.shape[0]):

            amp = amps[i]
            if self.use_local_max:
                local_max = np.max(np.abs(amp))
                if local_max != 0:
                    amp = amp / np.max(np.abs(amp))
            else:
                amp = amp/global_max
            norm_amps[i] = amp

        return norm_amps

    def _apply_taper(self):
        """apply taper"""

        if self._pst is None:
            st_proc = self._st.copy()
        else:
            st_proc = self._pst.copy()

        amps = self._amps(st=st_proc)
        tapered_amps = self._taper_amps(amps)
        self._amps2st(tapered_amps)

        self.tapered = True

    def _taper_amps(self, amps):
        """apply taper window"""

        taper_amps = np.zeros_like(amps)

        receiver = self.receiver

        # tapering function
        taper_func = getattr(signal.windows, 'hamming')
        taper_win = taper_func(len(receiver))

        for i in range(len(amps[0])):
            amp = amps[:, i]
            taper_amps[:, i] = amp * taper_win

        return taper_amps

    def _flip(self):
        """reverse order of traces"""
        if self._pst is None:
            st_proc = self._st.copy()
        else:
            st_proc = self._pst.copy()

        st_proc.reverse()

        self._pst = st_proc

    def _trim_times(self, start_time, end_time):
        """cut times of stream"""

        if self._pst is None:
            st_proc = self._st.copy()
        else:
            st_proc = self._pst.copy()

        for t, trace in enumerate(st_proc.traces):
            trace.trim(start_time, end_time)

        self._pst = st_proc
        self._update_params_from_stream(st_proc)

    def _trim_by_offsets(self, min_offset, max_offset):
        """cut traces outside of the offsets limits"""

        if self._pst is None:
            st_proc = self._st.copy()
        else:
            st_proc = self._pst.copy()

        receiver = self.receiver
        source = self.source
        offsets = self._offsets(source,receiver)

        st_new = obspy.Stream()
        receiver_subset = []
        for i, (offset, trace) in enumerate(zip(offsets, st_proc.traces)):

            # forward shots
            if (min_offset >= 0) and (max_offset > 0):
                if (offset >= min_offset) and (offset <= max_offset):
                    st_new.append(trace)
                    receiver_subset.append(receiver[i])
                if (offset > max_offset):
                    break

            # reverse shots
            elif (min_offset <= 0) and (max_offset < 0):
                if (offset <= min_offset) and (offset >= max_offset):
                    st_new.append(trace)
                    receiver_subset.append(receiver[i])
                if (offset > min_offset):
                    break
        # update
        self._pst = st_new
        self._update_params_from_stream(st_new)

    def _trim_by_receiver_separation(self,sep):
        """select channels with specified geophone separation"""

        if self._pst is None:
            st_proc = self._st.copy()
        else:
            st_proc = self._pst.copy()

        receiver = self.receiver
        unique_sep = np.unique(self.dx_list)

        # in case of equidistant geophone separation
        if len(unique_sep) == 1:
            if sep % self.dx == 0:
                step = int(sep/self.dx)
            else:
                step = round(sep / self.dx)

            st_new = obspy.Stream()
            for trace in st_proc[::step]:
                st_new.append(trace)

        # in case of varying geophone separation
        else:
            # if sep occurs
            if sep in unique_sep:
                first = np.where(self.dx_list == sep)[0][0]
                rdist = receiver[first] - receiver[first+1:]
                counter = 1
                indices = [first]
                for i,d in enumerate(rdist):
                    if abs(d) == sep*(counter):
                        indices.append(i+first+1)
                        counter+=1

                st_new = obspy.Stream()
                for i in indices:
                    st_new.append(st_proc[i])

            else:
                if sep > np.min(unique_sep):
                    # determine first occurrence
                    first_shift = 0
                    for i,r0 in enumerate(receiver):
                        rdist_tmp = receiver[i] - receiver[i + 1:]
                        first_tmp = np.where(abs(rdist_tmp) == sep)[0]
                        if len(first_tmp) > 0:
                            first_shift = i
                            break

                    # get all consecutive traces
                    if len(first_tmp) > 0:
                        first = first_shift
                        rdist = receiver[first] - receiver[first + 1:]
                        counter = 1
                        indices = [first]
                        for i, d in enumerate(rdist):
                            if abs(d) == sep * (counter):
                                indices.append(i + first + 1)
                                counter += 1
                        st_new = obspy.Stream()
                        for i in indices:
                            st_new.append(st_proc[i])
                    else:
                        raise ValueError('Requested receiver separation is not valid.')

                else:
                    raise ValueError('Requested receiver separation is not valid.')

        # update
        self._pst = st_new
        self._update_params_from_stream(st_new)

    def _trim_by_trace_window(self, nwin, xmid):
        """select traces around xmid and window size"""

        nchannels = self.nchannels

        if nwin <= nchannels:
            if (nwin % 2) == 0:
                if xmid in self._receiver():
                    trace_select = range(int((nchannels - nwin) / 2), int((nchannels + nwin) / 2 + 1))
                else:
                    trace_select = range(int((nchannels - nwin) / 2), int((nchannels + nwin) / 2))
            else:
                if xmid in self._receiver():
                    trace_select = range(int((nchannels - nwin - 1) / 2), int((nchannels + nwin - 1) / 2) + 2)
                else:
                    trace_select = range(int((nchannels - nwin - 1) / 2), int((nchannels + nwin - 1) / 2) + 1)

            return trace_select
        else:
            return None

    def _select_traces(self, trace_select):
        """select a subset of a stream based on trace indices"""

        receiver = self.receiver

        if self._pst is None:
            st_proc = self._st.copy()
        else:
            st_proc = self._pst.copy()

        st_new = obspy.Stream()
        receiver_subset = []
        for i, trace in enumerate(st_proc):
            if i in trace_select:
                st_new.append(trace)
                receiver_subset.append(receiver[i])

        # update
        self._pst = st_new
        self._update_params_from_stream(st_new)

    def _filter_freq(self,type,freqmin=None,freqmax=None):
        """apply frequency filtering"""

        if self._pst is None:
            st_proc = self._st.copy()
        else:
            st_proc = self._pst.copy()

        if type == 'bandpass':
            if (freqmin is not None) and (freqmax is not None):
                st_proc.filter(type=type,
                               freqmin=freqmin,
                               freqmax=freqmax,
                                corners = 2,
                                zerophase = True)


        elif type in ['lowpass','highpass']:
            if freqmin is not None:
                freq = freqmin
            elif freqmax is not None:
                freq = freqmax

            st_proc.filter(type=type,
                           freq=freq,
                            corners = 2,
                            zerophase = True)

        self._pst = st_proc

    def _remove_trace(self, trace_indices):
        """remove a trace based on an index"""

        if self._pst is None:
            st_proc = self._st.copy()
        else:
            st_proc = self._pst.copy()

        st_new = obspy.Stream()
        receiver_subset = []
        for i, trace in enumerate(st_proc):
            if i not in trace_indices:
                st_new.append(trace)

        # update
        self._pst = st_new
        self._update_params_from_stream(st_new)

    def _mute(self, tapering='mild'):
        """
        interactive linear muting
        @param tapering: taper strength
        """

        if self._pst is None:
            st_proc = self._st.copy()
        else:
            st_proc = self._pst.copy()
        self._st_backup_mute = st_proc.copy()

        # repetition for left and right side muting
        terminate = False
        count = 0
        while terminate == False:

            fig, ax = plt.subplots(figsize=(10, 5))
            self._plotSeismogram(axes=ax, amp_scale=1)

            text = '\n'.join((
                r'$\bf{Keyboard \quad commands:}$',
                r'Press $\bf{t}$ for top or $\bf{b}$ for bottom mute.',
                r'Press $\bf{v}$ to estimate the velocity.',
                r'Press $\bf{enter}$ to refresh.',
                r'Press $\bf{crtl+z}$ to reset last step. Press $\bf{r}$ to reset.',
                r'Press $\bf{e}$ to stop the process.'))
            at = AnchoredText(text,
                               loc='lower right', prop=dict(size=6), frameon=True,bbox_to_anchor=(1., 1.15),
                       bbox_transform=ax.transAxes
                       )
            ax.add_artist(at)

            plot = SeismoInteractive(ax,receiver=self.receiver)
            ax.set_title(f'Top mute active', fontweight='bold')
            plt.tight_layout()
            plt.show()

            # extract points from points_list
            if len(plot.points) > 0:
                x, y = zip(*sorted(plot.points.items()))
                points = []
                for i in range(len(x)):
                    points.append((x[i], y[i]))

            key = plot.key
            reset = plot.reset
            reset_last = plot.reset_last
            terminate = plot.terminate

            if reset:
                self._reset_mute()
                count = 0

            if reset_last:
                self._reset_mute_last()
                count -= 1

            elif terminate is False and (not reset) and (not reset_last):
                if len(points) > 0:
                    self._linear_mute(points,key, tapering=tapering)
                    count += 1
                else:
                    terminate= True

    def _linear_mute(self, points,key='t', **kwargs):
        """
        linear muting
        @param points: list, point list containing x and y data
        @param key: str
        """

        # tapering type and settings
        taper_type = kwargs.pop('taper_type', 'tukey')
        taper_func = getattr(signal.windows, taper_type)

        kwargs_taper = {}
        if taper_type == 'tukey':
            # shape of the tukey window
            taper = kwargs.pop('tapering', 'mild')
            if taper == 'mild':
                taper_alpha = 0.3
            elif taper == 'strong':
                taper_alpha = 0.5
            elif taper == 'weak':
                taper_alpha = 0.2
            kwargs_taper['alpha'] = taper_alpha

        # data
        if self._pst is None:
            st_proc = self._st.copy()
        else:
            st_proc = self._pst.copy()
        self._st_backup_last_mute = st_proc.copy()

        receiver = np.array(self.receiver)
        dt = self.dt  # sampling rate in sec
        delay = self.delay  # pre trigger in sec
        ndelay = int(abs(delay / dt))
        npts = len(st_proc[0].data)

        # top mute boundary (straight line)
        top_idx = np.zeros_like(receiver, dtype=int)
        if key == 't':

            ((idx1, t1), (idx2, t2)) = points

            x1 = receiver[idx1]
            x2 = receiver[idx2]
            idx_between = np.where((receiver >= x1) & (receiver <= x2))[0]

            slope = (t2 - t1) / (x2 - x1)
            times = t1 + slope * (receiver[idx_between] - x1)
            top_idx_between = np.array((times / dt) + ndelay, dtype=int)
            top_idx[idx_between] = top_idx_between

        # bottom mute boundary (straight line)
        bottom_idx = np.ones_like(receiver, dtype=int) * (npts - 1)
        if key == 'b':
            ((idx1, t1), (idx2, t2)) = points

            x1 = receiver[idx1]
            x2 = receiver[idx2]
            idx_between = np.where((receiver >= x1) & (receiver <= x2))[0]

            slope = (t2 - t1) / (x2 - x1)
            times = t1 + slope * (receiver[idx_between] - x1)
            bottom_idx_between = np.array((times / dt) + ndelay, dtype=int)
            bottom_idx[idx_between] = bottom_idx_between

        # Perform windowing
        window = np.zeros(npts)
        for i, (start, stop) in enumerate(zip(top_idx, bottom_idx)):
            taper_win = taper_func(stop - start, **kwargs_taper)
            window[start:stop] = taper_win
            st_proc[i].data *= window
            window *= 0

        self._pst = st_proc

    def _reset_mute(self):

        if self._pst is None:
            self._st = self._st_backup_mute
        else:
            self._pst = self._st_backup_mute

    def _reset_mute_last(self):

        if self._pst is None:
            self._st = self._st_backup_last_mute
        else:
            self._pst = self._st_backup_last_mute


    def _zero_padding(self,amps):
        """append zeros to amplitudes to achieve a desired resolution"""

        df = self.df
        dt = self.dt

        _,npts = amps.shape
        new_npts = int(round(1 / (df * dt)))

        if new_npts > npts:
            padding = new_npts - npts
            npts = new_npts
        else:
            padding = 0 # no padding

        zero_padded_amps = np.pad(amps, [(0, 0), (padding, padding)], mode='constant', constant_values=0)

        return zero_padded_amps,padding,npts

    def _argfreq(self):
        """return the frequency ids of the selection"""

        dt = self.dt

        if self._pst is None:
            st = self._st.copy()
        else:
            st = self._pst.copy()

        amps = self._amps(st=st)

        if self.pad:
            amps, _, _ = self._zero_padding(amps)

        nchannels, npts = amps.shape

        # frequency range
        omega_fs = 2 * np.pi * 1 / dt
        omega = np.arange(npts) * (omega_fs / npts)
        freq = omega / (2 * np.pi)

        min_id = np.argmin(np.abs(freq - self.fmin))
        max_id = np.argmin(np.abs(freq - self.fmax))
        fids = np.arange(min_id, max_id + 1, step=self.fstep)

        return fids

    def _lmo(self, vel = None, bulk_shift=0):
        """
        linear move-out (LMO) correction

        @param vel: float, velocity for the LMO in m/s
        @param bulk_shift: float, optional, static shift in s applied to the time
        """

        receiver = self.receiver
        source = self.source

        # estimate the velocity from the data if it is not provided
        if vel is None:
            fig, ax = plt.subplots(figsize=(10, 5))
            self._plotSeismogram(axes=ax, amp_scale=1)

            text = '\n'.join((
                r'$\bf{Keyboard \quad commands:}$',
                r'Press $\bf{v}$ to estimate the velocity.',
                r'Press $\bf{e}$ to stop the process.',))
            at = AnchoredText(text,
                              loc='lower right', prop=dict(size=6), frameon=True, bbox_to_anchor=(1., 1.15),
                              bbox_transform=ax.transAxes
                              )
            ax.add_artist(at)

            plot = SeismoInteractive(ax, receiver=receiver)
            ax.set_title(f'Velocity estimation', fontweight='bold')
            plt.tight_layout()
            plt.show()

            if plot.slope is not None:
                vel = 1 / plot.slope

        if vel is not None:

            if self._pst is None:
                st = self._st.copy()
            else:
                st = self._pst.copy()

            amps = self._amps(st=st)

            # sample size
            iX, iT = amps.shape

            # source-receiver offsets
            offsets = self._aoffsets(receiver, source)

            t = np.arange(iT) * self.dt

            amps_lmo = np.zeros_like(amps)
            for i in range(len(amps)):
                tlmo = offsets[i] / vel
                amps_lmo[i] = np.interp(t - bulk_shift, t - tlmo, amps[i])

            self._amps2st(amps=amps_lmo)

    # def _dlmo(self):
    #     """
    #     dynamic linear moveout correction by Park et al. (1998)
    #     """

    # %% wavefield transformation
    def _apply_trafo(self,do_pick = False,save_dc = False,show=False,**kwargs):
        """
        Apply the wave field transformation

        @param do_pick: perform the picking
        @param save_dc: save the extracted dispersion curve
        @param show: show the dispersion image
        """

        keys = ['hdbf','cfdbf','fdbf', 'pfdbf','phaseshift','phase']

        # apply the transformation based on the chosen method
        if self.trafo_type.lower() in ['mopa']:
            self._MOPA(**kwargs)

            # save the dispersion curve
            if save_dc:
                kwargs.setdefault('path2disp', 'dc')
                self._save_dc(**kwargs)

        else:
            if self.trafo_type.lower() in ['hdbf','cfdbf']:
                self._fdbf()
            elif self.trafo_type.lower() in ['fdbf', 'pfdbf']:
                self._fdbf(steering='plane')
            elif self.trafo_type.lower() in ['phaseshift','phase']:
                self._phaseshift()
            #elif self.trafo_type.lower() in ['fk']:
                # self._fkdc()
                #raise NotImplementedError('Dispersion image based on FK currently not supported.')
            # elif self.trafo_type.lower() in ['lrt']:
            #     #self._lrt()
            #     raise NotImplementedError('Transformation based on LRT currently not supported.')
            else:
                raise NotImplementedError(f'Transformation "{self.trafo_type}" not supported. '
                                          f'Use one of the keys: {keys}')

            # pick the dispersion curve
            if do_pick:
                self._dcpicking(pck_mode=self._pck_mode,**kwargs)

                # save the dispersion curve
                if save_dc:
                    kwargs.setdefault('path2disp','dc')
                    self._save_dc(**kwargs)

            # show the dispersion image
            if show:
                self._plotDispersionImage(**kwargs)

    def _steering_vector(self,kx,steering = 'cylindrical',sign = -1):
        """set of phase delays (Zywicki, 1999)"""
        if steering == 'cylindrical':
            # cylindrical steering vector exp(-1j[phi(H0(kx))])
            # H0 ... Hankel function Hn = Jn + i Yn
            return np.exp(-1j * np.angle(special.j0(kx) + 1j*special.y0(kx)))
        else:
            # plane steering vector
            return np.exp(1j * kx * sign)

    def _fk_backtransform(self,FK_unwrap,iT,iX):
        """Transformation to x-t domain"""

        iF = nextpow2(iT)[1]
        FK = np.zeros((iF,iF)).astype("complex")

        FK_unwrap = np.flipud(FK_unwrap)
        pos_freq = iF // 2

        # exploit symmetry
        # top half
        FK[:pos_freq] = FK_unwrap
        # bottom half
        FK[(pos_freq+1):] = np.conjugate(np.rot90(FK_unwrap[1:],2))

        # back transformation
        FK = np.fft.ifftshift(np.conjugate(np.transpose(FK)))
        amps = np.fft.ifft2(FK,s=(iF,iF)).real
        amps = amps[:iX,:iT]

        # source-receiver offsets
        receiver = self.receiver
        source = self.source
        if source > receiver[-1]:
            amps = np.flipud(amps)

        return amps

    # def _fk_transform_kpos(self):
    #     """Transformation to F-K domain"""
    #     receiver = self.receiver
    #     source = self.source
    #
    #     # amplitude data & processing
    #     if not self.tapered:
    #         self._apply_taper()
    #
    #     if self._pst is None:
    #         st = self._st.copy()
    #     else:
    #         st = self._pst.copy()
    #
    #     amps = self._amps(st=st)
    #
    #     # source-receiver offsets
    #     if source > receiver[-1]:
    #         amps = np.flipud(amps)
    #
    #     # sample spacing
    #     dx = self.dx
    #     dt = self.dt
    #
    #     # sample size
    #     iX,iT = amps.shape
    #     iF = nextpow2(iT)[1]
    #     iK = nextpow2(iT)[1]
    #
    #     # wavenumber and frequencies
    #     freq = np.fft.fftfreq(iF, dt)
    #     k = np.fft.fftfreq(iK, dx)
    #     kw = k*2*np.pi
    #
    #     # FK transformation
    #     FK = np.fft.fft2(amps,s=(iK,iF))
    #     FK = np.fft.fftshift(np.conjugate(np.transpose(FK)))
    #
    #     # select only positive frequencies
    #     pos_freq = FK.shape[0] // 2
    #     FK_unwrap = FK[:pos_freq,:]
    #
    #     # set negative wavenumber quadrant to 0
    #     pos_kw = FK.shape[1] // 2
    #     FK_unwrap[:,:pos_kw] = 0
    #
    #     FK_unwrap = np.flipud(FK_unwrap)
    #     FK_unwrap = np.fft.fftshift(FK_unwrap,axes=1)
    #
    #     theta = np.angle(FK_unwrap)
    #     FK_abs = abs(FK_unwrap)
    #
    #     return FK_abs, theta, kw, freq,iX,iT

    def _fk_transform(self):
        """Transformation to F-K domain"""
        receiver = self.receiver
        source = self.source

        # amplitude data & processing
        if not self.tapered:
            self._apply_taper()

        if self._pst is None:
            st = self._st.copy()
        else:
            st = self._pst.copy()

        amps = self._amps(st=st)

        # source-receiver offsets
        if source > receiver[-1]:
            amps = np.flipud(amps)

        # sample spacing
        dx = self.dx
        dt = self.dt

        # sample size
        iX,iT = amps.shape
        iF = nextpow2(iT)[1]

        # wavenumber and frequencies
        freq = np.fft.fftfreq(iF, dt)
        k = np.fft.fftfreq(iF, dx)
        kw = k*2*np.pi

        # FK transformation
        FK = np.fft.fft2(amps,s=(iF,iF))
        FK = np.fft.fftshift(np.conjugate(np.transpose(FK)))

        # select only positive frequencies
        pos_freq = FK.shape[0] // 2
        FK_unwrap = FK[0:pos_freq]
        FK_unwrap = np.flipud(FK_unwrap)
        FK_unwrap = np.fft.fftshift(FK_unwrap,axes=1)

        theta = np.angle(FK_unwrap)
        FK_abs = abs(FK_unwrap)

        return FK_abs, theta, kw, freq,iX,iT

    def _fk_filter_from_pick(self, fname=None, show=False, **kwargs):
        """apply fk filter by picking boundaries"""

        # transformation
        FK_abs, theta, kw, freq, iX, iT = self._fk_transform()

        npoints = FK_abs.shape[1]

        fpos = freq[:npoints // 2]
        df = fpos[1] - fpos[0]
        fmin = np.argmin(np.abs(fpos - self.fmin))
        fmax = np.argmin(np.abs(fpos - self.fmax))

        # kwpos = np.linspace(0, np.max(kw), npoints)
        kwpos = np.linspace(0, 2 * np.max(kw), npoints)

        if self.kmax is None:
            self.kmax = np.max(kwpos[:npoints // 2])

        kmin = np.argmin(np.abs(kwpos - self.kmin))
        kmax = np.argmin(np.abs(kwpos - self.kmax))
        #kmax = np.max(kwpos[:npoints // 2])

        # tapering function
        taper_func = getattr(signal.windows, 'hann')
        taper_len = int(kwargs.pop('taper_length', 5) // df)
        taper_win = taper_func(2 * taper_len)

        FK_abs_filt = FK_abs.copy()

        terminate = False
        while terminate == False:

            fig, ax = plt.subplots(figsize=(6, 4))
            self._plotFK(FK_abs_filt[fmin:fmax, kmin:kmax], axes=ax)  # xlimit=np.max(kwpos[:npoints//2]))
            text = '\n'.join((
                r'$\bf{Keyboard \quad commands:}$',
                r'Press $\bf{e}$ to stop the process.',
                r'Press $\bf{t}$ for top or $\bf{b}$ for bottom filter.'))
            at = AnchoredText(text,
                              loc='lower right', prop=dict(size=6), frameon=True, bbox_to_anchor=(1.25, 1.05),
                              bbox_transform=ax.transAxes
                              )
            ax.add_artist(at)

            plot = FKFilterInteractive(ax)

            ax.set_title(f'Top filter active', fontweight='bold')
            plt.tight_layout()
            plt.show()

            terminate = plot.terminate
            key = plot.key

            if len(plot.points) > 0:

                x, y = zip(*sorted(plot.points.items()))
                points = []
                for i in range(len(x)):
                    points.append((x[i], y[i]))

                fp = np.array([np.round(points[i][1], 4) for i in range(len(points))])
                kp = np.array([np.round(points[i][0], 4) for i in range(len(points))])

                # write to file
                if (fname is not None):

                    path, _ = os.path.split(self.fname)
                    safe_makedirs(path)

                    if os.path.isfile(fname):
                        warnings.warn('File already exists. Fk filter will be appended.')

                    file = open(fname, "a+")
                    file.write(f'{self.pre}\t{key}\t{len(fp)}\n')
                    for i in range(len(fp)):
                        file.write(f'{kp[i]}\t{fp[i]}\n')

            # apply filter
            if not terminate:
                if len(points) > 0:

                    f = interpolate.interp1d(fp, kp, fill_value="extrapolate")
                    kpp = f(fpos)

                    if key == 't':
                        window = np.zeros_like(FK_abs_filt[0, :])
                        for j in range(len(fpos)):
                            k_min_tmp = np.argmin(abs(kwpos - kpp[j]))
                            window[k_min_tmp:] = 1
                            if k_min_tmp > taper_len - 1:
                                window[k_min_tmp - taper_len:k_min_tmp] = taper_win[:taper_len]
                            else:
                                window[:k_min_tmp] = taper_win[taper_len - k_min_tmp:taper_len]

                            FK_abs_filt[j, :] *= window
                            window *= 0

                    if key == 'b':
                        window = np.ones_like(FK_abs_filt[0, :])
                        for j in range(len(fpos)):
                            k_min_tmp = np.argmin(abs(kwpos - kpp[j]))
                            window[k_min_tmp:] = 0
                            if k_min_tmp < len(kwpos) - taper_len:
                                window[k_min_tmp:taper_len + k_min_tmp] = taper_win[taper_len:]
                            else:
                                window[k_min_tmp:] = taper_win[taper_len:taper_len + len(kwpos) - k_min_tmp]

                            FK_abs_filt[j, :] *= window
                            window = np.ones_like(FK_abs_filt[0, :])

        # back transformation
        FK_filt = FK_abs_filt * np.exp(1j * theta)
        FK_filt = np.fft.ifftshift(FK_filt, axes=1)
        FK_filt[:,:npoints // 2] = 0
        amps = self._fk_backtransform(FK_filt, iT, iX)
        self._amps2st(amps)

        if show:
            fig, ax = plt.subplots(1, 2, figsize=(8, 4))
            self._plotFK(FK_abs[fmin:fmax, kmin:kmax], axes=ax[0])
            self._plotFK(FK_abs_filt[fmin:fmax, kmin:kmax], axes=ax[1])
            ax[0].set_title('Raw data', fontweight='bold')
            ax[1].set_title('Post fk filter', fontweight='bold')
            plt.tight_layout()
            plt.show()

    def _fk_filter_from_file(self, fname=None, show=False, **kwargs):
        """apply the fk filter based on a file containing the bounds"""

        # transformation
        FK_abs, theta, kw, freq, iX, iT = self._fk_transform()

        npoints = FK_abs.shape[1]

        fpos = freq[:npoints // 2]
        df = fpos[1] - fpos[0]
        fmin = np.argmin(np.abs(fpos - self.fmin))
        fmax = np.argmin(np.abs(fpos - self.fmax))

        # kwpos = np.linspace(0, np.max(kw), npoints)
        kwpos = np.linspace(0, 2 * np.max(kw), npoints)
        #kmax = np.max(kwpos[:npoints // 2])

        if self.kmax is None:
            self.kmax = np.max(kwpos[:npoints // 2])

        kmin = np.argmin(np.abs(kwpos - self.kmin))
        kmax = np.argmin(np.abs(kwpos - self.kmax))

        # tapering function
        taper_func = getattr(signal.windows, 'hann')
        taper_len = int(kwargs.pop('taper_length', 5) // df)
        taper_win = taper_func(2 * taper_len)

        # plt.figure();plt.imshow(np.flipud(FK_abs),extent = (kw[0], 2*kw[255], freq[0], freq[255]), aspect='auto')

        FK_abs_filt = FK_abs.copy()

        # import previously created filter
        if fname is not None:
            if os.path.isfile(fname):
                points_dict = read_FKfilter(fname)

                for key, point_list in points_dict.items():

                    for points in point_list:
                        if len(points) > 0:

                            fp = points[:, 1]  # frequency
                            kp = points[:, 0]  # wavenumber

                            f = interpolate.interp1d(fp, kp, fill_value="extrapolate")
                            kpp = f(fpos)

                            if key == 't':
                                window = np.zeros_like(FK_abs_filt[0, :])
                                for j in range(len(fpos)):
                                    k_min_tmp = np.argmin(abs(kwpos - kpp[j]))
                                    window[k_min_tmp:] = 1
                                    if k_min_tmp > taper_len - 1:
                                        window[k_min_tmp - taper_len:k_min_tmp] = taper_win[:taper_len]
                                    else:
                                        window[:k_min_tmp] = taper_win[taper_len - k_min_tmp:taper_len]

                                    FK_abs_filt[j, :] *= window
                                    window *= 0

                            elif key == 'b':
                                window = np.ones_like(FK_abs_filt[0, :])
                                for j in range(len(fpos)):
                                    k_min_tmp = np.argmin(abs(kwpos - kpp[j]))
                                    window[k_min_tmp:] = 0
                                    if k_min_tmp < len(kwpos) - taper_len:
                                        window[k_min_tmp:taper_len + k_min_tmp] = taper_win[taper_len:]
                                    else:
                                        window[k_min_tmp:] = taper_win[taper_len:taper_len + len(kwpos) - k_min_tmp]

                                    FK_abs_filt[j, :] *= window
                                    window = np.ones_like(FK_abs_filt[0, :])
                            else:
                                raise ValueError('Incorrect key in file. '
                                                 'Use either "t" for top or "b" for bottom mute.')
            else:
                warnings.warn("Incorrect filename provided. No filtering applied.")
        else:
            warnings.warn("No file provided. No filtering applied.")

        # back transformation
        FK_filt = FK_abs_filt * np.exp(1j * theta)
        FK_filt = np.fft.ifftshift(FK_filt, axes=1)
        FK_filt[:,:npoints // 2] = 0
        amps = self._fk_backtransform(FK_filt, iT, iX)
        self._amps2st(amps)

        if show:
            fig, ax = plt.subplots(1, 2, figsize=(8, 4))
            self._plotFK(FK_abs[fmin:fmax, kmin:kmax], axes=ax[0])
            self._plotFK(FK_abs_filt[fmin:fmax, kmin:kmax], axes=ax[1])
            ax[0].set_title('Raw data', fontweight='bold')
            ax[1].set_title('Post fk filter', fontweight='bold')
            plt.tight_layout()
            plt.show()

    # def _fkdc(self):
    #     """Dispersion curve based on the FK tansformation"""
    #
    #     self.dispersive_energy = None
    #     self.velocity = None
    #     self.frequency = None
    #
    #     # transformation
    #     FK_abs, theta, kw, freq, iX, iT = self._fk_transform()
    #
    #     npoints = FK_abs.shape[1]
    #     fpos = freq[:npoints//2]
    #     kwpos = np.linspace(0,np.max(kw),npoints)
    #
    #     min_id = np.argmin(np.abs(freq - self.fmin))
    #     max_id = np.argmin(np.abs(freq - self.fmax))
    #     fids = np.arange(min_id, max_id + 1, step=self.fstep)
    #     freq = freq[fids]
    #     FK = FK_abs[min_id:max_id,:].T
    #
    #     self.frequency = freq
    #     self.dispersive_energy = V
    #     self.velocity = vels
    #     self.wavenumber = ks


    def _phaseshift(self):
        """Phase-shift transformation method after Park et al.(1998)."""

        self.dispersive_energy = None
        self.velocity = None
        self.frequency = None

        dt = self.dt
        receiver = self.receiver
        source = self.source

        # amplitude data & processing
        if not self.tapered:
            self._apply_taper()

        if self._pst is None:
            st = self._st.copy()
        else:
            st = self._pst.copy()

        amps = self._amps(st=st)

        if self.pad:
            amps,_,_ = self._zero_padding(amps)
        if self.norm_amps:
            amps = self._normalize_amps(amps)

        # sample size
        iX, iT = amps.shape

        # source-receiver offsets
        offsets = self._aoffsets(receiver, source)
        if source > receiver[-1]:
            offsets = np.flipud(offsets)
            amps = np.flipud(amps)

        # frequency range
        omega_fs = 2 * np.pi * 1/dt
        omega = np.arange(iT) * (omega_fs/iT)
        freq = omega/(2*np.pi)

        min_id = np.argmin(np.abs(freq - self.fmin))
        max_id = np.argmin(np.abs(freq - self.fmax))
        fids = np.arange(min_id, max_id + 1, step=self.fstep)
        freq = freq[fids]

        # testing phase velocities
        vels = np.arange(self.vmin, self.vmax, self.vstep)

        # transformation to U(x,w) domain
        u = np.fft.fft(amps)

        # transformation to V(f,v) domain
        ks = np.zeros_like(vels)
        V = np.zeros((len(vels), len(freq))).astype(complex)
        for j, (f_index, f) in enumerate(zip(fids, freq)):
            for i, vel in enumerate(vels):
                ktrial = wavenumber(f, vel)
                kx = ktrial*offsets
                steer = self._steering_vector(kx,steering = 'none', sign=1)
                V[i, j] = np.abs(np.sum(steer * u[:, f_index]/np.abs(u[:, f_index])))
                ks[j] = ktrial

        V = V / len(offsets)  # normalization by trace number (suggested by Olafsdottir,2018)

        self.frequency = freq
        self.dispersive_energy = V
        self.velocity = vels
        self.wavenumber = ks

    def _rfest(self, u, iX):
        """spatiospectral correlation matrix (Zywicki, 1999)"""

        _, iF, nblocks = u.shape

        # weighting matrix
        weights = 1 / np.abs(np.mean(u, axis=-1))
        for i in range(iF):
            wi = weights[:, i]
            for b in range(nblocks):
                u[:, i, b] *= wi

        # Calculate spatiospectral correlation matrix
        R = np.empty((iX, iX, iF)).astype(complex)
        Rsum = np.zeros((iX, iX)).astype(complex)
        tslice_n = np.zeros((iX, 1)).astype(complex)
        tslice_h = np.transpose(np.conjugate(tslice_n))
        for i in range(iF):
            Rsum[:, :] = 0
            for j in range(nblocks):
                tslice_n[:, 0] = u[:, i, j]
                tslice_h[0, :] = np.conjugate(tslice_n)[:, 0]
                Rsum += np.dot(tslice_n, tslice_h)
            Rsum /= nblocks
            R[:, :, i] = Rsum[:]

        return R

    def _fdbf(self, steering = 'cylindrical'):
        """frequency-domain beamforming (Zywicki, 1999)"""

        self.dispersive_energy = None
        self.velocity = None
        self.frequency = None

        dt = self.dt
        receiver = self.receiver
        source = self.source

        # receiver-source offsets; time series matrix
        offsets = self._aoffsets(receiver, source)

        # amplitude data & processing
        if not self.tapered:
            self._apply_taper()

        if self._pst is None:
            st = self._st.copy()
        else:
            st = self._pst.copy()

        amps = self._amps(st=st)

        if self.pad:
            amps,_,_ = self._zero_padding(amps)
        if self.norm_amps:
            amps = self._normalize_amps(amps)

        # sample size
        iX, iT = amps.shape

        if source > receiver[-1]:
            offsets = np.flipud(offsets)
            amps = np.flipud(amps)

        # frequency range
        omega_fs = 2 * np.pi * 1/dt
        omega = np.arange(iT) * (omega_fs/iT)
        freq = omega/(2*np.pi)

        min_id = np.argmin(np.abs(freq - self.fmin))
        max_id = np.argmin(np.abs(freq - self.fmax))
        fids = np.arange(min_id, max_id + 1, step=self.fstep)
        freq = freq[fids]

        # testing phase velocity
        vels = np.arange(self.vmin, self.vmax, self.vstep)

        # transformation to U(x,w) domain
        amps = amps.reshape(iX, iT, 1)
        u = np.fft.fft(amps, axis=1)

        # Calculate the spatiospectral correlation matrix
        sscm = self._rfest(u, iX)
        sscm = sscm[:,:,fids]

        # weighting
        offsets_n = offsets.reshape(iX, 1)
        offsets_h = np.transpose(np.conjugate(offsets_n))
        w = np.dot(offsets_n, offsets_h)

        ks = np.zeros_like(vels)
        V = np.zeros((len(vels), len(freq))).astype(complex)
        steer = np.zeros((iX, 1)).astype(complex)
        kx = np.zeros_like(offsets)
        for i, f in enumerate(freq):
            romega = sscm[:, :, i]*w
            for j, vel in enumerate(vels):
                ktrial = wavenumber(f,vel)
                kx[:] = ktrial*offsets[:]
                steer[:,0] = self._steering_vector(kx,steering)
                _V = np.dot(np.dot(np.transpose(np.conjugate(steer)),romega), steer)
                V[j, i] = _V
                ks[j] = ktrial

        V = V / len(offsets)  # normalization by trace number (suggested by Olafsdottir,2018)

        self.frequency = freq
        self.dispersive_energy = V
        self.velocity = vels
        self.wavenumber = ks

    def _MOPA(self, weighted = False, rel_err = 5/100, abs_err = None,
              stopAtChi2=2,outfile = None, **kwargs):
        """Multi-offset phase analysis (MOPA; Strobbia and Foti, 2014)"""

        dt = self.dt
        receiver = self.receiver
        source = self.source

        # receiver-source offsets and amplitudes
        offsets = self._aoffsets(receiver,source)
        min_nrec = kwargs.pop('min_nrec',12)

        if not self.tapered:
            self._apply_taper()

        if self._pst is None:
            st = self._st.copy()
        else:
            st = self._pst.copy()

        amps = self._amps(st=st)

        if self.pad:
            amps,_,_ = self._zero_padding(amps)

        if source > receiver[-1]:
            offsets = np.flipud(offsets)
            amps = np.flipud(amps)

        iX, iT = amps.shape

        # frequency range
        omega_fs = 2 * np.pi * 1/dt
        omega = np.arange(iT) * (omega_fs/iT)
        freq = omega/(2*np.pi)

        min_id = np.argmin(np.abs(freq - self.fmin))
        max_id = np.argmin(np.abs(freq - self.fmax))
        fids = np.arange(min_id, max_id + 1, step=self.fstep)
        freq = freq[fids]

        # fft
        u = np.fft.fft(amps)

        results_dict_plotting = {}

        freqs = []
        vel0s = []
        chi2s = []

        # MOPA
        for j,f_index in enumerate(fids):

            chi2 = np.inf
            offsets_index = 0

            # check the convergence and remove near offset geophones if chi^2 is too high
            while (chi2 >= stopAtChi2) & (len(offsets[offsets_index:]) >= min_nrec):

                offsets_inv = offsets[offsets_index:]
                mag = np.abs(u[offsets_index:, f_index])
                phase = np.angle(u[offsets_index:, f_index])
                phi = np.unwrap(phase, axis=0)

                # weights
                weights = np.ones_like(phi)
                if weighted:
                    if abs_err is None:
                        error = rel_err*phi
                    else:
                        error = abs_err

                    var = np.var(error)
                    weights *= 1/var

                # linear LSQR to find k and phi0 of phi = -k*offset+phi0
                k0, phi0 = linear_LSQR(offsets_inv, phi, weights)

                # response and fit
                phi_resp = phase_response(offsets_inv, k0, phi0)
                rrms,chi2 = compute_chi2(phi, phi_resp, rel_err*phi)

                offsets_index += 1

            # final inversion results
            results_dict_plotting[j] = {'offsets': offsets_inv,
                                        'mag': mag,
                                        'phase': phase,
                                        'k0': k0,
                                        'phi0': phi0}

            freqs.append(freq[j])  # frequencies
            vel0s.append(2 * np.pi * freq[j] / k0)  # phase velocities
            chi2s.append(chi2)

        if len(vel0s) > 0:

            # %% plot MOPA results
            if kwargs.setdefault('showMOPAResults',False):

                # %% dispersion curve obtained in classical sense as comparison
                self._fdbf()
                self._dcpicking(pck_mode='auto')
                f_fdbf = self._picks['auto'][0]['f']
                v_fdbf = self._picks['auto'][0]['v']

                fig, ax = plt.subplots(3, 1, figsize=(8, 6), constrained_layout=True)
                color = plt.cm.viridis(np.linspace(0, 0.9, len(np.arange(len(freqs)))))

                for ii in np.arange(len(freqs)):

                    # amplitude
                    ax[0].scatter(results_dict_plotting[ii]['offsets'], results_dict_plotting[ii]['mag'],
                                  marker="o", s=15, c=color[ii].reshape(1,-1), edgecolor='k',
                                  linewidth=0)

                    # fitted lines
                    ax[1].plot(results_dict_plotting[ii]['offsets'],
                               phase_response(results_dict_plotting[ii]['offsets'],
                                              results_dict_plotting[ii]['k0'],
                                              results_dict_plotting[ii]['phi0']),
                               color = color[ii].reshape(1,-1),
                               alpha = 0.75,linewidth = 0.8,linestyle='dashed')

                    # phase data
                    ax[1].scatter(results_dict_plotting[ii]['offsets'],
                                  np.unwrap(results_dict_plotting[ii]['phase'], axis=0),
                                  marker="o", s=15, c=color[ii].reshape(1,-1),
                                  edgecolor='k',
                                  linewidth=0, zorder=2)

                    # dispersion curve from MOPA
                    if chi2s[ii] > stopAtChi2:
                        ec = 'r'
                        label = f'MOPA - chi^2 > {stopAtChi2}'
                    else:
                        ec = 'k'
                        label = f'MOPA - chi^2 <= {stopAtChi2}'

                    ax[2].scatter(freqs[ii], vel0s[ii], marker="o", s=25, c=color[-1].reshape(1, -1),
                                  edgecolor=ec, linewidth=0.8, zorder=2,
                                  label=label, alpha=0.7)

                # dispersion curve from FDBF
                ax[2].scatter(f_fdbf, v_fdbf, marker="s", s=25, c=color[0].reshape(1,-1),
                              edgecolor='k', linewidth=0.8, zorder=-2, label = 'FDBF')

                for axi in ax.flat:
                    axi.grid(True, linestyle=':')
                ax[0].set_xlabel("offset (m)")
                ax[1].set_xlabel("offset (m)")
                ax[0].set_ylabel(f"amplitude")
                ax[1].set_ylabel(f"phase (rad)")
                plot_colorBar(ax[0], self.fmin, self.fmax, label='f (Hz)', orientation='vertical')
                plot_colorBar(ax[1], self.fmin, self.fmax, label='f (Hz)', orientation='vertical')
                handles, labels = plt.gca().get_legend_handles_labels()
                by_label = OrderedDict(zip(labels, handles))
                ax[2].legend(by_label.values(), by_label.keys(),loc='upper right',
                             frameon=True, title='Transformation')
                ax[2].set_ylabel(f"phase velocity (m/s)")
                ax[2].set_xlabel(f"frequency (Hz)")
                ax[2].set_ylim([self.vmin,self.vmax])
                ax[2].set_xlim([self.fmin, self.fmax])
                ax[0].set_title('MOPA - Shotfile: ' + self.pre, fontweight='bold')
                fig.align_ylabels(ax)

            if outfile:
                fig.savefig(outfile)
                plt.close()
            else:
                plt.show()

            # dispersion curve
            self._pick = True
            self._picks[self._pck_mode] = {0: {'f': np.array(freqs),
                                               'v': np.array(vel0s),
                                               'chi2': np.array(chi2s)}}
        else:
            warnings.warn('No dispersion curve extracted.')


    def _compute_phasediffs(self):
        """compute phase differences between adjacent receivers for one shot file"""

        receiver = self.receiver
        source = self.source

        if not self.tapered:
            self._apply_taper()

        if self._pst is None:
            st = self._st.copy()
        else:
            st = self._pst.copy()

        amps = self._amps(st=st)

        if self.pad:
            amps,_,_ = self._zero_padding(amps)

        if source > receiver[-1]:
            amps = np.flipud(amps)

        # frequency range
        fids = self._argfreq()

        # fft
        u = np.fft.fft(amps)

        # extract phase & compute phase differences
        phase_diff = np.zeros((len(fids),len(receiver)-1))
        for j, f_index in enumerate(fids):

            phase = np.angle(u[:, f_index])
            phase_unwrapped = np.unwrap(phase, axis=0)
            if source > receiver[-1]:
                phase_unwrapped = np.flipud(phase_unwrapped)
            di = np.diff(phase_unwrapped)  # phase difference between adjacent geophones

            phase_diff[j,:] = di

        return phase_diff, fids

    def _norm_power(self,power):
        """normalize amplitudes"""

        # norm = np.max(np.abs(power))
        # power = np.abs(power) / norm

        norm_power = np.zeros_like(power)
        global_max = np.max(np.abs(power))

        for i in range(norm_power.shape[1]):
            pow = power[:,i]
            if self.use_local_max_power:
                local_max = np.max(np.abs(pow))
                if local_max != 0:
                    pow = pow / np.max(np.abs(pow))
            else:
                pow = pow/global_max
            norm_power[:,i] = pow

        return norm_power

    def _dcpicking(self, pck_mode = 'auto', axes=None,**kwargs):
        """automatic or interactive dispersion curve picking"""

        self._peaks_idx = {}
        self._disp_curves_idx = {}

        receiver = self.receiver
        source = self.source
        offsets = self._aoffsets(receiver,source)

        if pck_mode == 'auto':
            # locate amplitude maxima at each frequency, i.e. apparent dispersion curve
            peaks_idx = np.argmax(self.dispersive_energy, axis=0)

            freq_pick = self.frequency
            vel_pick = self.velocity[peaks_idx]

            self._picks[pck_mode] = {0:{'f': freq_pick, 'v': vel_pick}}

        elif pck_mode == 'manual':
            # interactive dispersion curve picking by selection of boundary boxes
            if axes is None:
                fig = plt.figure(figsize=(16, 9), constrained_layout=True)
                gs = fig.add_gridspec(5, 2)
                ax0 = fig.add_subplot(gs[0, 0:2])
                ax1 = fig.add_subplot(gs[1:5, 0:2])
            else:
                ax0 = axes[0]
                ax1 = axes[1]

            if 'title' in kwargs:
                title = kwargs.pop('title', None)
                ax0.set_title(self.pre.replace('_',' ') + f" - xmid = {title} m", fontweight='bold')
            else:
                ax0.set_title(self.pre.replace('_', ' '), fontweight='bold')
            self._plotGeometry(axes = ax0)

            # plot dispersion image
            text = '\n'.join((
                r'$\bf{Keyboard \quad commands:}$',
                r'Press $\bf{e}$ to stop the process.',
                r'Press any number to set dc index.',
                r'Press $\bf{d}$ to delete boundary.',
                r'Press $\bf{p}$ to pick a dc.',
                r'Press $\bf{r}$ to reset picks.',
                r'Scroll $\bf{up}$ to tighten and $\bf{down}$ to loosen boundary.'))
            at = AnchoredText(text,
                               loc='lower right', prop=dict(size=6), frameon=True,bbox_to_anchor=(1., 1.),
                       bbox_transform=ax1.transAxes)
            ax1.add_artist(at)
            self._plotDispersionImage(axes=ax1)

            ax1.set_title(f"Dispersion curve picking", fontweight="bold")

            # show picked dc curves for same xmid location
            if 'dc_prior' in kwargs:
                dc_fnames = kwargs['dc_prior']
                for i in range(len(dc_fnames)):
                    curve = Curve()
                    curve._read(dc_fnames[i])
                    curve._plotdata(axes=ax1,
                                      color='r',
                                      alpha = 0.1,
                                      size = 10,
                                      axis_style = False,
                                      marker = '.',
                                      show_orig=False)

            # pick polygons
            dcpicker = DCPickingInteractive(ax1,self.frequency, self.velocity,
                                            self.dispersive_energy, offsets = offsets)
            plt.show()

            # retrieve picks
            picks = dcpicker.picks

            if len(picks) != 0:
                self._picks[pck_mode] = picks
                self._pick = True

            else:
                self._pick = False

        else:
            raise ValueError(f'Picking mode not recognized. Use one of the keys: {["auto","manual"]} \n '
                             f'for automatic or manual dispersion curve picking, respectively.')


    def _windowing(self,path2disp, win_len, minoffset,maxoffset,win_move,ext = 'csv',**kwargs):
        """
        run a moving window over stream data

        @param path2disp: str, storage location
        @param win_len: int, window length
        @param minoffset: float, min accepted offset
        @param maxoffset: float, max accepted offset
        @param win_move: int, increment with which the window is moved
        @param ext: str, file format in which the dispersion curve should be saved
        """

        # default settings for optional FK filter
        fk_filter = kwargs.pop('fk_filter',False)
        path2fk = kwargs.pop('path2fk',None)

        # default settings for optional visualizations
        show_previousDC = kwargs.pop('show_previousDC',False)
        show_FK = kwargs.pop('show_FK',False)
        show_SFR = kwargs.pop('show_SFR',False)
        show_seismogram = kwargs.pop('show_seismogram',False)
        show_spectrogram = kwargs.pop('show_spectrogram', False)

        # default settings for the wavefield transformation and picking
        do_pick = kwargs.pop('do_pick', True)
        apply_trafo = kwargs.pop('apply_trafo',True)

        if self.trafo_type.lower() == 'mopa':
            do_pick = False

        all_receiver = self.receiver
        source = self.source

        streams_dict = {}

        mintrace = 0
        maxtrace = win_len
        win_id = 0

        while maxtrace <= len(all_receiver):

            trace_select = range(mintrace, maxtrace)
            temp_stream = copy.deepcopy(self)
            temp_stream._select_traces(trace_select=trace_select)

            receiver = temp_stream.receiver
            offsets = temp_stream._aoffsets(receiver, source)

            mintrace += win_move
            maxtrace += win_move

            shot_condition = ((np.min(offsets) <= maxoffset) &
                              (np.min(offsets) >= minoffset) &
                              (np.min(receiver) > source)) | \
                             ((np.max(receiver) < source) &
                              (np.min(offsets) >= minoffset) &
                              (np.min(offsets) <= maxoffset))

            if shot_condition:

                # storage location
                xmid = round(temp_stream.midpoint, 2)
                prjdir = os.path.join(path2disp, str(xmid))

                use_loc = True

                # optionally: use only xmids provided in list
                if 'xmids' in kwargs:
                    if xmid not in kwargs['xmids']:
                        use_loc = False

                if use_loc:
                    # optionally: load dc files with same xmid that were previously generated
                    fnames = []
                    if show_previousDC:
                        path2csv = os.path.join(prjdir, "0_csv")
                        if os.path.isdir(path2csv):
                            for fname in os.listdir(path2csv):
                                fnames.append(os.path.join(path2csv, fname))
                            fnames = natural_sort(fnames)

                    # optionally: create some figures
                    if show_seismogram:
                        temp_stream._plotSeismogram(show = True,**kwargs)

                    if show_spectrogram:
                        temp_stream._plotSpectrogramComposite(show = True)

                    if show_SFR:
                        temp_stream._plotSFR(show=True, amp_scale = 0.02, color = 'k')

                    # # apply wavefield transformation
                    # if self.trafo_type.lower() != 'mopa':
                    #     if apply_trafo:
                    #         temp_stream._apply_trafo(do_pick=do_pick,
                    #                                  save_dc = False,
                    #                                  #pck_mode=self._pck_mode,
                    #                                  dc_prior = fnames,
                    #                                  title = xmid,
                    #                                  **kwargs)
                    #
                    # if len(temp_stream._picks) == 0:

                    if fk_filter:
                        if path2fk is not None:
                            fid = os.path.join(path2fk,f'win{win_id}')
                            if os.path.isfile(fid):
                                temp_stream._fk_filter_from_file(fname=fid, show=show_FK)
                            else:
                                temp_stream._fk_filter_from_pick(fname=fid, show=False)

                    if apply_trafo:
                        temp_stream._apply_trafo(do_pick=do_pick,
                                                 save_dc = False,
                                                 dc_prior = fnames,
                                                 title = xmid,
                                                 **kwargs)

                    streams_dict[str(xmid)] = temp_stream

                    # create and save the dispersion curve
                    if len(temp_stream._picks) > 0:

                        safe_makedirs(prjdir)
                        fname = (self.pre +
                                 f'_ch{len(temp_stream._pst)}_'
                                 f'dx{str(self.dx).replace(".","")}_'
                                 f'{self.trafo_type}')

                        curve = Curve()
                        curve._init_data(freq=temp_stream._picks[self._pck_mode][0]['f'],
                                        vel=temp_stream._picks[self._pck_mode][0]['v'])

                        curve._save(prjdir,fname,ext)

                    win_id += 1

        return streams_dict

    def _curve(self, id = 0):
        """set the dispersion curve"""

        if len(self._picks) > 0:
            if id in self._picks[self._pck_mode]:
                self.curve = Curve()
                self.curve._init_data(freq=self._picks[self._pck_mode][id]['f'],
                                      vel=self._picks[self._pck_mode][id]['v'])
            else:
                raise ValueError(f'Mode id {id} does not exist yet.')
        else:
            raise ValueError('No pick set has been created so far.')


    def _save_dc(self,path2disp, fname = None, id = 0, ext = 'csv',**kwargs):
        """
        save picked dispersion curve to file

        @param path2disp: str, storage location
        @param fname: str, file name
        @param id: int, mode id
        @param ext: str, file format in which the dispersion curve should be saved
        """

        xmid = self.midpoint

        prjdir = os.path.join(path2disp, str(xmid))
        safe_makedirs(prjdir)

        if fname is None:
            fname = f'{self.pre}_ch{len(self._pst)}_{self.trafo_type}'

        if self.curve is not None:
            self.curve._save(prjdir,fname, ext)

        else:
            if len(self._picks) > 0:
                if id in self._picks[self._pck_mode]:
                    curve = Curve()
                    curve._init_data(freq=self._picks[self._pck_mode][0]['f'],
                                    vel=self._picks[self._pck_mode][0]['v'])
                    curve._save(prjdir, fname, ext)
                else:
                    warnings.warn(f'Mode id {id} does not exist yet. No data has been saved.')
            else:
                warnings.warn('No pick set has been created so far. No data has been saved.')

    # %% PLOTTING
    def _plotGeometry(self,axes=None, outfile=None,
                        fmt=None, show=True):
        """plot acquisition setup of shot file"""

        if axes is None:
            fig, ax = plt.subplots(figsize=(6, 2))
        else:
            ax = axes

        all_receiver = self._receiver(self._st)

        ax.scatter(all_receiver, np.zeros(len(all_receiver)), marker='v', c='k',label='active channels',alpha = 0.7)
        ax.scatter(self.receiver, np.zeros(len(self.receiver)), marker='v', c='lightgrey',
                    label='selected channels')
        ax.scatter(self.source, 0.2, marker='*', s= 60,c='limegreen', label='shot location')
        ax.legend(loc='upper right', ncol=1, frameon=True,
                  edgecolor = 'k',fontsize = 6,bbox_to_anchor=(1, 1.5)).get_frame().set_boxstyle('Square', pad=0.2)

        # Use the min and max source position instead
        ax.set_xlim([np.min(all_receiver) - 5,
                      np.max(all_receiver) + 5])
        ax.set_ylim([-0.5, 0.5])
        ax.set_xlabel('x (m)')
        ax.get_yaxis().set_ticks([])
        ax.grid(axis='x', which='both', linestyle=":")
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_linewidth(1)

        if axes is not None:
            return ax

        if outfile:
            if fmt:
                fig.savefig(outfile, format=fmt)
            else:
                fig.savefig(outfile)
        elif show:
            plt.show()
        else:
            return fig

    def _plotSeismogram(self, axes=None, st = None, amp_scale=None, trace_select=None,
                        cut_times=None, offset_limits=None, outfile=None,
                        fmt=None, show=True, **kwargs):
        """plot seismogramm of a single shot file"""

        if st is None:
            if self._pst is None:
                st = self._st.copy()
            else:
                st = self._pst.copy()

        color = kwargs.pop('color', 'dimgrey')
        linewidth = kwargs.pop('linewidth', 0.5)
        title = kwargs.pop('title', self.pre)
        step = kwargs.pop('tick_scale', 10)
        alpha = kwargs.pop('alpha',0.5)

        if axes is None:
            fig, ax = plt.subplots(figsize=(8,6))
        else:
            ax = axes

        amps = self._amps(st=st)
        amps = self._detrend_signal(amps)
        if self.norm_amps:
           amps = self._normalize_amps(amps)

        nchannels, npts = amps.shape

        t = np.arange(npts) * self.dt

        if amp_scale is None:
            amp_scale = np.mean(np.diff(np.array(self.receiver))) / 2

        for i, pos in enumerate(self.receiver):
            amps[i] = amps[i] * amp_scale

        if kwargs.setdefault('show_map', 'True'):
            ax.imshow(amps.T,
                     extent=[-1,(len(amps)-1)+1,t[-1],t[0]],
                     cmap='bwr',
                     aspect='auto',
                     vmin=-1, vmax=1,
                     interpolation='bicubic')

        for i, trace in enumerate(amps):
            if ((i+1) % 5 == 0) & ((i+1) % 10 != 0):
                ax.plot(trace+i, t, color=color, linewidth=linewidth+0.5,alpha = alpha)
            elif (i+1) % 10 == 0:
                ax.plot(trace+i, t, color=color, linewidth=linewidth+1,alpha = alpha)
            else:
                ax.plot(trace + i, t, color=color, linewidth=linewidth, alpha=alpha)

        if title is not None:
            title = title.replace('_',' ')
            ax.set_title(title, fontweight='bold')
        ax.set_ylabel("time (s)")

        ax.set_xlim(-2,(len(amps)-1)+2)

        if kwargs.pop('show_xticks',True):
            ax.xaxis.tick_top()
            offsets = self.receiver
            xticks = np.arange(len(offsets))[step-1::step]
            ax.set_xticks(np.arange(len(offsets))[step-1::step])
            xticklabels = []
            for i in xticks:
                xticklabels.append(f'{st[i].stats.channel}\n{offsets[i]}')
            ax.set_xticklabels(xticklabels)

            text = 'channel nr.:\ndistance (m):'
            at = AnchoredText(text,
                              loc='lower left',
                              prop=dict(ha='right'),
                              bbox_to_anchor=(-0.15, 1.0),
                              pad=0, borderpad=0.8, frameon=False,
                              bbox_transform=ax.transAxes)
            ax.add_artist(at)

        ymin = kwargs.pop('ymin', np.min(t))
        ymax = kwargs.pop('ymax', np.max(t))
        ax.set_ylim([ymin, ymax])

        ax.grid(axis='y', linestyle=":")
        ax.invert_yaxis()

        if trace_select is not None:
            ax.add_patch(Rectangle((trace_select[0] - 0.5, np.min(t)),
                                   np.abs(trace_select[-1] - trace_select[0]) + 1,
                                   np.max(t), facecolor='lightgray', alpha=0.75,
                                   zorder=-2, label='Trace-based selection'))
            ax.legend(loc='lower left')

        if cut_times is not None:
            tmin, tmax = cut_times
            xlim = ax.get_xlim()

            ax.add_patch(Rectangle((xlim[0], np.max(t) - tmax), np.abs(xlim[0] - xlim[1]),
                                   -(np.max(t) - tmax),
                                   facecolor='lightgray', alpha=0.75,
                                   zorder=-2, label='Time-based selection'))
            ax.legend(loc='lower left')

        if offset_limits is not None:
            min_offset, max_offset = offset_limits
            _, offset_ids = self._range(offsets, min_offset, max_offset, step=1)
            ax.add_patch(Rectangle((offset_ids[0], np.min(t)),
                                   offset_ids[1] + 1, np.max(t),
                                   facecolor='lightgray', alpha=0.75,
                                   zorder=-2, label='Offset-based selection'))
            ax.legend(loc='lower left')

        if axes is not None:
            return ax
        else:
            plt.tight_layout()

        if outfile:
            if fmt:
                fig.savefig(outfile, format=fmt)
            else:
                fig.savefig(outfile)
        elif show:
            plt.show()
        else:
            return fig

    def _plotSpectrogram(self, axes=None, outfile=None, fmt=None, show=False, **kwargs):
        """plot spectrogram"""

        if self._pst is None:
            st = self._st.copy()
        else:
            st = self._pst.copy()

        dt = self.dt
        npts = self.npts
        receiver = self.receiver
        source = self.source

        scale = kwargs.pop('scale', 5)

        # receiver-source offsets; time series matrix
        offsets = self._aoffsets(receiver, source)

        amps = self._amps(st=st)
        # if kwargs.pop("detrend", True):
        #     amps = self._detrend_signal(amps)
        # if kwargs.pop("norm", True):
        #     amps = self._normalize_amps(amps)

        if source > receiver[-1]:
            offsets = offsets[::-1]
            amps = np.flipud(amps)
        offsets = np.array(offsets)

        # frequency range
        omega_fs = 2 * np.pi * 1 / dt
        omega = np.arange(npts) * (omega_fs / npts)
        freq = omega / (2 * np.pi)

        min_id = np.argmin(np.abs(freq - self.fmin))
        max_id = np.argmin(np.abs(freq - self.fmax))
        fids = np.arange(min_id, max_id + 1, step=self.fstep)
        freq = freq[fids]

        # fft
        u = np.fft.fft(amps)/amps.shape[1]
        df = (1/self.df)/amps.shape[1]

        # absolute amplitudes in db
        abs_amps = np.empty((len(freq), len(receiver)))
        for row in range(len(receiver)):
            ui = np.abs(u[row, fids])
            abs_amps[:, row] = ui

        # db
        abs_amps = 10 * np.log10(abs_amps)

        abs_amps_min = round(np.percentile(abs_amps,5))
        abs_amps_max = round(np.percentile(abs_amps, 95))

        if axes is None:
            fig, ax = plt.subplots(figsize=(3, 4))
        else:
            ax = axes

        title = kwargs.pop('title', None)

        img = ax.contourf(np.arange(len(offsets)),
                        freq,
                        abs_amps,
                        np.linspace(abs_amps_min, abs_amps_max, 21),
                        #extend='both',
                        cmap=plt.cm.get_cmap(kwargs.pop('cmap', 'viridis')))

        ax.set_xlim(-2, (len(self.receiver) - 1) + 2)

        if kwargs.pop('show_xticks',True):
            ax.xaxis.tick_top()
            offsets = self.receiver
            step = int(len(offsets) / scale)
            xticks = np.arange(len(offsets))[step::step]
            ax.set_xticks(np.arange(len(offsets))[step::step])
            xticklabels = []
            for i in xticks:
                xticklabels.append(f'{st[i].stats.channel}\n{offsets[i]}')
            ax.set_xticklabels(xticklabels)

            text = 'channel nr.:\ndistance (m):'
            at = AnchoredText(text,
                              loc='lower left',
                              prop=dict(ha='right'),
                              bbox_to_anchor=(-0.15, 1.0),
                              pad=0, borderpad=0.8, frameon=False,
                              bbox_transform=ax.transAxes)
            ax.add_artist(at)

        plt.colorbar(img, label='amplitude (db)', ax=ax)
        ax.set_ylabel('frequency (Hz)')
        ax.set_ylim([1, 100])
        ax.grid(True, linestyle=':')

        if title is not None:
            fig.suptitle(self.pre)

        if axes is not None:
            return ax
        else:
            plt.tight_layout()

        if outfile:
            if fmt:
                fig.savefig(outfile, format=fmt)
                plt.close()
            else:
                fig.savefig(outfile)
                plt.close()
        elif show:
            plt.show()
        else:
            return fig

    def _plotSpectra(self, axes=None, outfile=None, fmt=None, show=False, **kwargs):
        """plot spectra"""

        if self._pst is None:
            st = self._st.copy()
        else:
            st = self._pst.copy()

        dt = self.dt
        npts = self.npts
        receiver = self.receiver
        source = self.source

        amps = self._amps(st=st)
        # if kwargs.pop("detrend", True):
        #     amps = self._detrend_signal(amps)
        if self.norm_amps:
            amps = self._normalize_amps(amps)

        if source > receiver[-1]:
            amps = np.flipud(amps)

        # frequency range
        omega_fs = 2 * np.pi * 1 / dt
        omega = np.arange(npts) * (omega_fs / npts)
        freq = omega / (2 * np.pi)

        min_id = np.argmin(np.abs(freq - self.fmin))
        max_id = np.argmin(np.abs(freq - self.fmax))
        fids = np.arange(min_id, max_id + 1, step=self.fstep)
        freq = freq[fids]

        if axes is None:
            fig, ax = plt.subplots(figsize=(3, 4))
        else:
            ax = axes

        # fft
        u = np.fft.fft(amps)/amps.shape[1]
        df = (1/self.df)/amps.shape[1]

        # compute absolute normalized psd
        norm_amps = np.zeros((len(freq), len(receiver)))
        for row in range(len(receiver)):
            ui = np.abs(u[row, fids])
            norm_amps[:, row] =ui

        color = plt.cm.viridis(np.linspace(0, 1, len(receiver)))
        for row in range(len(receiver)):
            ax.plot(norm_amps[:, row], freq, color=color[row],**kwargs)
        ax.xaxis.tick_top()
        ax.set_xlabel('normalized amplitudes')
        ax.xaxis.set_label_position('top')
        ax.grid(True, linestyle=':')
        ax.set_ylabel('frequency (Hz)')
        ax.set_ylim([1, 100])
        #ax.set_xlim([1, 0])

        for axis in ['top', 'bottom', 'left', 'right']:
            ax.spines[axis].set_linewidth(1)

        import matplotlib as mpl
        cmap = mpl.colors.LinearSegmentedColormap.from_list(
            'Custom cmap', color, len(color))
        norm = plt.Normalize(st[0].stats.channel, st[-1].stats.channel)
        smap = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        cbar = plt.colorbar(smap, ax=ax)
        cbar.set_label('Channel Nr.')

        if axes is not None:
            return ax
        else:
            plt.tight_layout()

        if outfile:
            if fmt:
                fig.savefig(outfile, format=fmt)
                plt.close()
            else:
                fig.savefig(outfile)
                plt.close()
        elif show:
            plt.show()
        else:
            return fig

    def _plotSpectrogramComposite(self, axes=None, outfile=None, fmt=None, show=False, **kwargs):
        """plot seismogram, spectrogram and spectra"""

        if axes is None:
            fig, ax = plt.subplots(1, 3, figsize=(12, 4))
        else:
            ax = axes

        self._plotSeismogram(axes=ax[0], title=None,**kwargs)
        self._plotSpectrogram(axes=ax[1],**kwargs)
        self._plotSpectra(axes=ax[2],**kwargs)

        if axes is not None:
            return axes
        else:
            plt.tight_layout()

        if outfile:
            if fmt:
                fig.savefig(outfile, format=fmt)
                plt.close()
            else:
                fig.savefig(outfile)
                plt.close()
        elif show:
            plt.show()
        else:
            return fig

    def _plotFK(self,FK_data=None,axes= None, outfile=None, fmt=None, show=True,
                             **kwargs):
        """plot FK image"""

        if axes is None:
            fig,ax = plt.subplots(figsize=(6, 4), constrained_layout=True)
        else:
            ax = axes

        # transformation
        if FK_data is None:
            FK_data, theta, kw, freq, iX, iT = self._fk_transform()
            npoints = FK_data.shape[1]
            kwpos = np.linspace(0, 2 * np.max(kw), npoints)

            fpos = freq[:npoints // 2]
            fmin = np.argmin(np.abs(fpos - self.fmin))
            fmax = np.argmin(np.abs(fpos - self.fmax))

            if self.kmax is None:
                self.kmax = np.max(kwpos[:npoints // 2])

            kmin = np.argmin(np.abs(kwpos - self.kmin))
            kmax = np.argmin(np.abs(kwpos - self.kmax))

            FK_data = FK_data[fmin:fmax,kmin:kmax]

        # Normalization
        if self.norm_power:
            FK_data = self._norm_power(FK_data)
            label = "amplitudes (normalized)"
        else:
            label = "amplitudes"

        img = ax.imshow(abs(FK_data), aspect='auto', origin='lower',
                           extent=[self.kmin, self.kmax, self.fmin, self.fmax])
        ax.set_ylabel('frequency (Hz)')
        ax.set_xlabel('wavenumber (rad/m)')
        ax.grid(linestyle=':')

        for axis in ['top', 'bottom', 'left', 'right']:
            ax.spines[axis].set_linewidth(1)

        plt.colorbar(img, label=label, ax=ax)

        if axes is not None:
            return ax

        if outfile:
            if fmt:
                fig.savefig(outfile, format=fmt)
            else:
                fig.savefig(outfile)
        elif show:
            plt.show()
        else:
            return fig


    def _plotSFR(self, axes=None, st = None, amp_scale=None, outfile=None,
                        fmt=None, show=True, **kwargs):
        """plot swept-frequency record (SFR)"""

        if st is None:
            if self._pst is None:
                st = self._st.copy()
            else:
                st = self._pst.copy()

        color = kwargs.pop('color', 'dimgrey')
        linewidth = kwargs.pop('linewidth', 0.5)
        scale = kwargs.pop('scale', 1)
        alpha = kwargs.pop('alpha',0.5)

        if axes is None:
            fig, ax = plt.subplots(figsize=(6, 4))
        else:
            ax = axes

        amps = self._amps(st=st)
        amps = self._detrend_signal(amps)
        if self.norm_amps:
           amps = self._normalize_amps(amps)

        # add empty traces in plot if channels were removed for the visualisation
        receiver = self.receiver
        trace_sep = np.diff(receiver)
        empty_tr_idx = np.where(trace_sep != self.dx)[0]
        nchannels, npts = amps.shape

        # time
        t = np.arange(npts) * self.dt

        # stretch function
        stretch = np.sin(2*np.pi*self.fmin*t + np.pi*(self.fmax-self.fmin)*t**2/self.SFR_time)

        # convolution
        SFR = np.zeros((nchannels,2*npts-1))
        for i in range(nchannels):

            SFR[i] = np.convolve(amps[i],stretch)

        if amp_scale is None:
            amp_scale = np.mean(np.diff(np.array(self.receiver))) / 2

        for i, pos in enumerate(self.receiver):
            SFR[i] = SFR[i] * amp_scale

        # time
        t = np.arange(len(SFR[i])) * self.dt

        # plot SFR
        for i, trace in enumerate(SFR):
            ax.plot(trace+i, t, color=color, linewidth=linewidth,alpha = alpha)

        ymin = kwargs.pop('ymin', np.min(t))
        ymax = kwargs.pop('ymax', np.max(t))
        ax.set_ylim([ymin, ymax])

        ax.grid(axis='y', linestyle=":")
        ax.invert_yaxis()

        ax.set_xlim(-2, (len(self.receiver) - 1) + 2)

        if kwargs.pop('show_xticks',True):
            ax.xaxis.tick_top()
            offsets = self.receiver
            step = int(len(offsets) / scale)
            xticks = np.arange(len(offsets))[step::step]
            ax.set_xticks(np.arange(len(offsets))[step::step])
            xticklabels = []
            for i in xticks:
                xticklabels.append(f'{st[i].stats.channel}\n{offsets[i]}')
            ax.set_xticklabels(xticklabels)

            text = 'channel nr.:\ndistance (m):'
            at = AnchoredText(text,
                              loc='lower left',
                              prop=dict(ha='right'),
                              bbox_to_anchor=(-0.15, 1.0),
                              pad=0, borderpad=0.8, frameon=False,
                              bbox_transform=ax.transAxes)
            ax.add_artist(at)

        if axes is not None:
            return ax

        if outfile:
            if fmt:
                fig.savefig(outfile, format=fmt)
            else:
                fig.savefig(outfile)
        elif show:
            plt.show()
        else:
            return fig


    def _plotDispersionImage(self,axes=None, outfile=None, fmt=None, show=True,
                             **kwargs):
        """plot dispersion image"""

        if axes is None:
            fig,ax = plt.subplots(figsize=(6, 4), constrained_layout=True)
        else:
            ax = axes

        dispersive_energy = self.dispersive_energy

        if self.norm_power:
            # TODO: tmp work around
            local_max = self.use_local_max_power
            self.use_local_max_power = False
            dispersive_energy = self._norm_power(dispersive_energy)
            self.use_local_max_power = local_max
            label = "amplitudes (normalized)"
            limits = (0, 1)
        else:
            label = "amplitudes"
            limits = (np.min(dispersive_energy), np.max(dispersive_energy))

        keyy = kwargs.pop("key","vel")

        if keyy == "vel":
            daty = self.velocity
            labely = "phase velocity (m/s)"
        elif keyy == "k":
            daty = self.wavenumber
            labely = "wavenumber (rad/m)"

        datx = self.frequency
        labelx = "frequency (Hz)"

        # plot dispersion image and dispersion curves
        img = ax.contourf(datx,
                           daty,
                           dispersive_energy,
                           np.linspace(limits[0], limits[1], 21),
                           #extend='both',
                           cmap=plt.cm.get_cmap(kwargs.pop('cmap', 'viridis')))

        ax.grid(True, linestyle=':')
        ax.set_xlabel(labelx)
        ax.set_ylabel(labely)
        ax.set_ylim([np.min(daty), np.max(daty)])

        for axis in ['top', 'bottom', 'left', 'right']:
            ax.spines[axis].set_linewidth(1)

        if kwargs.pop("show_cbar", True):
            plt.colorbar(img, label=label, ax=ax,orientation = 'vertical', pad = 0.01)

        if axes is not None:
            return ax

        if outfile:
            if fmt:
                fig.savefig(outfile, format=fmt)
            else:
                fig.savefig(outfile)
        elif show:
            plt.show()
        else:
            return fig

    def _plotDispersionImageComposite(self, axes=None, outfile=None, fmt=None, show=True,title = None,
                             **kwargs):
        """plot geometry, seismogram and dispersion image"""

        if axes is None:
            fig = plt.figure(figsize=(10, 6))
            gs = fig.add_gridspec(3, 2)
            ax0 = fig.add_subplot(gs[0, 0:2])
            ax1 = fig.add_subplot(gs[1:3, 0])
            ax2 = fig.add_subplot(gs[1:3, 1])
        else:
            ax0 = axes[0]
            ax1 = axes[1]
            ax2 = axes[2]

        # plot geometry
        self._plotGeometry(axes = ax0)
        ax0.set_title(self.pre, fontweight='bold')

        # plot seismogram
        self._plotSeismogram(axes=ax1, amp_scale=None,  **kwargs)

        # plot dispersion image and dispersion curves
        ax2.set_title(title)
        self._plotDispersionImage(axes=ax2,keyy='vel')
        if self._pick:
            for key1 in self._picks.keys():
                for key2 in self._picks[key1].keys():

                    ax2.plot(self._picks[key1][key2]['f'], self._picks[key1][key2]['v'],
                            markeredgecolor='k',
                            marker="s",
                            markersize=5, color='white',
                            linewidth=0)

        #fig.align_ylabels()
        plt.tight_layout()

        if axes is not None:
            return axes

        if outfile:
            if fmt:
                fig.savefig(outfile, format=fmt)
            else:
                fig.savefig(outfile)
        elif show:
            plt.show()
        else:
            return fig


