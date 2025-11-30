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

# %% MASW2D
# directories
prj_dir = '../data/real_data/Moriago'    # I have changed the relative path to make the script work in the "swa" folder
path2raw = os.path.join(prj_dir,'RIFL1')
path2geom = f'{prj_dir}/geometry_test_L1.csv'
ext = '.sg2' # shot file extension

procset = 'proc1' # processing set label

# processing and plotting settings
settings = create_settings(fmin=10, fmax=30,                  # frequency range
                         vmin=300, vmax=800, velstep=2)     # testing phase velocity range and step

swam = MASW2DManager(f'{prj_dir}/proc/40a_MASW2D_L1',path2raw=path2raw,path2geom=path2geom, settings=settings)

# load data from database based on procset label
#swam.load_procset('raw')

# set a new procset label
swam.set_procset_label(procset)

# # plot data
# swam.plot_streams(attr='seismogram', apply_to = 'cur')

# apply preprocessing step to the whole data (apply_to = 'all')
processing_kwargs = {'min': 15, 'max': 100} # arguments for the processing
swam.preprocess_streams(attr='trim', apply_to = 'all',by = 'offset',**processing_kwargs)

# remove zero amplitude data
swam.preprocess_streams(attr='check_traces', apply_to = 'all')

# transform data for all files (apply_to = 'all')
swam.transform_streams(attr='phaseshift', apply_to = 'all')

# # extract dispersion curves automatically for all files (apply_to = 'all')
# swam.extract_curves(apply_to = 'all', pck_mode='auto', auto_method = 'max')
# # --> method to obtain dc is "phaseshift_max" (= transformation method + auto_method)

# # extract dispersion curves manually for selected data (apply_to = 'cur')
swam.extract_curves(apply_to = 'all', pck_mode='manual')
# --> method to obtain dc is "phaseshift" (= transformation method + NO auto_method)

# # process dispersion curve of selected data (apply_to = 'cur')
#processing_kwargs = {'kernel_size':3} # arguments for the processing
#swam.process_curves(apply_to = 'all', attr='smooth', method='phaseshift_max', **processing_kwargs)
#swam.plot_curves(apply_to = 'cur', method='phaseshift_max')

# plot the pseudosection
#swam.plot_pseusodsection(method='phaseshift_max',cmap='jet')
swam.plot_pseusodsection(method='phaseshift',cmap='jet')

# # save the dispersion curves
# swam.save_curves(method='phaseshift_max', format = 'csv')
