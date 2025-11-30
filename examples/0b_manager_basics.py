from swa import *
import matplotlib
matplotlib.use('Qt5Agg')

# %% Base operations with Manager classes

# directories
prj_dir = 'data/syn_data'    # I have changed the relative path to make the script work in the "swa" folder
path2raw = os.path.join(prj_dir,'raw')
path2geom = f'{prj_dir}/geometry_v2.csv'
ext = '.sgy' # shot file extension

# processing and plotting settings
settings = create_settings(fmin=10, fmax=50,                  # frequency range
                         vmin=10, vmax=1000, velstep=1)     # testing phase velocity range and step

# manager
swam = BaseManager(f'{prj_dir}/proc/swa_v2/3b_MASW2D',
                   path2raw=path2raw,
                   path2geom=path2geom,
                   settings=settings
                   )

# load data from database based on procset label
swam.load_procset('raw')

# set a new procset label
procset = 'test' # processing set label
swam.set_procset_label(procset)

# select data
swam.select_data(sin=1, rep=1, inplace=True)

# %% Plotting
# plot the survey geometry
swam.plot('geometry')

# plot the seismogram
swam.plot('seismogram')

# Other attributes for plotting of the stream data:
# 'spectrogram','spectra','spectrogramComposite','FK','SFR','dispersionImage','dispersionImageComposite'

# preprocess the data
# trim by offset
processing_kwargs = {'min': 10, 'max': 1e6} # arguments for the processing
swam.preprocess(attr='trim',by = 'offset',**processing_kwargs)

# remove zero amplitude data
swam.preprocess(attr='check_traces')

swam.load_procset(procset)

# perform wavefield transformation based on the phaseshift method
swam.transform(method = 'phaseshift')

# perform wavefield transformation based on the phaseshift method
swam.transform(method = 'fdbf')

# plot the dispersion images
fig,ax = plt.subplots(1,2,figsize=(10,5))
swam.plot('dispersionImage', method = 'phaseshift', axes = ax[0])
swam.plot('dispersionImage', method = 'fdbf', axes = ax[1])

plt.tight_layout()
plt.show()