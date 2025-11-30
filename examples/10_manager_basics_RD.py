from swa import *
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('Qt5Agg')

# %% Base operations with Manager classes

# directories
prj_dir = 'data/real_data/Cavezzo'    # I have changed the relative path to make the script work in the "swa" folder
path2raw = os.path.join(prj_dir,'raw')
path2geom = f'{prj_dir}/geom_file.csv'
ext = '.dat' # shot file extension

# processing and plotting settings
settings = create_settings(fmin=10, fmax=60,                  # frequency range
                         vmin=50, vmax=500, velstep=1)     # testing phase velocity range and step

# manager
swam = BaseManager(f'{prj_dir}/proc/10_manager_basics',
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
swam.select_data(sin=26, rep=3, inplace=True)

# removal of the last two channels
swam.preprocess(attr='trim',by = 'remove', ids = np.arange(46,48))

# resampling
swam.print_stats()
processing_kwargs = {'sampling_rate': 500} # sampling rate in Hz
swam.preprocess(attr='filter', by = 'resample',**processing_kwargs)
swam.print_stats()

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

swam.preprocess_streams(attr='filter', by = 'FK')