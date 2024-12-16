import sys
import copy
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(1, '../../swa')

from geometry import *
from utils import *
from _stream import SeismicStream
from _curve import Curve
from _combineCurves import CombineCurves

# %% Windowing and combination of dispersion curves

# directories
method = 'mopa'

version = 'v7'
prj_dir = '../data/testdata_ilaria/syn_data/'
path2raw = '../../../data/Synthetic_data/resampled/'
path2geom = f'{prj_dir}/geometry_test.csv'
path2fk = f'{prj_dir}/proc/{version}/fk_filter'
path2diffs = f"{prj_dir}/proc/{version}/tomo2d/phase_diffs"

path2disp = f'{prj_dir}/proc/{version}/{method}/picks/'
path2cmb = f'{prj_dir}/proc/{version}/{method}/cmb/'
path2plot = f'{prj_dir}/proc/{version}/plots/'
ext = '.sgy' # shot file extension

safe_makedirs(path2plot)

fmin = 10
fmax = 50

# processing and plotting settings
settings = create_settings_dict(trafo = method,             # transformation type
                         zero_padding=False, freq_step=0.5,  # zero padding
                         normalize = True,local_max = True, # amplitude normalization
                         picking = version,                  # picking mode ("manual" or "auto")
                         fmin=fmin, fmax=fmax,                  # frequency range
                         vmin=50, vmax=1500, velstep=1,     # testing phase velocity range and step
                         normalize_power = True, local_max_power = False,)

# get paths to shot files, survey geometry from geometry.csv
shot_files, source_coordinates, receiver_coordinates = read_geometry(path2geom)
path2sht = get_shotfiles_from_geometry(path2raw, shot_files, extension = ext, sort_ascending = False)

# % MOPA
rel_err = 10/100
chi2 = 1.5

# apply FK filtering
filter_fk = True

# %% windowing
# define window length
win_len = 30

# define offset range
min_offset_win = 3
max_offset_win = 16

min_offset = 3
max_offset = 1e6


# move increment
sr_move = 2

# minimum receiver number
min_nrec = 12

# loop over all files
for i in range(0,len(path2sht)):

    # read seismic data
    stream = SeismicStream(path2sht[i][0], settings) # record
    fn = os.path.splitext(os.path.basename(path2sht[i][0]))[0]  # filename

    # create copy of stream object
    stream_fw = copy.deepcopy(stream) # copy
    stream_rw = copy.deepcopy(stream)  # copy

    # define offset range
    offset = stream.receiver-stream.source              # signed offset vector
    oids = np.argwhere((offset > min_offset) & (offset < max_offset))[:, 0]

    if len(offset[oids]) >= min_nrec:

        # filter by offset (remove near offsets)
        stream_fw._select_traces(oids)

        # apply fk filtering to remove higher modes
        fk_fname = f'{path2fk}/fw_shots/fkfilter_{fn}.txt'
        path, _ = os.path.split(fk_fname)
        safe_makedirs(path)

        stream_fw_cp = copy.deepcopy(stream_fw)
        stream_fw_cp._fdbf()

        if filter_fk:
            # if file exits apply fk filter
            if os.path.isfile(fk_fname):
                stream_fw._fk_filter_from_file(fname=fk_fname,
                                            show=False)
            # otherwise pick in data
            else:
                stream_fw._fk_filter_from_pick(fname=fk_fname,
                                            show=False)

        # # figure
        # fig, ax = plt.subplots(2, 2, constrained_layout=True)
        # stream_fw_cp._fdbf()
        # stream_fw._fdbf()
        # stream_fw_cp._plotDispersionImage(axes=ax[1, 0])
        # stream_fw_cp._plotSeismogram(axes=ax[0, 0],amp_scale=2)
        # stream_fw._plotDispersionImage(axes=ax[1, 1])
        # stream_fw._plotSeismogram(axes=ax[0, 1],amp_scale=2)
        # plt.show()

        # windowing procedure
        stream_fw._windowing(path2disp,
                          win_len,
                          min_offset_win, max_offset_win,
                          sr_move,
                          showMOPAResults = False,
                          min_nrec = min_nrec,
                          weighted = True,
                          rel_err = rel_err,
                          stopAtChi2 = chi2)

    # define offset range
    oids = np.argwhere((offset > -max_offset) & (offset < -min_offset))[:, 0]

    if len(offset[oids]) >= min_nrec:

        # filter by offset (remove near offsets)
        stream_rw._select_traces(oids)

        # apply fk filtering to remove higher modes
        fk_fname = f'{path2fk}/rw_shots/fkfilter_{fn}.txt'
        path, _ = os.path.split(fk_fname)
        safe_makedirs(path)

        if filter_fk:
            # if file exits apply fk filter
            if os.path.isfile(fk_fname):
                stream_rw._fk_filter_from_file(fname=fk_fname,
                                               show=False)
            # otherwise pick in data
            else:
                stream_rw._fk_filter_from_pick(fname=fk_fname,
                                               show=False)

        # windowing procedure
        stream_rw._windowing(path2disp,
                             win_len,
                             min_offset_win, max_offset_win,
                             sr_move,
                             #showMOPAResults=True,
                             min_nrec=min_nrec,
                             weighted=True,
                             rel_err=rel_err,
                             stopAtChi2=chi2)

# read the dispersion curve data and plot the 2D pseudosection
path2csv = '0_csv'
subfolders = [f.path for f in os.scandir(path2disp) if (f.is_dir())]
subfolders = natural_sort(subfolders)

vmin = 200
vmax = 500

fig,ax = plt.subplots(figsize=(8,6), constrained_layout = True)

for i,subfolder in enumerate(subfolders):

    dir = os.path.join(subfolder, path2csv)
    _, sf = os.path.split(subfolders[i])
    xmid = float(sf)

    if os.path.isdir(dir):
        for fname in os.listdir(dir):

            curve = Curve()
            curve._read(os.path.join(dir, fname))
            curve._plotColumn(axes = ax,
                          xmid = xmid,
                          vmin = vmin, vmax = vmax,
                          cmap = 'viridis', y_value = 'f',
                          width = 0.5*sr_move,)


plot_colorBar(ax, vmin, vmax, cmap='viridis', orientation='vertical')
ax.set_xlim([receiver_coordinates[0,0],receiver_coordinates[-1,0]])
ax.set_ylim([fmin,fmax])

ax.set_title('MOPA')
fig.savefig(os.path.join(path2plot,'raw_mopa.png'))
plt.show()

# %% combine dispersion curves
combCurves = CombineCurves(prjdir=path2disp,        # location where dcs are stored
                           path2cmb = path2cmb)     # location where combined dcs shall be stored

# import the data located in path2disp
combCurves._import_data()

# interactive filtering of data
#combCurves._filter_all()

# combine all dispersion curves with same xmid
combCurves._combine_all(mode=1,
                        a= 8,
                        kind = 'cubic',
                        pn=30,            # parameter controlling the wavelength interval
                        save=True,      # save the combined dc
                        show=False)     # show the combined dc

# read the dispersion curve data and plot the 2D pseudosection
path2csv = '0_csv'
dcs = [f.path for f in os.scandir(os.path.join(path2cmb,path2csv))]

fig,ax = plt.subplots(figsize=(8,6), constrained_layout = True)

for i,fname_dc in enumerate(dcs):

    _, sf = os.path.split(fname_dc)
    xmid = float(re.findall(r"[-+]?(?:\d*\.*\d+)", sf)[0])

    curve = Curve()
    curve._read(fname_dc)
    curve._plotColumn(axes = ax,
                  xmid = xmid,
                  vmin = vmin, vmax = vmax,
                  cmap = 'viridis', y_value = 'f',
                  width = 0.5*sr_move,)


plot_colorBar(ax, vmin, vmax, cmap='viridis', orientation='vertical')
ax.set_xlim([receiver_coordinates[0,0],receiver_coordinates[-1,0]])
ax.set_ylim([fmin,fmax])

ax.set_title('MOPA')
fig.savefig(os.path.join(path2plot,'mean_mopa.png'))
plt.show()

# plot a single dispersion curve and the error
_, sf = os.path.split(dcs[25])
xmid = float(re.findall(r"[-+]?(?:\d*\.*\d+)", sf)[0])
curve = Curve()
curve._read(dcs[0])
fig, ax = plt.subplots(figsize=(8, 6), constrained_layout=True)
curve._plotdata(axes=ax)
fig.savefig(os.path.join(path2plot,'dc.png'))
plt.close()
