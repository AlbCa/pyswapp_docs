import sys
import os
nb_dir = os.path.dirname(os.path.abspath("__file__")) # get nb absolute path
prj_root = os.path.abspath(os.path.join(nb_dir, "/home/Natalie/Documents/Projects/GIT/swa")) # set swa path
sys.path.append(prj_root) # add path
from swa import *


# %% MASW2D
# directories
prj_dir = '../../data/real_data/AsoloL1'
path2raw = os.path.join(prj_dir,'raw/dat')
path2geom = f'{prj_dir}/geometry_dat.csv'
ext = '.dat' # shot file extension

procset = 'proc1' # processing set label

# processing and plotting settings
settings = create_settings(fmin=10, fmax=50,                  # frequency range
                         vmin=10, vmax=1000, velstep=1)     # testing phase velocity range and step

swam = MASW2DManager(f'{prj_dir}/proc/test_MASW2D_v3')

# %%
swam.gui_view(attr='FK')

swam.gui_interact(attr='FK')















# %%
# processing_kwargs = {'min': 10, 'max': 1e10} # arguments for the processing
#swam.preprocess_streams(procset = procset,attr='trim', apply_to = 'all',by = 'offset',**processing_kwargs)
# swam.preprocess_streams(procset = procset,attr='filter', apply_to = 'all',by = 'mute')
#swam.plot_streams(attr = 'geometry')

#swam.moving_window(minoffset = 2, maxoffset = 10, wlen = 24, wmove = 4)
# plot data
#swam.plot_streams(attr='geometry', use_windows=True)
#swam.test_plot(attr='seismogram',procset='raw')
#swam.plot_streams(attr='seismogram', use_windows=True)
# swam.transform('phaseshift', use_windows=True)
# swam.plot_streams(attr='dispersionImageComposite', use_windows=True,procset='proc1')
#swam.plot(attr='spectrogram')
#swam.plot_streams(attr='spectra', apply_to = 'cur')
#swam.plot_streams(attr='dispersionImage', apply_to = 'cur', use_windows=True)
# swam.transform('phaseshift', use_windows=True)

# %%

#swam.plot_streams(attr='SFR', apply_to = 'cur')

# # set a new procset label
# swam.set_procset_label(procset)
#
# # apply preprocessing step to the whole data (apply_to = 'all')
# processing_kwargs = {'min': 1, 'max': 1e10} # arguments for the processing
# swam.preprocess_streams(attr='trim', apply_to = 'cur',by = 'offset',**processing_kwargs)
#
# # reverse polarity
# swam.preprocess_streams(attr='filter', apply_to = 'cur',by = 'reverse_polarity', ids = range(10,40))
# swam.plot_streams(attr='seismogram', apply_to = 'cur')
# #
# # extract dispersion curves automatically for all files (apply_to = 'all')
# # swam.extract_curves(apply_to = 'all', pck_mode='auto', auto_method = 'max')
# # --> method to obtain dc is "phaseshift_max" (= transformation method + auto_method)
#
# # # # extract dispersion curves manually for selected data (apply_to = 'cur')
# swam.extract_curves(apply_to = 'all', pck_mode='manual')
# # # --> method to obtain dc is "phaseshift" (= transformation method + NO auto_method)
# #
#
# # plot the pseudosection
# swam.plot_pseusodsection(method='phaseshift_max',cmap='viridis')
#
# # save the dispersion curves
# swam.save_curves(method='phaseshift_max', format = 'csv')
