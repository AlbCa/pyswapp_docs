from matplotlib import interactive

from swa import *
from swa import Tomo2DManager

# %% Windowing
# directories
prj_dir = '../data/syn_data'
path2raw = os.path.join(prj_dir,'raw')
path2geom = f'{prj_dir}/geometry_v2.csv'
ext = '.sgy' # shot file extension

procset = 'proc3' # processing set label

# processing and plotting settings
settings = create_settings(fmin=10, fmax=50,                  # frequency range
                         vmin=10, vmax=1000, velstep=1)     # testing phase velocity range and step

swam = MASW2DManager(f'{prj_dir}/proc/swa_v2/3b_MASW2D',path2raw=path2raw,path2geom=path2geom, settings=settings)

# load data from database based on procset label
swam.load_procset('raw')

# set a new procset label
swam.set_procset_label(procset)

# Run moving window along data
swam.moving_window(minoffset = 3, maxoffset = 1e6, wlen = 25, wmove = 10)

#Plot the data in each window
#swam.plot_streams(attr='geometry', apply_to = 'all', use_windows=True)

#phaseshift transformation
swam.transform_streams(attr='phaseshift', apply_to = 'all', use_windows=True)

# extract the dispersion curves
swam.extract_curves(apply_to = 'all', pck_mode='auto', auto_method = 'max', use_windows=True)

# plot the pseudosection
swam.plot_pseusodsection(method='phaseshift_max', cmap='viridis')

# save the dispersion curves
swam.save_curves(apply_to = 'all', procset='proc2', method='phaseshift', dc_mode=0, format = 'csv', use_windows=True)
