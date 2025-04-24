import sys
import os
nb_dir = os.path.dirname(os.path.abspath("__file__")) # get nb absolute path
prj_root = os.path.abspath(os.path.join(nb_dir, "../")) # set swa path
sys.path.append(prj_root) # add path
from swa import *
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('Qt5Agg')

# %% Base operations with Manager classes

# directories
prj_dir = '../data/real_data/Moriago'    # I have changed the relative path to make the script work in the "swa" folder
path2raw = os.path.join(prj_dir,'ALL')
path2geom = f'{prj_dir}/geometry_test.csv'
ext = '.sg2' # shot file extension

# processing and plotting settings
settings = create_settings(fmin=5, fmax=40,                  # frequency range
                         vmin=100, vmax=1200, velstep=1)     # testing phase velocity range and step

# manager
swam = BaseManager(f'{prj_dir}/proc/10_manager_basics',
                   path2raw=path2raw,
                   path2geom=path2geom,
                   settings=settings
                   )

# load data from database based on procset label
swam.load_procset('raw')

# Polarity switch for specific traces
shots = swam._sql.get_table('shots')
for ii in range(len(shots)):
    sin = shots.loc[ii, 'sin']
    rep = shots.loc[ii, 'rep']
    if shots.loc[ii, 'first_geophone'] == 1:
        swam.data[sin][rep]._pst[53].data = -swam.data[sin][rep]._pst[53].data
        swam.data[sin][rep]._pst[57].data = -swam.data[sin][rep]._pst[57].data
    elif shots.loc[ii, 'first_geophone'] == 38:
        swam.data[sin][rep]._pst[7].data = -swam.data[sin][rep]._pst[7].data
        swam.data[sin][rep]._pst[10].data = -swam.data[sin][rep]._pst[10].data
        swam.data[sin][rep]._pst[20].data = -swam.data[sin][rep]._pst[20].data
        swam.data[sin][rep]._pst[51].data = -swam.data[sin][rep]._pst[51].data        
    elif shots.loc[ii, 'first_geophone'] == 75:
        swam.data[sin][rep]._pst[6].data = -swam.data[sin][rep]._pst[6].data
        swam.data[sin][rep]._pst[9].data = -swam.data[sin][rep]._pst[9].data
        swam.data[sin][rep]._pst[14].data = -swam.data[sin][rep]._pst[14].data
        swam.data[sin][rep]._pst[25].data = -swam.data[sin][rep]._pst[25].data            
    else:
        swam.data[sin][rep]._pst[30].data = -swam.data[sin][rep]._pst[30].data
        swam.data[sin][rep]._pst[36].data = -swam.data[sin][rep]._pst[36].data
        swam.data[sin][rep]._pst[40].data = -swam.data[sin][rep]._pst[40].data
        swam.data[sin][rep]._pst[49].data = -swam.data[sin][rep]._pst[49].data    

# set a new procset label
procset = 'test' # processing set label
swam.set_procset_label(procset)


# %% Plotting

# select data
swam.select_data(sin=26, rep=2, inplace=True)

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
#fig,ax = plt.subplots(1,2,figsize=(10,5))
fig = plt.plot(figsize=(5,5))
swam.plot('dispersionImage', method = 'phaseshift') #, axes = ax[0])
#swam.plot('dispersionImage', method = 'fdbf', axes = ax[1])

plt.tight_layout()
plt.show()

swam.preprocess(attr='filter', by = 'FK', fname = 'C:/Users/Ilaria/Documents/GitHub/swa/data/real_data/Moriago/dummy_filter_new2.txt')
# plot the seismogram
swam.plot('seismogram')