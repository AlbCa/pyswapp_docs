import sys
import copy
import numpy as np
import pickle
from obspy import read
import os

sys.path.insert(1, 'swa')

from utils import *
from _stream import SeismicStream

# %% STEP 1: get phase differences for each file

# %% settings
settings = create_settings_dict(
                         picking = 'manual',trafo = 'fdbf', # transformation
                         fmin=5, fmax=40,
                         vmin=100,vmax=1200, velstep=1
                         )

# with open('../testdata_ilaria/syn_data/settings.pickle', 'wb') as fp:
#     pickle.dump(settings, fp, pickle.HIGHEST_PROTOCOL)

min_offset = 6
max_offset = 1e6
min_ntraces = 6

# %% directories
prj_dir = '../Consegna_Moriago/'
path2raw = os.path.join(prj_dir,'RIFL4')
#path2geom = 'geometry.csv'
ext = '.sg2'

# %% survey geometry & recording parameters
# shot_files, source_coordinates, receiver_coordinates = read_geometry(path2geom) # read geometry information
# path2sht = get_shotfiles_from_geometry(path2raw, shot_files, extension = ext, sort_ascending = True) # shot file location
# rec0 = SeismicStream(path2sht[0][0], settings, receiver_coordinates, source_coordinates[0]) # record0
# nshots = len(shot_files) # number of shots
# nrec = len(receiver_coordinates) # number of receivers
# dx = np.mean(np.diff(receiver_coordinates[:,0])) # receiver separataion
# dt = rec0.dt # sampling rate in s
# npts = rec0.npts # number of samples

dx = 5
fs = 256
dt = 1/fs
npts = 512

# %% frequency range
trafo_settings = settings['trafo']
fmin = trafo_settings['fmin']
fmax = trafo_settings['fmax']

omega_fs = 2 * np.pi * 1 / dt
omega = np.arange(npts) * (omega_fs / npts)
freq = omega / (2 * np.pi)

min_id = np.argmin(np.abs(freq - fmin))
max_id = np.argmin(np.abs(freq - fmax))
fids = np.arange(min_id, max_id + 1)
freq_sel = freq[fids]

# %% phase differences
path2sht = os.listdir('../Consegna_Moriago/RIFL4/')
all_phase_diffs = []

for i in range(0,len(path2sht)):

    # Read seismic data
    nfile = os.path.join(path2raw,path2sht[i])
    stream = SeismicStream(nfile, settings) # record
    
    # I correct for the polarity shift of some traces (data dependent)
    stream._st[30].data = -stream._st[30].data
    stream._st[36].data = -stream._st[36].data
    stream._st[40].data = -stream._st[40].data
    stream._st[49].data = -stream._st[49].data
    
    # ## I try to extract parameters directly from traces
    # nfile = os.path.join(path2raw,path2sht[i])
    # stream = read(nfile)
    ntraces = stream._st.count()
    srcx = stream._st[0].stats.sx
    recx = np.empty(ntraces)
    for rr in range(ntraces):
       recx[rr]=stream._st[rr].stats.rx
        
    stream_fw = copy.deepcopy(stream) # copy
    stream_rw = copy.deepcopy(stream)  # copy    

    fn = os.path.splitext(os.path.basename(path2sht[i]))[0] # filename

    # %% empty phase difference matrix
    phase_diffs = np.empty((len(fids), ntraces - 1))
    phase_diffs[:] = np.nan

    #### FORWARD SHOTS
    # define offset range
    offset = recx - srcx # signed offset vector
    oids = np.argwhere((offset > min_offset) & (offset < max_offset))[:,0]
    
    offset_fw = offset[oids]

    # filter by offset (remove near offsets)
    if len(offset_fw) >= min_ntraces:
        
        stream_fw._trim_by_offsets(min_offset, max_offset)

        #stream_fw._apply_trafo(do_pick=False) # apply transformation
        #stream_fw._plotDispersionImage() # plot dispersion image

        # filter fk spectrum (only keep apparent fundamental mode)
        #stream_fw._fk_filter(fod = f'../testdata_ilaria/syn_data/proc/fk_filter/fw_shots/fkfilter_{fn}.txt')
        stream_fw._fk_filter_from_file(fname='C:/Users/Ilaria/Downloads/dummy_filter_new2.txt', show=False, taper_length=5)
        #stream_fw._fk_filter_from_pick(fname='C:/Users/Ilaria/Downloads/dummy_filter_new.txt', show=False)

        # # plot seismogram
        # fig, ax = plt.subplots(1, 2, figsize=(10, 4))
        # stream._plotSeismogram(axes=ax[0], show_map=True, amp_scale=1.1)
        # stream_fw._plotSeismogram(axes=ax[1], show_map=True, amp_scale=1.1)
        # plt.savefig(f'syn_data/plots/seis_fw_shot{int(source_coordinates[i][0])}.png')
        # plt.close()

        # compute phase differences
        phase_diffs_sub, fids = stream_fw._compute_phasediffs()

        # store in array
        phase_diffs[:,oids[:-1]] = phase_diffs_sub


    #### REVERSE SHOTS
    # define offset range
    offset = recx - srcx # signed offset vector
    oids = np.argwhere((offset > -max_offset) & (offset < -min_offset))[:,0]

    offset_rw = offset[oids]

    if len(offset_rw) >= min_ntraces:
        # filter by offset (remove near offsets)
        stream_rw._trim_by_offsets(-min_offset, -max_offset)

        #stream_rw._apply_trafo(do_pick=False) # apply transformation
        
        stream_rw._fk_filter_from_file(fname='C:/Users/Ilaria/Downloads/dummy_filter_new2.txt', show=False, taper_length=5)
        #stream_rw._fk_filter_from_pick(fname='C:/Users/Ilaria/Downloads/dummy_filter_new.txt', show=False)

        # plot seismogram
        # fig, ax = plt.subplots(1, 2, figsize=(10, 4))
        # stream._plotSeismogram(axes=ax[0], show_map=True, amp_scale=1.1)
        # stream_rw._plotSeismogram(axes=ax[1], show_map=True, amp_scale=1.1)
        # plt.savefig(f'syn_data/plots/seis_rw_shot{int(source_coordinates[i][0])}.png')
        # plt.close()

        # compute phase differences
        phase_diffs_sub, fids = stream_rw._compute_phasediffs()

        # store in array
        phase_diffs[:,oids[:-1]] = phase_diffs_sub
        
    all_phase_diffs.append(phase_diffs)

# %% save all phase differences
with open("D:/Documenti/UNIPD/RTDA/Dati_a_riflessione_shallow/Moriago_della_Battaglia/Tomo2D/all_phase_diffs.pickle", "wb") as fp:
    pickle.dump(all_phase_diffs, fp)
    

