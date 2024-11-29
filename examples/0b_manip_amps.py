import sys
import copy
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(1, '../../swa')

from geometry import *
from utils import *
from _stream import SeismicStream

# %% Show and interact with the seismogram

# directories
prj_dir = '../data/testdata_ilaria/syn_data'
path2raw = os.path.join(prj_dir,'raw')
path2geom = f'{prj_dir}/geometry_test.csv'
ext = '.sgy' # shot file extension

# processing and plotting settings
settings = create_settings_dict(
                         zero_padding=True, freq_step=0.5,  # zero padding
                         normalize = True,local_max = True, # amplitude normalization
                         )


# get paths to shot files, survey geometry from geometry.csv
shot_files, source_coordinates, receiver_coordinates = read_geometry(path2geom)
path2sht = get_shotfiles_from_geometry(path2raw, shot_files, extension = ext, sort_ascending = False)

# stream object
stream = SeismicStream(path2sht[0][0], settings) # record

# show the seismogram
stream._plotSeismogram(amp_scale=1.5)
plt.show()

# interactive linear muting
stream._mute()

# show the seismogram
stream._plotSeismogram(amp_scale=1.5)
plt.show()

# linear move out
stream._lmo(vel = None,   # if vel is None a window will pop up where the vel can be estimated
            bulk_shift=0) # optional bulk shift
stream._plotSeismogram(amp_scale=1.5)
plt.show()

# select a subset
mintrace = 4
maxtrace = 12

trace_select = range(mintrace, maxtrace)
stream._select_traces(trace_select=trace_select)
stream._plotSeismogram(amp_scale=1.5)
plt.show()