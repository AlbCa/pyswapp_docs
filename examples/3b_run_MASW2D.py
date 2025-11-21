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
swam.preprocess_streams(type='trim',by = 'offset',**processing_kwargs)

# remove zero amplitude data
swam.preprocess(type='check_traces')

swam.transform(type='phaseshift')
swam.transform(type='fdbf')

# manual dc picking
swam.gui_interact('FV')

# automatic dc picking
swam.extract(method = 'max') # method here can be 'max' or the trafo method

# automatic dc picking
swam.extract(apply_to = 'all', method = 'MOPA', stopAtChi2 = 1, rel_err = 15/100,showResults = True)

# plot the corresponding pseudosections
swam.plot('pseudosection',method = 'phaseshift')
swam.plot('pseudosection',method = 'fdbf')
swam.plot('pseudosection',method = 'max')
swam.plot('pseudosection',method = 'MOPA')
