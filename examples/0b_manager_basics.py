import matplotlib.pyplot as plt

from swa import *
from plot_settings import *

# %% Base operations with Manager classes

# directories
prj_dir = '../data/syn_data'
path2raw = os.path.join(prj_dir,'raw')
path2geom = f'{prj_dir}/geometry_v2_test.csv'
ext = '.sgy' # shot file extension

# processing and plotting settings
settings = create_settings(fmin=10, fmax=50,                  # frequency range
                         vmin=10, vmax=1000, velstep=1)     # testing phase velocity range and step

# %% 1. Create a new project
# this will
# -create the project directory structure if it does not exist
# - copy raw data and geometry into the project directory if paths are provided

# manager
swam = BaseManager(f'{prj_dir}/proc/swa_v2/test', # project directory path
                   path2raw=path2raw,                       # optional, copy & per default rename data from path (outside project directory)
                   path2geom=path2geom,                     # optional, copy geom from path (outside project directory)
                   settings=settings,                       # optional, define settings for visualisations and processing
                   rename = False,                          # optional, rename copied raw data to preferred filename format, default value is False!
                   )

# load data from database based on existing procset label
swam.load_procset('raw')

# set a new procset label
procset = 'test' # processing set label
swam.set_procset_label(procset)

# select data
swam.select_data(sin=1, rep=1, inplace=True)

# preprocess the data
# trim by offset
processing_kwargs = {'min': 2, 'max': 10, 'which': 'reverse'} # arguments for the processing
swam.preprocess(attr='trim',by = 'offset',**processing_kwargs)

# remove zero amplitude data
swam.preprocess(attr='check_traces')

# plot selected data
swam.plot('geometry')
swam.plot('seismogram', amp_scale = 1, color = 'k')
swam.plot('FK')
swam.plot('spectra')
swam.plot('spectrogram')
swam.plot('SFR')

# perform wavefield transformation based on the phaseshift method
swam.transform(method = 'fdbf')
swam.plot('FV')

# %% VIEWER
# figure viewer
swam.gui_view()
swam.gui_view('FK')

# interactive figure viewer
swam.gui_interact()
swam.gui_interact('FV')

# plot picked dispersion curve
swam.plot_curve(method = 'fdbf')

# automatic dispersion curve extraction using MOPA
swam.extract(pck_mode='auto', method = 'MOPA')
swam.plot_curve(method = 'MOPA')

# automatic dispersion curve extraction using trafo and max
# (INFO:
# I changed the use of method here, to make it less confusing hopefully.
# method now only refers to the auto extraction method
# you don't have to combine the trafo method and the extraction method)
swam.extract(pck_mode='auto', method = 'max') # method here can be 'max' or the trafo method
swam.plot_curve(method = 'max')
