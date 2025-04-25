import matplotlib.pyplot as plt
from matplotlib import interactive

from swa import *
from plot_settings import *

# %% Windowing
# directories
prj_dir = '../data/real_data/Moriago'
path2raw = os.path.join(prj_dir,'raw')
path2geom = f'{prj_dir}/geometry_raw.csv'
ext = '.sg2' # shot file extension

procset = 'proc3' # processing set label

# processing and plotting settings
settings = create_settings(fmin=10, fmax=40,                  # frequency range
                         vmin=10, vmax=1000, velstep=1)     # testing phase velocity range and step

swam = MASW2DManager(f'{prj_dir}/proc/swa_raw/3b_MASW2D',path2raw=path2raw,path2geom=path2geom, settings=settings)

# # load data from database based on procset label
# swam.load_procset('raw')
#
# # set a new procset label
# swam.set_procset_label(procset)
# swam.preprocess_streams(attr='check_traces', apply_to = 'all')
#
# # Run moving window along data
# swam.moving_window(minoffset = 3, maxoffset = 20, wlen = 24, wmove = 3)
#
# #Plot the data in each window
# #swam.plot_streams(attr='geometry', apply_to = 'all', use_windows=True)
#
# # # # # #phaseshift transformation
# swam.transform_streams(attr='fdbf', apply_to = 'all', use_windows=True)
# # # # swam.plot_streams(attr='dispersionImageComposite', apply_to = 'all', use_windows=True,
# # # #                   show_map = False, color = 'k', cmap = 'Greys', show = True)
# #
# #
# # # extract the dispersion curves
# swam.extract_curves(apply_to = 'all', pck_mode='manual', trafo_method = 'fdbf', use_windows=True)
# swam.extract_curves(apply_to = 'all', pck_mode='auto', auto_method = 'max', trafo_method = 'phaseshift', use_windows=True)
# # swam.extract_curves(apply_to = 'all', pck_mode='auto', auto_method = 'MOPA', use_windows=True)
#
# # plot the pseudosection
swam.plot_pseusodsection(auto_method = None, trafo_method = 'fdbf', cmap='cividis', vmin = 400, vmax = 700, fmin  = 10, fmax = 40, width = 5)
# fig,ax = plt.subplots(figsize=(6,3))
# swam.plot_pseusodsection(method='MOPA', dc_mode=0, cmap='cividis', axes = ax,
#                          outfile = '/home/Natalie/Documents/Projects/GIT/swa/data/syn_data/figures_EGU/Pseudosections/pseudo_mopa.png')

#
# # save the dispersion curves
# swam.save_curves(apply_to = 'all', procset='proc2', method='phaseshift', dc_mode=0, format = 'csv', use_windows=True)
