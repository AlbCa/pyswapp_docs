from swa import *

# %% MASW2D
# directories
prj_dir = '../data/syn_data'
path2raw = os.path.join(prj_dir,'raw')
path2geom = f'{prj_dir}/geometry_v2_test.csv'
ext = '.sgy' # shot file extension

procset = 'proc1' # processing set label

# processing and plotting settings
settings = create_settings(fmin=10, fmax=50,                  # frequency range
                         vmin=10, vmax=1000, velstep=1)     # testing phase velocity range and step

swam = MASW2DManager(f'{prj_dir}/proc/3b_MASW2D',path2raw=path2raw,path2geom=path2geom, settings=settings)

# load data from database based on procset label
swam.load_procset('proc1')

# set a new procset label
swam.set_procset_label(procset)

#apply preprocessing step to the whole data (apply_to = 'all')
processing_kwargs = {'min': 1, 'max': 1e10} # arguments for the processing
swam.preprocess_streams(attr='trim', apply_to = 'all',by = 'offset',**processing_kwargs)

# remove zero amplitude data
swam.preprocess(attr='check_traces', apply_to = 'all')

# transform data for all files (apply_to = 'all')
swam.transform(attr='phaseshift', apply_to = 'all')
swam.transform(attr='fdbf', apply_to = 'all')

# manual dc picking
swam.gui_interact('FV')

# automatic dc picking
swam.extract(method = 'max',apply_to = 'all') # method here can be 'max' or the trafo method

# automatic dc picking
swam.extract(apply_to = 'all', method = 'MOPA', stopAtChi2 = 1, rel_err = 15/100)

# plot the corresponding pseudosections
swam.plot('pseudosection',method = 'phaseshift')
swam.plot('pseudosection',method = 'fdbf')
swam.plot('pseudosection',method = 'max')
swam.plot('pseudosection',method = 'MOPA')
