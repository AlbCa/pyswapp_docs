from swa import *

# %% TOMOGRAPHIC LIKE APPROACH
# directories
prj_dir = '../data/syn_data'
path2raw = os.path.join(prj_dir,'raw')
path2geom = f'{prj_dir}/geometry_v2_test.csv'
ext = '.sgy' # shot file extension

procset = 'tomo2D' # processing set label

# processing and plotting settings
settings = create_settings(fmin=10, fmax=50,                  # frequency range
                         vmin=10, vmax=1000, velstep=1)     # testing phase velocity range and step

swam = Tomo2DManager(f'{prj_dir}/proc/3a_tomo2D',settings=settings, overwrite=True)

# load data from database based on procset label
#swam.load_procset('tomo2D')

# set a new procset label where you will store the processed data
swam.set_procset_label(procset)

# Retrieve subsets from data corresponding to forward and reverse shots
swam.prepare_streams(min_offset=2, max_offset=48, min_rec = 48)

# # # Apply preprocessing steps to the data (e.g., FK filtering based on existing filters)
# # FK_kwargs = {'fname':path2fk, # specify a file name from which FK filter should be imported
# #              'show':False,     # show the filtered FK spectrum
# #               }
# # swam.preprocess_streams(type='filter', by = 'FK', **FK_kwargs)

# # FK filtering interactively)
swam.gui_interact('filter','FK')

# Compute the phase differences of the processed data
swam.compute_phasediff()

# Run the tomo2D
swam.run(lam = 20, min_offset = 3, max_offset = 72, rel_err = 10/100)

# Process the dispersion curves
#swam.process_curves(type = 'smooth', method = 'tomo2D', kernel_size = 3)

# Plot the pseudosection
swam.plot('pseudosection', method = 'tomo2D', cmap='cividis',vmax=500)

# Save the dispersion curves
swam.save(procset=procset, method='tomo2D', dc_mode=0, format = 'csv')
