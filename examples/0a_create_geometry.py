from swa import *

# %% Create the geometry.csv from raw data if it exists

# directories
prj_dir = '../data/syn_data'
path2raw = os.path.join(prj_dir,'raw')
path2geom = f'{prj_dir}/geometry_v3.csv'
ext = '.sgy' # shot file extension

# paths to the shot files
path2shts = [f.path for f in os.scandir(path2raw) if f.is_file()]
path2shts = natural_sort(path2shts)

# create geometry.csv
create_geometry(path2shts, path2geom=path2geom)
