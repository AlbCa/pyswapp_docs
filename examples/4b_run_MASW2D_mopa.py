from swa import *
from plot_settings import *

# directories
prj_dir = '../data/syn_data'
path2raw = os.path.join(prj_dir,'raw')
path2geom = f'{prj_dir}/geometry_v2_test.csv'
ext = '.sgy' # shot file extension

procset = 'proc2' # processing set label

# processing and plotting settings
settings = create_settings(fmin=15, fmax=50,                  # frequency range
                         vmin=10, vmax=600, velstep=1)     # testing phase velocity range and step

swam = MASW2DManager(f'{prj_dir}/proc/swa_v1/3b_MASW2D',path2raw=path2raw,path2geom=path2geom, settings=settings)

# load data from database based on procset label
swam.load_procset('raw')

# # plot data
# swam.plot_streams(attr='seismogram', apply_to = 'cur')

# set a new procset label
swam.set_procset_label(procset)

# apply preprocesisng step to data
processing_kwargs = {'min': 2, 'max': 25} # arguments for the processing
swam.preprocess_streams(attr='trim', apply_to = 'all',by = 'offset',**processing_kwargs)

processing_kwargs = {'min': -25, 'max': -2} # arguments for the processing
swam.preprocess_streams(attr='trim', apply_to = 'all',by = 'offset',**processing_kwargs)

# extract dispersion curves automatically
processing_kwargs = {'showMOPAResults':True, 'cmap': 'Greys'} # arguments for the processing
swam.extract_curves(apply_to = 'all', pck_mode='auto', auto_method = 'MOPA', **processing_kwargs)
# --> method to obtain dc is "MOPA" (no transformation + auto_method)

# plot the pseudosection
swam.plot_pseusodsection(method='MOPA', dc_mode=0, cmap='viridis', show = True)

# save the dispersion curves
swam.save_curves(method='MOPA', dc_mode=0, format = 'csv')
