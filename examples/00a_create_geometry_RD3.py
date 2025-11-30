import sys
import os
nb_dir = os.path.dirname(os.path.abspath("__file__")) # get nb absolute path
prj_root = os.path.abspath(os.path.join(nb_dir, "../")) # set swa path
sys.path.append(prj_root) # add path
from swa import *
import matplotlib
matplotlib.use('Qt5Agg')

# %% Create and read the geometry.csv
# directories
prj_dir = '../data/real_data/Asolo'
path2raw = os.path.join(prj_dir,'L1')
path2geom = f'{prj_dir}/geometry_test_v4.csv'
ext = '.dat' # shot file extension

# paths to the shot files
path2shts = [f.path for f in os.scandir(path2raw) if f.is_file()]
#path2shts += path2shts
path2shts = natural_sort(path2shts)

# create geometry.csv
create_geometry(path2shts, path2geom=path2geom)

# get paths to shot files, survey geometry from geometry.csv
shot_files, source_coordinates, receiver_coordinates = read_geometry(path2geom)  # read geometry information
path2sht = get_shotfiles_from_geometry(path2raw, shot_files, extension=ext, sort_ascending=True)  # shot file location
