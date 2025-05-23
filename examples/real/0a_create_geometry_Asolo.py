from swa import *

# %% Create and read the geometry.csv

for ext in ['sgy']:
    # directories
    prj_dir = '../../data/real_data/AsoloL1'
    path2raw = os.path.join(prj_dir,f'raw/{ext}')
    path2geom = f'{prj_dir}/geometry_{ext}.csv'

    # paths to the shot files
    path2shts = [f.path for f in os.scandir(path2raw) if f.is_file()]
    #path2shts += path2shts
    path2shts = natural_sort(path2shts)

    # create geometry.csv
    create_geometry(path2shts, path2geom=path2geom)
