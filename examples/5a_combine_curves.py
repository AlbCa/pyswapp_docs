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

swam = MASW2DManager(f'{prj_dir}/proc/5a_MASW2D',path2raw=path2raw,path2geom=path2geom, settings=settings)

# load processed data
swam.set_procset_label(procset)
#swam.load_procset(procset)

# dispersion curves
# swam.moving_window(minoffset = 3, maxoffset = 1e6, wlen = 24, wmove = 5)
# swam.extract_curves(method = 'MOPA', stopAtChi2 = 1, abs_err = 0.01)
#
# swam.plot('pseudosection',method='MOPA')

# set the data for the combination process and sort based on receiver spread mid point
swam.prepare_CC(method = 'MOPA')

# run some processes from the CC class, e.g., manual filtering of the sorted dispersion curves
swam.filter_CC()

# combine the dispersion curves
CC_kwargs = {'mode' : 0,    # mode 0 = binning; mode 1 = resampling to same frequency range and mean/std calculation
            'a':8,            # parameter controlling the wavelength interval
            'xlim' : [5,80],  # xlimit for plotting
            'ylim' : [50,400],# ylimit for plotting
            'show': False}      # show the combined dc
swam.combine(method = 'MOPA',**CC_kwargs)

# process the dispersion curves if necessary
# swam.process_CC(type='smooth', method='MOPA')

# plot the combined curves as pseudosection
swam.plot_CC(method='MOPA')

# save the dispersion curves to a file
swam.save_CC(method='MOPA')