from swa import *
from plot_settings import *

# %% TOMOGRAPHIC LIKE APPROACH
# directories
prj_dir = '../../data/real_data/Moriago'
path2raw = os.path.join(prj_dir,'raw')
path2geom = f'{prj_dir}/geometry_raw.csv'
ext = '.sg2' # shot file extension

procset = 'tomo2D' # processing set label

# processing and plotting settings
settings = create_settings(fmin=10, fmax=40,                  # frequency range
                         vmin=10, vmax=1000, velstep=1)     # testing phase velocity range and step

swam = Tomo2DManager(f'{prj_dir}/proc/swa_v2/3a_tomo2D',path2raw=path2raw,path2geom=path2geom, settings=settings)

# load data from database based on procset label
swam.load_procset('tomo2D')

# set a new procset label where you will store the processed data
swam.set_procset_label(procset)

# swam.plot_streams(attr='seismogram', apply_to = 'cur', show_map = False)
#
# # Retrieve subsets from data corresponding to forward and reverse shots
# swam.prepare_streams(min_offset=3, max_offset=1e6, min_rec = 24)
#
# # Apply preprocessing steps to the data (e.g., FK filtering)
# FK_kwargs = {'manual': True   # if manual is True: filter by picking
#              # fname=path2fk, # specify a file name to which picks should be saved or,
#                               # if manual is False, from which FK filter should be imported
#              # show=False     # show the filtered FK spectrum
#               }
# swam.preprocess_streams(attr='filter', by = 'FK', cmap = 'Greys', **FK_kwargs)
#
# # Compute the phase differences of the processed data
# swam.compute_phasediff()

# Run the tomo2D
swam.run(lam = 100, min_offset = 20, max_offset = 100, rel_err = 30/100)

# Plot the pseudosection
swam.plot_pseusodsection(auto_method='tomo2D', cmap='cividis', vmin = 400, vmax = 700, fmax = 40, width = 5)

# # Process the dispersion curves
# swam.process_curves(attr = 'smooth')
#
# # Plot the dispersion curves individually
# swam.plot_curves()
#
# # Save the dispersion curves
# swam.save_curves(procset=procset, method='tomo2D', dc_mode=0, format = 'csv')
