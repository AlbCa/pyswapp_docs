from swa import *

# %% Create and read the geometry.csv
# directories
prj_dir = '../../data/real_data/Mannsworth'
path2raw = os.path.join(prj_dir,'raw1')
path2geom = f'{prj_dir}/geometry2.csv'
ext = '.sg2' # shot file extension

# create geometry.csv
create_geometry(path2raw, path2geom=path2geom)
