from swa import *

# %% TOMO2D
# directories
prj_dir = '../../data/real_data/Moriago'
path2raw = os.path.join(prj_dir,'raw')
path2geom = f'{prj_dir}/geometry.csv'
ext = '.sg2' # shot file extension

procset = 'tomo2D' # processing set label

# processing and plotting settings
settings = create_settings(fmin=5, fmax=100,                  # frequency range
                         vmin=10, vmax=1000, velstep=1)     # testing phase velocity range and step

swam = Tomo2DManager(f'{prj_dir}/proc/3a_tomo2D',
                     path2raw=path2raw,
                     path2geom=path2geom,
                     settings=settings,
                     database = f'{procset}.db')

# set a new procset label where you will store the processed data
swam.set_procset_label(procset)

# # load data from database based on procset label
# swam.load_procset(procset)

# Retrieve subsets from data corresponding to forward and reverse shots
swam.prepare_streams(min_offset=5, max_offset=1e6, min_rec = 12)

# FK filtering interactively)
swam.gui_interact('FK',use_windows=True)

# Compute the phase differences of the processed data
swam.compute_phasediff()

# Run the tomo2D
swam.run(lam = 10, min_offset = 5, max_offset = 1e6, abs_err = 0.5)

# Plot the pseudosection
swam.plot('pseudosection', method = 'tomo2D', cmap='cividis')

# Process the dispersion curves
swam.process_curves(type = 'smooth')

# Plot the pseudosection
swam.plot('pseudosection', method = 'tomo2D', cmap='cividis')

# Save the dispersion curves
swam.save(procset=procset, method='tomo2D', dc_mode=0, format = 'csv')


