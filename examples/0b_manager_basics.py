from swa import *

# %% Base operations with Manager classes

# directories
prj_dir = '../data/syn_data'
path2raw = os.path.join(prj_dir,'raw')
path2geom = f'{prj_dir}/geometry_v2_test.csv'
ext = '.sgy' # shot file extension

# processing and plotting settings
settings = create_settings(fmin=1, fmax=100,                # frequency range
                         vmin=10, vmax=1000, velstep=1)     # testing phase velocity range and step

# %% 1. Create a new project
# this will
# - 1. create the project directory structure if it does not exist
# - 2. copy raw data and geometry into the project directory if paths are provided
swam = BaseManager(f'{prj_dir}/proc/0b_basics', # project directory path
                   path2raw=path2raw,                       # optional, copy & per default rename data from path (outside project directory)
                   path2geom=path2geom,                     # optional, copy geom from path (outside project directory)
                   settings=settings,                       # optional, define settings for visualisations and processing
                   rename = False,                          # optional, rename copied raw data to preferred filename format (Shotfile_<index>), default value is False!
                   )


# %% 2. Load a created project
#swam = BaseManager(f'{prj_dir}/proc/test') # project directory path

# %% 3. interact with the data
# load data from database based on existing procset label
#swam.load_procset('raw')

# set a new procset label
procset = 'proc1' # processing set label
swam.set_procset_label(procset)

# select data
swam.select_data(sin=1, rep=1, inplace=True)

# preprocess the data
# trim by offset
processing_kwargs = {'min': 2, 'max': 26, 'which': 'reverse'} # arguments for the processing
swam.preprocess(type='trim',by = 'offset',**processing_kwargs)

# remove zero amplitude data
swam.preprocess(type='check_traces')

# plot selected data
swam.plot('geometry')
swam.plot('seismogram', amp_scale = 1, color = 'k')
swam.plot('FK')
swam.plot('spectra')
swam.plot('spectrogram')
swam.plot('SFR')

# perform wavefield transformation based on the phaseshift and fdbf methods
swam.transform(method = 'phaseshift')
swam.transform(method = 'fdbf')
swam.plot('FV', method = 'phaseshift')
swam.plot('FV', method = 'fdbf')

# %% VIEWER
# figure viewer
# accepted keys: ['seismogram','','spectrogram','spectra','FK','SFR','dispersionImage','FV', 'curve']
swam.gui_view() # seismogram as default

# %% INTERACTOR
# filter data in FK-domain
swam.gui_interact('FK', taper_length = 10000)

# pick dispersion curves in FV-domain
swam.gui_interact('FV')

swam.plot('curve')
swam.plot('pseudosection')

# automatic dispersion curve extraction using MOPA
swam.extract(method = 'MOPA')
swam.plot('curve', method = 'MOPA')

# automatic dispersion curve extraction using max
swam.extract(method = 'max')
swam.plot('curve', method = 'max')

# points_top, points_bot = swam.read_filter('FK')
# swam.apply_filter('FK', points_top,points_bot, procset = 'proc1')
#
# swam.plot('FK',procset = 'proc1')
# swam.plot('FK',procset = 'test')

#swam.preprocess(type='filter',by = 'FK',fname = '../data/syn_data/testing/FKfilter.txt')


# # # automatic dispersion curve extraction using trafo and max
# # # (INFO regarding a modification here: initially you could apply the max extraction method to
# # # both wavefield transformation methods and access the dispersion curves via method = '<trafo_type>_max'
# # # I changed it now so that you only store the data using the identifier method = 'max', analogue to the use of MOPA
# # # --> it's probably sufficient and less confusing and you can still decide to which trafo method you wish to apply it
# # swam.extract(method = 'max') # method here can be 'max' or the trafo method
# # swam.plot_curve(method = 'max')
