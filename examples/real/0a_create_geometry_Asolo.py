from swa import *

# %% Create and read the geometry.csv

for ext in ['dat']:
    # directories
    prj_dir = '../../data/real_data/AsoloL1'
    path2raw = os.path.join(prj_dir,f'raw/{ext}')
    path2geom = f'{prj_dir}/geometry.csv'

    # create geometry.csv
    create_geometry(path2raw, path2geom=path2geom)
