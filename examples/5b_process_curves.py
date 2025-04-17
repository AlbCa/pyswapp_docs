import matplotlib.pyplot as plt
from matplotlib import interactive

from swa import *
from swa import Tomo2DManager

# %% MASW2D
# directories
prj_dir = '../data/syn_data'
path2raw = os.path.join(prj_dir,'raw')
path2geom = f'{prj_dir}/geometry_v2.csv'
ext = '.sgy' # shot file extension

procset = 'proc1' # processing set label

# processing and plotting settings
settings = create_settings(fmin=10, fmax=50,                  # frequency range
                         vmin=10, vmax=1000, velstep=1)     # testing phase velocity range and step

swam = MASW2DManager(f'{prj_dir}/proc/swa_v2/3b_MASW2D',path2raw=path2raw,path2geom=path2geom, settings=settings)

# load data from database based on procset label
swam.load_procset('proc1')

fig,ax = plt.subplots()
new_procset = 'new'

swam.plot_curves(apply_to = 'cur', procset= procset,
                 method='phaseshift',
                 color = 'lightgrey', axes = ax, label='original', marker = 's', size = 30)

# smooth the dispersion curve
processing_kwargs = {'kernel_size':3} # arguments for the processing
swam.process_curves(apply_to = 'cur', new_procset= new_procset,attr='smooth',
                    method='phaseshift', **processing_kwargs)
swam.plot_curves(apply_to = 'cur', procset= new_procset,
                 method='phaseshift', color = 'orange', axes = ax, label='smoothed', marker = 'o', size = 15, alpha = 1)

# resample the dispersion curve
processing_kwargs = {'pmin':25, 'pmax':40, 'pn':30} # arguments for the processing
swam.process_curves(apply_to = 'cur', new_procset= new_procset,
                    attr='resample', method='phaseshift', **processing_kwargs)
swam.plot_curves(apply_to = 'cur', procset= new_procset,
                 method='phaseshift', color = 'tomato', axes = ax, label='resampled', marker = 'o', size = 15, alpha = 1)

# filter the dispersion curve
processing_kwargs = {'pmin':25, 'pmax':40, 'param':'f'}
swam.process_curves(apply_to = 'cur', new_procset= new_procset,
                    attr='filter', method='phaseshift', **processing_kwargs)
swam.plot_curves(apply_to = 'cur', procset= new_procset,
                 method='phaseshift', color = 'mediumseagreen', axes = ax, label='filtered', marker = 'o', size = 15, alpha = 1)
ax.set_xlim([20,50])
ax.set_ylim([180,250])
plt.show()


