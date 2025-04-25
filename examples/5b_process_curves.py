import matplotlib.pyplot as plt
from matplotlib import interactive

from swa import *
from plot_settings import *
from swa import Tomo2DManager

# %% MASW2D
# directories
prj_dir = '../data/syn_data'
path2raw = os.path.join(prj_dir,'raw')
path2geom = f'{prj_dir}/geometry_v2_test.csv'
ext = '.sgy' # shot file extension

procset = 'proc2' # processing set label

# processing and plotting settings
settings = create_settings(fmin=10, fmax=50,                  # frequency range
                         vmin=10, vmax=1000, velstep=1)     # testing phase velocity range and step

swam = MASW2DManager(f'{prj_dir}/proc/swa_v1/3b_MASW2D',path2raw=path2raw,path2geom=path2geom, settings=settings)

# load data from database based on procset label
swam.load_procset('proc2')

fig,ax = plt.subplots(2,1, figsize = (8,8))
new_procset = 'new'

swam.select_data(sin=3, rep=1, inplace=True)

swam.plot_curves(apply_to = 'cur', procset= procset,
                 method='MOPA',
                 color = 'lightgrey', axes = ax[0], label='original', marker = 's', size = 60)

# smooth the dispersion curve
processing_kwargs = {'kernel_size':3} # arguments for the processing
swam.process_curves(apply_to = 'cur', new_procset= new_procset,attr='smooth',
                    method='MOPA', **processing_kwargs)
swam.plot_curves(apply_to = 'cur', procset= new_procset,
                 method='MOPA', color = 'dodgerblue', axes = ax[0], label='smoothed', marker = 'o', size = 25, alpha = 1)

# resample the dispersion curve
processing_kwargs = {'pmin':25, 'pmax':45, 'pn':30} # arguments for the processing
swam.process_curves(apply_to = 'cur', new_procset= 'new2',
                    attr='resample', method='MOPA', **processing_kwargs)
swam.plot_curves(apply_to = 'cur', procset= 'new2',
                 method='MOPA', color = 'red', axes = ax[0], label='resampled', marker = 'o', size = 25, alpha = 1)

# filter the dispersion curve
processing_kwargs = {'pmin':30, 'pmax':40, 'param':'f'}
swam.process_curves(apply_to = 'cur', new_procset= 'new3',
                    attr='filter', method='MOPA', **processing_kwargs)
swam.plot_curves(apply_to = 'cur', procset= 'new3',
                 method='MOPA', color = 'k', axes = ax[0], label='filtered', marker = 'o', size = 25, alpha = 1)


swam.process_curves(apply_to = 'cur',attr='estimate_error', method='MOPA', new_procset= 'new5', **processing_kwargs)
swam.plot_curves(apply_to = 'cur', procset= 'new5',
                 method='MOPA', color = 'k', axes = ax[1], showErr = True,
                 label='original', marker = 'o', size = 25, alpha = 1)

for axi in ax.flat:
    axi.set_xlim([15,50])
    axi.set_ylim([100,600])

plt.tight_layout()
plt.savefig('/home/Natalie/Documents/Projects/GIT/swa/data/syn_data/figures_EGU/process_curves.png')


