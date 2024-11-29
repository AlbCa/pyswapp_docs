import sys
import copy
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(1, '../../swa')

from geometry import *
from utils import *
from _stream import SeismicStream
from _curve import Curve

# %% Windowing approach with MOPA

# directories
prj_dir = '../data/testdata_ilaria/syn_data'
path2raw = os.path.join(prj_dir,'raw')
path2geom = f'{prj_dir}/geometry_test.csv'
path2fk = f'{prj_dir}/proc/fk_filter/fw_shots/fkfilter_Shot_test.txt'
path2disp = f'{prj_dir}/proc/dc_pick/mopa/'
ext = '.sgy' # shot file extension

# processing and plotting settings
settings = create_settings_dict(trafo = 'mopa',             # transformation type
                         zero_padding=True, freq_step=0.5,  # zero padding
                         normalize = True,local_max = True, # amplitude normalization
                         #picking = 'manual',                # picking mode ("manual" or "auto")
                         fmin=10, fmax=50,                  # frequency range
                         vmin=50, vmax=1000, velstep=1)     # testing phase velocity range and step


# get paths to shot files, survey geometry from geometry.csv
shot_files, source_coordinates, receiver_coordinates = read_geometry(path2geom)
path2sht = get_shotfiles_from_geometry(path2raw, shot_files, extension = ext, sort_ascending = False)

# %% windowing
# define window length
win_len = 16

# define minimum and maximum accepted offsets
min_offset = 2
max_offset = 6

# increment with which the window moves
sr_move = 1

stream = SeismicStream(path2sht[0][0],      # shot file
                       settings,            # settings dict
                       path2geom,           # path to the geometry file
                       source_index = 0)    # source/shot index number
stream._check_traces()                      # remove traces where all amplitudes are zero

# windowing procedure
streams_dict = stream._windowing(path2disp,
                                  win_len,
                                  min_offset, max_offset,
                                  sr_move,
                                  fk_filter=False,          # some visualisation and processing options during windowing
                                  path2fk = None,
                                  show_FK = False,
                                  show_SFR = False,
                                  show_seismogram = False,
                                  show_spectrogram = False,
                                  show_previousDC=False,
                                  )

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
                          cmap = 'viridis', y_value = 'lam',
                          width = 0.25,)

plot_colorBar(ax, vmin, vmax, cmap='viridis', orientation='vertical')
ax.set_xlim([10,30])
ax.set_ylim([5,80])

ax.set_title('Raw picks')
plt.show()
