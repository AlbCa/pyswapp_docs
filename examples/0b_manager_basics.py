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
                   overwrite = False,                       # optional, overwrite database .db file if it already exists --> create new project data base
                   )


# %% 2. Load a created project
#swam = BaseManager(f'{prj_dir}/proc/test') # project directory path

# %% 3. interact with the data

# 3.1 load data from database based on existing procset label
# swam.load_procset('raw')

# 3.2 set a new procset label
procset = 'proc1' # processing set label
swam.set_procset_label(procset)

# 3.3 select data
swam.select_data(sin=1, rep=1, inplace=True)

# 3.4 preprocess data
# Cut traces outside of offset limits considering forward, reverse or both offset shots
swam.preprocess(type = 'trim', by = 'offset', min = 5, max = 1e6, which = 'both')

# # remove zero amplitude data
# swam.preprocess(type='check_traces')

# # Cut recording time
# swam.preprocess(type = 'trim', by = 'time', min = 0, max = 0.5)

# # Select traces with specified geophone separation
# swam.preprocess(type = 'trim', by = 'separation', dx=2)

# # Select traces within a window defined by window midpoint (xmid) and window length (number of traces)
# swam.preprocess(type = 'trim', by = 'window', xmid = 25, wlen = 20)

# # Select traces
# swam.preprocess(type = 'trim', by = 'select', trace_ids = [1,2,3])

# # Remove traces
# swam.preprocess(type = 'trim', by = 'remove', trace_ids = [1,2,3])

# # Apply bandpass, lowpass or highpass frequency filtering
# swam.preprocess(type = 'filter', by = 'frequency', min = 5, max = 20, filter_type = 'bandpass')

# # Apply linear move-out with specified velocity
# swam.preprocess(type = 'filter', by = 'lmo', velocity = 100, bulk_shift = 0)

# # Mute amplitudes of selected traces
# swam.preprocess(type = 'filter', by = 'mute', trace_ids = [1,2,3])

# # Reverse polarity of selected traces
# swam.preprocess(type = 'filter', by = 'reverse_polarity', trace_ids = [1,2,3])

# # Apply Hamming window
# swam.preprocess(type = 'filter', by = 'taper')

# %% 4. view data
# 4.1 Data viewer
# swam.gui_view()
#
# # 4.2 create single plot of currently selected data
# swam.plot('geometry')
# swam.plot('seismogram', amp_scale = 1, color = 'k')
# swam.plot('FK')
# swam.plot('spectra')
# swam.plot('spectrogram')
# swam.plot('SFR')
#
# # %% 5. wave field transformation
# # perform wavefield transformation based on the phaseshift and fdbf methods
# swam.transform(method = 'phaseshift')
# swam.transform(method = 'fdbf')
# swam.plot('FV', method = 'phaseshift')
# swam.plot('FV', method = 'fdbf')


# %% 6. Interactive viewer
# filter data in FK-domain
swam.gui_interact('filter',domain = 'FK')

# # filter data in TX-domain
swam.gui_interact('filter',domain = 'TX')

# pick dispersion curves (in FV (based on phaseshift or fdbf) or FK domain possible -> can be selected in app)
swam.gui_interact('pick')

# plot results for data picked with phaseshift transform
swam.plot('curve', method = 'phaseshift')
swam.plot('pseudosection', method = 'phaseshift')

# plot results for data picked with fdbf transform
swam.plot('curve', method = 'phaseshift')
swam.plot('pseudosection', method = 'phaseshift')

# plot results for data picked with FK transform
swam.plot('curve', method = 'phaseshift')
swam.plot('pseudosection', method = 'phaseshift')

# %% 7. automatic dispersion curve extraction
# automatic dispersion curve extraction using MOPA
swam.extract(method = 'MOPA', stopAtChi2 = 1, abs_err = 0.01, showResults =  True)
swam.plot('curve', method = 'MOPA')

# automatic dispersion curve extraction using max
swam.extract(method = 'max')
swam.plot('curve', method = 'max')

# save curves to disk
swam.save(method = 'fdbf')
swam.save(method = 'phaseshift')
swam.save(method = 'MOPA')
swam.save(method = 'max')