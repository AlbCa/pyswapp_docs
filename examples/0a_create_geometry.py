import sys
sys.path.insert(1, '../../swa')
from geometry import *
from utils import *

# %% Create and read the geometry.csv

# directories
prj_dir = '../data/testdata_ilaria/syn_data'
path2raw = os.path.join(prj_dir,'raw')
path2geom = f'{prj_dir}/geometry_test.csv'
ext = '.sgy' # shot file extension

# paths to the shot files
path2shts = [f.path for f in os.scandir(path2raw) if f.is_file()]
path2shts += path2shts
path2shts = natural_sort(path2shts)

# create geometry.csv
create_geometry_from_sht(path2shts, rep=0, path2geom=path2geom)

# get paths to shot files, survey geometry from geometry.csv
shot_files, source_coordinates, receiver_coordinates = read_geometry(path2geom)  # read geometry information
path2sht = get_shotfiles_from_geometry(path2raw, shot_files, extension=ext, sort_ascending=True)  # shot file location
