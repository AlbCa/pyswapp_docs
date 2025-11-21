from swa import *

# %% Windowing
# directories
prj_dir = '../data/syn_data'
path2raw = os.path.join(prj_dir,'raw')
path2geom = f'{prj_dir}/geometry_v2_test.csv'
ext = '.sgy' # shot file extension

procset = 'proc2' # processing set label

# processing and plotting settings
settings = create_settings(fmin=5, fmax=80,                  # frequency range
                         vmin=10, vmax=1000, velstep=1)     # testing phase velocity range and step

swam = MASW2DManager(f'{prj_dir}/proc/3c_MASW2D',path2raw=path2raw,path2geom=path2geom, settings=settings)

# load data from database based on procset label
#swam.load_procset('raw')

# set a new procset label
swam.set_procset_label(procset)

# Run moving window along data
swam.moving_window(minoffset = 3, maxoffset = 1e6, wlen = 24, wmove = 1)
swam.preprocess(type='check_traces')

# print(swam._sql.get_tables())
# print(swam._sql.get_trafo_labels('proc1'))

# transform data for all files (type='fdbf')
swam.transform(type='phaseshift')
swam.transform(type='fdbf')

# manual dc picking
swam.gui_interact('FV',use_windows=True)

# extract the dispersion curves automatically
swam.extract_curves(method = 'max')

swam.extract(method = 'MOPA', stopAtChi2 = 1, rel_err = 1/100, showResults = True)

# plot the corresponding pseudosections
swam.plot('pseudosection',method = 'phaseshift')
swam.plot('pseudosection',method = 'fdbf')
swam.plot('pseudosection',method = 'max')
swam.plot('pseudosection',method = 'MOPA')
