import matplotlib.pyplot as plt

from swa import *
from plot_settings import *

# %% Base operations with Manager classes

# directories
prj_dir = '../data/syn_data'
path2raw = os.path.join(prj_dir,'raw')
path2geom = f'{prj_dir}/geometry_v2_test.csv'
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
swam.select_data(sin=2, rep=1, inplace=True)

# Other attributes for plotting of the stream data:
# 'spectrogram','spectra','spectrogramComposite','FK','SFR','dispersionImage','dispersionImageComposite'

# preprocess the data
# trim by offset
processing_kwargs = {'min': 2, 'max': 10, 'which': 'reverse'} # arguments for the processing
swam.preprocess(attr='trim',by = 'offset',**processing_kwargs)

swam.plot('geometry')
swam.plot('seismogram', amp_scale = 1, color = 'k')
#
# # processing_kwargs = {'manual': True,  'show':True}
# swam.preprocess(attr='filter',by = 'mute', color = 'k', show_map = False, **processing_kwargs)
#
# swam.plot('seismogram', amp_scale = 1, color = 'k')

# # remove zero amplitude data
# swam.preprocess(attr='check_traces')
#
# #perform wavefield transformation based on the phaseshift method
# swam.transform(method = 'phaseshift')

# # %% Plotting
# # plot the survey geometry
# fig, ax = plt.subplots(figsize = (6,1))
# swam.plot('geometry', axes = ax)
# plt.savefig('/home/Natalie/Documents/Projects/GIT/swa/data/syn_data/figures_EGU/BaseManager/geom.png')
#
# # plot the seismogram
# fig, ax = plt.subplots(figsize = (6,2))
# swam.plot('seismogram',show_map = False, amp_scale = 1, color = 'k',axes = ax)
# plt.savefig('/home/Natalie/Documents/Projects/GIT/swa/data/syn_data/figures_EGU/BaseManager/seismo.png')
#
# fig, ax = plt.subplots(figsize = (6,2))
# swam.plot('dispersionImage', cmap = 'Greys',axes = ax)
# plt.savefig('/home/Natalie/Documents/Projects/GIT/swa/data/syn_data/figures_EGU/BaseManager/disp.png')


# perform wavefield transformation based on the phaseshift method
# swam.transform(method = 'fdbf')
# swam.transform(method = 'phaseshift')
#
# swam.extract(pck_mode='manual', method = 'fdbf', cmap = 'Greys')
#
# # plot the dispersion images
# fig,ax = plt.subplots(1,2,figsize=(10,5))
# swam.plot('dispersionImage', method = 'phaseshift', axes = ax[0],cmap = 'Greys')
# swam.plot('dispersionImage', method = 'fdbf', axes = ax[1],cmap = 'Greys')
#
# plt.tight_layout()
# plt.show()