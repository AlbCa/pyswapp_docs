from swa import *

# %% Create and read the geometry.csv
# directories
prj_dir = '../data/syn_data'
path2raw = os.path.join(prj_dir,'raw')
path2geom = f'{prj_dir}/geometry_v2_test.csv'
ext = '.sgy' # shot file extension

# paths to the shot files
path2shts = [f.path for f in os.scandir(path2raw) if f.is_file()]
#path2shts += path2shts
path2shts = natural_sort(path2shts)

# create geometry.csv
create_geometry(path2shts, path2geom=path2geom)

# # get paths to shot files, survey geometry from geometry.csv
# shot_files, source_coordinates, receiver_coordinates = read_geometry(path2geom)  # read geometry information
# path2sht = get_shotfiles_from_geometry(path2raw, shot_files, extension=ext, sort_ascending=True)  # shot file location


# %% Create and read the geometry.csv
# directories
prj_dir = '../data/real_data/Moriago'
path2raw = os.path.join(prj_dir,'raw')
path2geom = f'{prj_dir}/geometry_raw.csv'
ext = '.sg2' # shot file extension

# paths to the shot files
path2shts = [f.path for f in os.scandir(path2raw) if f.is_file()]
path2shts = natural_sort(path2shts)

# create geometry.csv
create_geometry(path2shts, path2geom=path2geom)

# # get paths to shot files, survey geometry from geometry.csv
# shot_files, source_coordinates, receiver_coordinates = read_geometry(path2geom)  # read geometry information
# path2sht = get_shotfiles_from_geometry(path2raw, shot_files, extension=ext, sort_ascending=True)  # shot file location
