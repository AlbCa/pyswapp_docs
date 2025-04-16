
import sys
import os
nb_dir = os.path.dirname(os.path.abspath("__file__")) # get nb absolute path
prj_root = os.path.abspath(os.path.join(nb_dir, "../")) # set swa path
sys.path.append(prj_root) # add path
from swa import *
import matplotlib
matplotlib.use('Qt5Agg')

# %% TOMOGRAPHIC LIKE APPROACH
# directories
prj_dir = '../data/real_data/Cavezzo'    # I have changed the relative path to make the script work in the "swa" folder
path2raw = os.path.join(prj_dir,'raw')
path2geom = f'{prj_dir}/geom_file.csv'
ext = '.dat' # shot file extension

procset = 'tomo2D'  # processing set label

# processing and plotting settings
settings = create_settings(fmin=10, fmax=60,                  # frequency range
                           vmin=50, vmax=500, velstep=1)     # testing phase velocity range and step

swam = Tomo2DManager(f'{prj_dir}/proc/30a_tomo2D',path2raw=path2raw,path2geom=path2geom, settings=settings)

# load data from database based on procset label
#swam.load_procset('raw')

# set a new procset label where you will store the processed data
swam.set_procset_label(procset)

# Retrieve subsets from data corresponding to forward and reverse shots
swam.prepare_streams(min_offset=3, max_offset=1e6, min_rec = 12)

# removal of the last two channels
processing_kwargs = {'ids': np.arange(46,48)}  # arguments for the processing
swam.preprocess_streams(attr='trim',by = 'remove', apply_to = 'all',**processing_kwargs)

# resampling
swam.print_stats()
processing_kwargs = {'sampling_rate': 200} # sampling rate in Hz
swam.preprocess_streams(attr='filter', by = 'resample',**processing_kwargs)
swam.print_stats()

# Apply preprocessing steps to the data (e.g., FK filtering)
FK_kwargs = {'manual': True   # if manual is True: filter by picking
             # fname=path2fk, # specify a file name to which picks should be saved or,
                              # if manual is False, from which FK filter should be imported
             # show=False     # show the filtered FK spectrum
              }
swam.preprocess_streams(attr='filter', by = 'FK', **FK_kwargs)

# Compute the phase differences of the processed data
swam.compute_phasediff()

# Run the tomo2D
swam.run(lam = 50, min_offset = 10, max_offset = 30, rel_err = 15/100)

# Plot the pseudosection
swam.plot_pseusodsection(method='tomo2D')

# Process the dispersion curves
swam.process_curves(attr = 'smooth')

# Plot the dispersion curves individually
swam.plot_curves()

# Save the dispersion curves
swam.save_curves(procset=procset, method='tomo2D', dc_mode=0, format = 'csv')
