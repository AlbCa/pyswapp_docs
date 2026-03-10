from swa import *

# %% Create the geometry.csv from raw data if it exists

# directories
prj_dir = '../data/syn_data'
path2raw = os.path.join(prj_dir,'raw')
path2geom = f'{prj_dir}/geometry.csv'
ext = '.sgy' # shot file extension

# create geometry.csv
create_geometry(path2raw, path2geom=path2geom)
