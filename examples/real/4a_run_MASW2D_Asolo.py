from matplotlib import interactive

from swa import *
from swa import Tomo2DManager

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

swam = MASW2DManager(f'{prj_dir}/proc/test_MASW2D',path2raw=path2raw,path2geom=path2geom, settings=settings)

# load data from database based on procset label
swam.load_procset('proc1')

# set a new procset label
swam.set_procset_label(procset)

# plot data
swam.plot_streams(attr='geometry', apply_to = 'all')

#apply preprocessing step to the whole data (apply_to = 'all')
processing_kwargs = {'min': 1, 'max': 1e10} # arguments for the processing
swam.preprocess_streams(attr='trim', apply_to = 'all',by = 'offset',**processing_kwargs)

# remove zero amplitude data
swam.preprocess_streams(attr='check_traces', apply_to = 'all')

# transform data for all files (apply_to = 'all')
swam.transform_streams(attr='phaseshift', apply_to = 'all')
#
# extract dispersion curves automatically for all files (apply_to = 'all')
# swam.extract_curves(apply_to = 'all', pck_mode='auto', auto_method = 'max')
# --> method to obtain dc is "phaseshift_max" (= transformation method + auto_method)

# # # extract dispersion curves manually for selected data (apply_to = 'cur')
swam.extract_curves(apply_to = 'all', pck_mode='manual')
# # --> method to obtain dc is "phaseshift" (= transformation method + NO auto_method)
#

# plot the pseudosection
swam.plot_pseusodsection(method='phaseshift_max',cmap='viridis')

# save the dispersion curves
swam.save_curves(method='phaseshift_max', format = 'csv')
