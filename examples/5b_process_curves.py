from swa import *

# %% MASW2D
# directories
prj_dir = '../data/syn_data'
path2raw = os.path.join(prj_dir,'raw')
path2geom = f'{prj_dir}/geometry_v2_test.csv'
ext = '.sgy' # shot file extension

procset = 'proc1' # processing set label

# processing and plotting settings
settings = create_settings(fmin=2.5, fmax=60,                  # frequency range
                         vmin=10, vmax=1000, velstep=1)     # testing phase velocity range and step

swam = MASW2DManager(f'{prj_dir}/proc/5b_MASW2D',path2raw=path2raw,path2geom=path2geom, settings=settings)

# load data from database based on procset label
swam.set_procset_label(procset)

processing_kwargs = {'min': 2, 'max': 26} # arguments for the processing
swam.preprocess(type='trim',by = 'offset',**processing_kwargs)

# extract dispersion curves
swam.extract(method = 'MOPA', stopAtChi2 = 1, abs_err = 0.01)

fig, ax = plt.subplot_mosaic([['a)'],['b)']])

swam.select_data(sin=3, rep=1, inplace=True)

swam.plot_curves(apply_to = 'cur', procset= procset,
                 method='MOPA',
                 color = 'lightgrey', axes = ax['a)'], label='original', marker = 's', size = 60)

# smooth the dispersion curve
processing_kwargs = {'kernel_size':3} # arguments for the processing
swam.load_procset(procset)
new_procset = 'new'
swam.process_curves(apply_to = 'cur', procset= new_procset,type='smooth',
                    method='MOPA', **processing_kwargs)
swam.plot_curves(apply_to = 'cur', procset= new_procset,
                 method='MOPA', color = 'dodgerblue', axes = ax['a)'], label='smoothed', marker = 'o', size = 25, alpha = 1)

# resample the dispersion curve
swam.load_procset(procset)
processing_kwargs = {'pmin':25, 'pmax':45, 'pn':30} # arguments for the processing
swam.process_curves(apply_to = 'cur', procset= 'new2',
                    type='resample', method='MOPA', **processing_kwargs)
swam.plot_curves(apply_to = 'cur', procset= 'new2',
                 method='MOPA', color = 'red', axes = ax['a)'], label='resampled', marker = 'o', size = 25, alpha = 1)

# filter the dispersion curve
swam.load_procset(procset)
processing_kwargs = {'pmin':30, 'pmax':40, 'param':'f'}
swam.process_curves(apply_to = 'cur', procset= 'new3',
                    type='filter', method='MOPA', **processing_kwargs)
swam.plot_curves(apply_to = 'cur', procset= 'new3',
                 method='MOPA', color = 'k', axes = ax['a)'], label='filtered', marker = 'o', size = 25, alpha = 1)

swam.load_procset(procset)
swam.process_curves(apply_to = 'cur',type='estimate_error', method='MOPA', procset= 'new5')
swam.plot_curves(apply_to = 'cur', procset= 'new5',
                 method='MOPA', color = 'k', axes = ax['b)'], showErr = True,
                 label='original', marker = 'o', size = 25, alpha = 1)

from matplotlib.transforms import ScaledTranslation
for label, ax in ax.items():

    ax.set_xlim([5, 60])
    ax.set_ylim([150, 1000])

    if label in ['a)','b)']:
        ax.text(
            -0.075,0.93, label, transform=(
                ax.transAxes + ScaledTranslation(-20/72, +7/72, fig.dpi_scale_trans)),
                va='bottom')

plt.tight_layout()
plt.show()


