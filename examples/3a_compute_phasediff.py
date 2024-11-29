import sys
import copy
import numpy as np
import pickle

sys.path.insert(1, '../../swa')

from utils import *
from _stream import SeismicStream

# %% STEP 1: get phase differences for each file

# directories
prj_dir = '../data/testdata_ilaria/syn_data'
path2raw = os.path.join(prj_dir,'raw')
path2geom = f'{prj_dir}/geometry_test.csv'
path2fk = f'{prj_dir}/proc/fk_filter'
path2diffs = f"{prj_dir}/proc/phase_diffs"
ext = '.sgy' # shot file extension

# processing and plotting settings
settings = create_settings_dict(trafo = 'fdbf',             # transformation type
                         zero_padding=False, freq_step=0.5,  # zero padding
                         normalize = True,local_max = True, # amplitude normalization
                         picking = 'manual',                # picking mode ("manual" or "auto")
                         fmin=5, fmax=50,                  # frequency range
                         vmin=50, vmax=1000, velstep=1)     # testing phase velocity range and step


# get paths to shot files
path2sht = [f.path for f in os.scandir(path2raw) if f.is_file()]
path2sht = natural_sort(path2sht)
path2sht = [[f] for f in path2sht]

# define offset range for forward shots
min_offset_fw = 3
max_offset_fw = 1e6

# define offset range for reverse shots
min_offset_rw = -3
max_offset_rw = -1e6

# minimum receiver number
min_nrec = 6

# %% phase differences
all_phase_diffs = []

for i in range(0,len(path2sht)):

    # read seismic data
    stream = SeismicStream(path2sht[i][0], settings) # record
    fids = stream._argfreq()                         # indices of frequency subset
    nrec = len(stream.receiver)

    # create copy of stream object
    stream_fw = copy.deepcopy(stream) # copy
    stream_rw = copy.deepcopy(stream)  # copy

    fn = os.path.splitext(os.path.basename(path2sht[i][0]))[0] # filename

    # %% process forward shots
    phase_diffs = np.empty((len(fids), nrec - 1))
    phase_diffs[:] = np.nan

    # define offset range
    offset = stream.receiver-stream.source              # signed offset vector
    omin = np.argmin(np.abs(offset - min_offset_fw))    # min offset id
    omax = np.argmin(np.abs(offset - max_offset_fw))    # max offset id
    oids = np.arange(omin, omax+1)                      # offset ids to be used

    if len(offset[oids]) >= min_nrec:

        # filter by offset (remove near offsets)
        stream_fw._trim_by_offsets(min_offset_fw, max_offset_fw)

        # apply fk filtering to remove higher modes
        fk_fname = f'{path2fk}/fw_shots/fkfilter_{fn}.txt'
        path, _ = os.path.split(fk_fname)
        safe_makedirs(path)

        # if file exits apply fk filter
        if os.path.isfile(fk_fname):
            stream_fw._fk_filter_from_file(fname=fk_fname,
                                        show=False)
        # otherwise pick in data
        else:
            stream_fw._fk_filter_from_pick(fname=fk_fname,
                                        show=False)

        # compute phase differences
        phase_diffs_sub, fids = stream_fw._compute_phasediffs()

        # store in array
        phase_diffs[:,oids[:-1]] = phase_diffs_sub

    # %% process reverse shots
    omax = np.argmin(np.abs(offset - min_offset_rw))
    omin = np.argmin(np.abs(offset - max_offset_rw))
    oids = np.arange(omin, omax+1)

    if len(offset[oids]) >= min_nrec:
        # filter by offset (remove near offsets)
        stream_rw._trim_by_offsets(min_offset_rw, max_offset_rw)

        # apply fk filtering to remove higher modes
        fk_fname = f'{path2fk}/rw_shots/fkfilter_{fn}.txt'
        path, _ = os.path.split(fk_fname)
        safe_makedirs(path)

        # if file exits apply fk filter
        if os.path.isfile(fk_fname):
            stream_rw._fk_filter_from_file(fname=fk_fname,
                                           show=False)
        # otherwise pick in data
        else:
            stream_rw._fk_filter_from_pick(fname=fk_fname,
                                           show=False)

        # compute phase differences
        phase_diffs_sub, fids = stream_rw._compute_phasediffs()

        # store in array
        phase_diffs[:,oids[:-1]] = phase_diffs_sub

    all_phase_diffs.append(phase_diffs)

# %% save all phase differences
safe_makedirs(path2diffs)
with open(f"{path2diffs}/all_phase_diffs.pickle", "wb") as fp:
    pickle.dump(all_phase_diffs, fp)


