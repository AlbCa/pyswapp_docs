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
swam.moving_window(minoffset = 3, maxoffset = 1e6, wlen = 24, wmove = 5)
swam.extract_curves(method = 'MOPA', stopAtChi2 = 1, abs_err = 0.01)

swam.plot('pseudosection',method='MOPA')

# combine the dispersion curves based on binning
CC_kwargs = {'combination_method' : 'binning',
            'a':8,            # parameter controlling the wavelength interval
            'xlim' : [5,80],  # xlimit for plotting
            'ylim' : [50,400],# ylimit for plotting
            'show': False}      # show the combined dc

# # combine the dispersion curves based on resampling
# CC_kwargs = {'combination_method' : 'resampling',
#             'pmin':5,            # minimum frequency for common frequency range
#             'pmax':50,           # maximum frequency for common frequency range
#             'pn': 30,            # number of new sampling points
#             'pspace': 'log',     # log or linear scale
#             'kind': 'cubic',     # kind of interpolation
#             'xlim' : [5,80],  # xlimit for plotting
#             'ylim' : [50,400],# ylimit for plotting
#             'show': False}      # show the combined dc

swam.combine(method = 'MOPA', filter = False, **CC_kwargs)

# process the dispersion curves if necessary
swam.process_CC(type='smooth', method='MOPA')

# plot the combined curves as pseudosection
swam.plot_CC(method='MOPA')

# save the dispersion curves to a file
swam.save_CC(method='MOPA')