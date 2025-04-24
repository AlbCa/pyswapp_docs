
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
prj_dir = '../data/real_data/Moriago'    # I have changed the relative path to make the script work in the "swa" folder
path2raw = os.path.join(prj_dir,'ALL')
path2geom = f'{prj_dir}/geometry_test.csv'
ext = '.sg2' # shot file extension

procset = 'tomo2D'  # processing set label

# processing and plotting settings
settings = create_settings(fmin=5, fmax=40,                  # frequency range
                           vmin=100, vmax=1200, velstep=1)     # testing phase velocity range and step

swam = Tomo2DManager(f'{prj_dir}/proc/30a_tomo2D',path2raw=path2raw,path2geom=path2geom, settings=settings)

# load data from database based on procset label
#swam.load_procset('raw')


# Polarity switch for specific traces
shots = swam._sql.get_table('shots')
for ii in range(len(shots)):
    sin = shots.loc[ii, 'sin']
    rep = shots.loc[ii, 'rep']
    if shots.loc[ii, 'first_geophone'] == 1:
        swam.data[sin][rep]._st[53].data = -swam.data[sin][rep]._st[53].data
        swam.data[sin][rep]._st[57].data = -swam.data[sin][rep]._st[57].data
    elif shots.loc[ii, 'first_geophone'] == 38:
        swam.data[sin][rep]._st[7].data = -swam.data[sin][rep]._st[7].data
        swam.data[sin][rep]._st[10].data = -swam.data[sin][rep]._st[10].data
        swam.data[sin][rep]._st[20].data = -swam.data[sin][rep]._st[20].data
        swam.data[sin][rep]._st[51].data = -swam.data[sin][rep]._st[51].data        
    elif shots.loc[ii, 'first_geophone'] == 75:
        swam.data[sin][rep]._st[6].data = -swam.data[sin][rep]._st[6].data
        swam.data[sin][rep]._st[9].data = -swam.data[sin][rep]._st[9].data
        swam.data[sin][rep]._st[14].data = -swam.data[sin][rep]._st[14].data
        swam.data[sin][rep]._st[25].data = -swam.data[sin][rep]._st[25].data            
    else:
        swam.data[sin][rep]._st[30].data = -swam.data[sin][rep]._st[30].data
        swam.data[sin][rep]._st[36].data = -swam.data[sin][rep]._st[36].data
        swam.data[sin][rep]._st[40].data = -swam.data[sin][rep]._st[40].data
        swam.data[sin][rep]._st[49].data = -swam.data[sin][rep]._st[49].data    


# set a new procset label where you will store the processed data
swam.set_procset_label(procset)

# Retrieve subsets from data corresponding to forward and reverse shots
swam.prepare_streams(min_offset=15, max_offset=250, min_rec = 12)

# # Apply preprocessing steps to the data (e.g., FK filtering)
# FK_kwargs = {'manual': False,  # if manual is True: filter by picking
#              'fname': 'C:/Users/Ilaria/Documents/GitHub/swa/data/real_data/Moriago/dummy_filter_new2.txt',  # specify a file name to which picks should be saved or, if manual is False, from which FK filter should be imported
#              'show': False  # show the filtered FK spectrum  
#               }

swam.preprocess_streams(attr='filter', by = 'FK', fname = 'C:/Users/Ilaria/Documents/GitHub/swa/data/real_data/Moriago/dummy_filter_new2.txt') # **FK_kwargs)

# Compute the phase differences of the processed data
swam.compute_phasediff()

# Run the tomo2D
swam.run(lam = 100, min_offset = 15, max_offset = 250) #, rel_err = 15/100)

# Plot the pseudosection
swam.plot_pseusodsection(method='tomo2D')

# # Process the dispersion curves
# swam.process_curves(attr = 'smooth')

# # Plot the dispersion curves individually
# swam.plot_curves()

# # Save the dispersion curves
# swam.save_curves(procset=procset, method='tomo2D', dc_mode=0, format = 'csv')
