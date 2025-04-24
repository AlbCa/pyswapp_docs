import sys
import os
nb_dir = os.path.dirname(os.path.abspath("__file__")) # get nb absolute path
prj_root = os.path.abspath(os.path.join(nb_dir, "../")) # set swa path
sys.path.append(prj_root) # add path
from swa import *
from swa import Tomo2DManager
import matplotlib
from matplotlib import interactive
matplotlib.use('Qt5Agg')

# %% Windowing
# directories
prj_dir = '../data/real_data/Moriago'    # I have changed the relative path to make the script work in the "swa" folder
path2raw = os.path.join(prj_dir,'RIFL1')
path2geom = f'{prj_dir}/geometry_test_L1.csv'
ext = '.sg2' # shot file extension

procset = 'proc3' # processing set label

# processing and plotting settings
settings = create_settings(fmin=10, fmax=30,                  # frequency range
                         vmin=300, vmax=800, velstep=2)     # testing phase velocity range and step

swam = MASW2DManager(f'{prj_dir}/proc/40c_MASW2D_L1',path2raw=path2raw,path2geom=path2geom, settings=settings)

# load data from database based on procset label
swam.load_procset('raw')

# set a new procset label
swam.set_procset_label(procset)

# FK filter
swam.preprocess_streams(attr='filter', by = 'FK', fname = 'C:/Users/Ilaria/Documents/GitHub/swa/data/real_data/Moriago/dummy_filter_new2.txt') # manual = 'True') ## **FK_kwargs)

# Run moving window along data
swam.moving_window(minoffset = 50, maxoffset = 100, wlen = 25, wmove = 4)

#Plot the data in each window
#swam.plot_streams(attr='geometry', apply_to = 'all', use_windows=True)

#phaseshift transformation
swam.transform_streams(attr='phaseshift', apply_to = 'all', use_windows=True)

# extract the dispersion curves
swam.extract_curves(apply_to = 'all', pck_mode='manual', use_windows=True) # pck_mode='auto', auto_method = 'max', use_windows=True)

# plot the pseudosection
swam.plot_pseusodsection(method='phaseshift_max', cmap='jet')

# # save the dispersion curves
# swam.save_curves(apply_to = 'all', procset='proc2', method='phaseshift', dc_mode=0, format = 'csv', use_windows=True)
