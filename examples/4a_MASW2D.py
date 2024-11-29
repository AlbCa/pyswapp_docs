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
prj_dir = '../data/testdata_ilaria/syn_data'
path2raw = os.path.join(prj_dir,'raw')
path2geom = f'{prj_dir}/geometry_test.csv'
path2fk = f'{prj_dir}/proc/fk_filter/fw_shots/fkfilter_Shot_test.txt'
path2disp = f'{prj_dir}/proc/dc_pick/win_all/picks/'
path2cmb = f'{prj_dir}/proc/dc_pick/win_all/cmb/'
ext = '.sgy' # shot file extension

# processing and plotting settings
settings = create_settings_dict(trafo = 'fdbf',             # transformation type
                         zero_padding=True, freq_step=0.5,  # zero padding
                         normalize = True,local_max = True, # amplitude normalization
                         picking = 'auto',                  # picking mode ("manual" or "auto")
                         fmin=10, fmax=50,                  # frequency range
                         vmin=50, vmax=1000, velstep=1)     # testing phase velocity range and step


# get paths to shot files, survey geometry from geometry.csv
shot_files, source_coordinates, receiver_coordinates = read_geometry(path2geom)
path2sht = get_shotfiles_from_geometry(path2raw, shot_files, extension = ext, sort_ascending = False)

# %% windowing
# define window length
win_len = 24

# define minimum and maximum accepted offsets
min_offset = 2
max_offset = 5

# increment with which the window moves
sr_move = 1

# loop over all files
for i in range(0,len(path2sht)):
    stream = SeismicStream(path2sht[i][0],      # shot file
                           settings)            # settings dict
    stream._check_traces()                      # remove traces where all amplitudes are zero

    # windowing procedure
    stream._windowing(path2disp,
                      win_len,
                      min_offset, max_offset,
                      sr_move)

# read the dispersion curve data and plot the 2D pseudosection
path2csv = '0_csv'
subfolders = [f.path for f in os.scandir(path2disp) if (f.is_dir())]
subfolders = natural_sort(subfolders)

vmin = 100
vmax = 220

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
                          width = 0.25,)


plot_colorBar(ax, vmin, vmax, cmap='viridis', orientation='vertical')
ax.set_xlim([receiver_coordinates[0,0],receiver_coordinates[-1,0]])
ax.set_ylim([5,50])

ax.set_title('Raw picks')
plt.show()

# %% combine dispersion curves
combCurves = CombineCurves(prjdir=path2disp,        # location where dcs are stored
                           path2cmb = path2cmb)     # location where combined dcs shall be stored

# import the data located in path2disp
combCurves._import_data()

# interactive filtering of data
# combCurves._filter_all()

# combine all dispersion curves with same xmid
combCurves._combine_all(a=8,            # parameter controlling the wavelength interval
                        save=True,      # save the combined dc
                        show=False)     # show the combined dc

# read the dispersion curve data and plot the 2D pseudosection
path2csv = '0_csv'
dcs = [f.path for f in os.scandir(os.path.join(path2cmb,path2csv))]

vmin = 100
vmax = 220

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
                  width = 0.25,)


plot_colorBar(ax, vmin, vmax, cmap='viridis', orientation='vertical')
ax.set_xlim([receiver_coordinates[0,0],receiver_coordinates[-1,0]])
ax.set_ylim([5,50])

ax.set_title('Raw picks')
plt.show()