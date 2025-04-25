from swa import *

# %% Combine curves
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

# load processed data
swam.set_procset_label(procset)
swam.load_procset(procset)

# set the data for the combination process and sort based on receiver spread mid point
swam.prepare_CC(method = 'MOPA', use_windows=True)

# run some processes from the CC class, e.g., manual filtering of the sorted dispersion curves
swam.CC.filter_all()

# combine the dispersion curves
CC_kwargs = {'mode' : 0,    # mode 0 = binning; mode 1 = resampling to same frequency range and mean/std calculation
            'a':8,            # parameter controlling the wavelength interval
            'xlim' : [5,80],  # xlimit for plotting
            'ylim' : [50,400],# ylimit for plotting
            'save':False,     # save the combined dc
            'show': True}      # show the combined dc
swam.combine(method = 'MOPA', use_windows=True, **CC_kwargs)

# process the dispersion curves if necessary
swam.process_CC(attr='smooth', method='MOPA')

# save the dispersion curves to a file
swam.save_CC(method='MOPA')