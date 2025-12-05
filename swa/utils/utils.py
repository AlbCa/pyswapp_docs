import os
import re
from collections.abc import Iterable

import glob
import numpy as np
import pandas as pd

import logging
import shutil

from scipy import interpolate

supported_extensions = ['.sg2','.dat','.syn','.sgy','.syn']

# %% Logging
def create_logging(name):
    """ create logger """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch)

    return logger


def create_projectdir(prjdir = ''):
    """create project directory"""

    subdirs = ['01_data/raw','02_geom','03_proc','04_figs']
    for sd in subdirs:
        safe_makedirs(os.path.join(prjdir,sd))


def rename_files(path2raw, extension = '.sg2', prjdir = '', channel_nr = 1000, rename = False):
    """copy & optionally rename file for easier handling of geometry"""

    if not '.' in extension:
        extension = '.' + extension

    original = []
    for fname in os.listdir(path2raw):
        if fname.endswith(extension):
            original.append(fname)
    original = natural_sort(original)
    renamed = [f'Shotfile_{channel_nr+i}{extension}' for i in range(len(original))]

    # Copy and rename the copied file
    for fname_old,fname_new in zip(original,renamed):
        #path, name = os.path.split(fname)
        shutil.copy(os.path.join(path2raw,fname_old),
                    os.path.join(prjdir,f'01_data/raw/{fname_old}'))

        if rename:
            shutil.move(os.path.join(prjdir,f'01_data/raw/{fname_old}'),
                        os.path.join(prjdir,f'01_data/raw/{fname_new}'))


# %% file tools for reading/writing
def print_inventory(dct):
    """print the dictionary items to console"""
    for key in dct.keys():
        print("{}\t|\t{}".format(key, len(dct[key])))

# %% file tools
def get_num_from_str(string):
    """extract numbers from string"""

    p = '[\d]+[.,\d]+|[\d]*[.][\d]+|[\d]+'

    if re.search(p, string) is not None:
        return re.findall(p, string)


def natural_sort(l):
    """sort list based on numbers in ascending order"""
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
    return sorted(l, key=alphanum_key)

# TODO add data index (e.g., sin, rep, wid)
def read_filter(fin):
    """import existing filters from file"""

    points_top = {}
    points_bot = {}

    with open(fin, 'r') as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):

        parts = lines[i].strip().split('\t')

        # Expect lines like: t <npoints>   or   b <npoints>
        if parts[0] in ('t', 'b') and len(parts) == 2:
            label = parts[0]
            npoints = int(parts[1])

            # Collect the following npoints lines
            for j in range(i + 1, i + 1 + npoints):
                x, y = lines[j].strip().split('\t')

                x = float(x)
                y = float(y)

                if label == 't':
                    points_top[x] = y
                else:
                    points_bot[x] = y

            # Skip past the block
            i += 1 + npoints
        else:
            i += 1

    return points_top, points_bot

def write_filter(fout, points, key):
    """export filter to file"""

    if len(points) == 0:
        return

    # points is assumed to be a dict {x: y}
    x, y = zip(*sorted(points.items()))

    with open(fout, "w") as f:
        f.write(f"{key}\t{len(x)}\n")
        for xi, yi in zip(x, y):
            f.write(f"{xi:.4f}\t{yi:.4f}\n")

def filter_df2dict(df):

    if df.empty:
        return {},{}

    top = df[df['key'] == 't'].sort_values('x_value')
    bot = df[df['key'] == 'b'].sort_values('x_value')

    points_top = dict(zip(top['x_value'], top['y_value']))
    points_bot = dict(zip(bot['x_value'], bot['y_value']))

    return points_top, points_bot

def save2csv(outfile, freq, vel, err):
    """save dispersion curve in csv format"""

    f = open(outfile, 'w')
    f.write('#Frequency,Velocity,Velstd\n')
    for line in range(len(freq)):
        f.write('%.3f,%.3f,%.9f\n' %
                (freq[line],
                 vel[line],
                 err[line]))
    f.close()

def get_shotfiles_from_geometry(path2raw, shot_files, extension = '.sg2', sort_ascending = True):
    """get the paths to the shot files from the geometry.csv file"""
    fnames = []
    for fname in os.listdir(path2raw):
        if fname.endswith(extension):
            fnames.append(fname)
    fnames = natural_sort(fnames)

    if not sort_ascending:
        fnames = list(reversed(fnames))

    path2sht = []

    for sht in shot_files:
        if isinstance(sht, Iterable):
            sht_reps = []
            for i, fname in enumerate(fnames):
                sfn = str(re.findall(r'\d+', fname.replace(extension,''))[0])

                for rep in sht:
                    if rep ==sfn:
                        sht_reps.append(os.path.join(path2raw, fnames[i]))

            path2sht.append(sht_reps)
        else:
            for i, fname in enumerate(fnames):
                sfn = str(re.findall(r'\d+', fname.replace(extension,''))[0])

                if sht == sfn:
                    path2sht.append(os.path.join(path2raw, fnames[i]))

    return path2sht


def create_geometry(path2shts, path2geom = 'geometry.csv'):
    """
    create a geometry.csv from seismic shot files (.sgy and .sg2 file formats)

    This function can be used to convert the source and geophone coordinate information contained
    in the seismic raw data to the geometry file format. The geometry file is a csv file that stores
    an abstract representation of the survey layout, that can be optionally passed to some modules.
    Check out docs/geometry_file.pdf for a description of the format.

    Parameters
    ----------
    path2shts: list, paths to shot files
    path2geom: str, path to geometry file
    """

    if '.syn' in path2shts[0]:
        print('Seismic data with extension ".syn" does not contain geometry information.')
        return

    from swa.stream import SeismicStream

    geom = pd.DataFrame(columns=['x','y','z','geo','shot','first_geo','ngeo'])

    # add receiver stations first
    nids = 0
    for i in range(len(path2shts)):

        # seismic stream containing survey geometry
        stream = SeismicStream(path2shts[i])
        stream.read_data(path2shts[i], channel_nr=1001, extract_geometry = True)

        # shot parameters
        stream.set_shot_params()                    # set the shot parameters from the seismic data
        receiver = stream.receiver                  # geophone x-coordinates
        ngeo = stream.nchannels                     # number of geophones
        nids += ngeo

        if len(np.unique(receiver)) != ngeo:
            raise ValueError('Unique geophone coordinates does not match expected number of geophones. '
                             f'{len(np.unique(receiver))} != {ngeo}')

        df = pd.DataFrame({'x':receiver,
                           'y': 0,
                           'z': 0,
                           'geo': 1,
                           'shot': '-1',
                           'first_geo': 1,
                           'ngeo': -1})

        geom = pd.concat([geom, df])
        nids += ngeo

    geom = geom.drop_duplicates(subset=['x']).reset_index(drop=True)
    geom = geom.sort_values(by = 'x')
    geom.insert(0, 'id', np.arange(len(geom)))

    # add the shots
    for i in range(len(path2shts)):

        # seismic stream containing survey geometry
        stream = SeismicStream(path2shts[i])
        stream.read_data(path2shts[i], channel_nr=1001, extract_geometry = True)

        # shot parameters
        stream.set_shot_params()                    # set the shot parameters from the seismic data
        first_geo = stream.receiver[0]              # first geophone
        ngeo = stream.nchannels                     # number of geophones
        name = stream.pre                           # file name
        sin = str(int(get_num_from_str(name)[0]))   # numerical part of file
        source = stream.source                      # source x-coordinate
        nids += ngeo

        sid = np.where(geom.x == source)[0]
        first_geo_id = int(geom.id[geom.x == first_geo].item())
        first_geo_id += 1

        if len(sid) > 0:
            if geom.loc[sid[0],'shot'] == '-1':
                geom.loc[sid[0],'shot'] = sin
                geom.loc[sid[0], 'first_geo'] = str(first_geo_id)
                geom.loc[sid[0], 'ngeo'] = str(ngeo)
            else:
                geom.loc[sid[0],'shot'] += ';' + sin
                geom.loc[sid[0],'first_geo'] += ';' + str(first_geo_id)
                geom.loc[sid[0],'ngeo'] += ';' + str(ngeo)

        else:
            tmp_dict = {'x':source,
                       'y': 0,
                       'z': 0,
                       'geo': 0,
                       'shot': sin,
                       'first_geo': first_geo_id,
                       'ngeo': ngeo}

            df = pd.DataFrame([tmp_dict])
            geom = pd.concat([geom, df])
            geom.reset_index(drop=True, inplace=True)

    geom = geom.sort_values(by='x')
    geom = geom.drop(columns=['id'])
    geom['shot'].astype(str)
    geom['first_geo'].astype(str)
    geom['ngeo'].astype(str)
    geom.to_csv(path2geom, index=False, header=False)

def get_fileList(path2raw):
    """get the paths to the shot files from the geometry.csv file"""

    for ext in supported_extensions:
        fname_list = glob.glob(os.path.join(path2raw, '*' + ext))

        if len(fname_list) > 0:
            return fname_list, ext

    return None, None

def save2DC(outfile, parkseis_params, freq, vel, snr):
    """save dispersion curve in parkseis format"""

    receiver = parkseis_params['receiver']
    midpoint = parkseis_params['midpoint']
    source = parkseis_params['source']
    sn = parkseis_params['record_number']
    channel = parkseis_params['channel']

    f = open(outfile, 'w')
    f.write(f'>>Start\t{len(freq)}\n')
    for line in range(len(freq)):
        f.write('%s\t%.3f\t%.3f\t%d\n' %
                ('DATA',
                 freq[line],
                 vel[line],
                 snr[line]))
    f.write('>>End\n')
    f.write(f'X-Coord: {midpoint}\n')
    f.write(f'MidXYZ| {midpoint}| 0.000| 0.000\n')
    f.write(f'SourceXYZ| {source}| 0.000| 0.000\n')
    f.write(f'MidSTA| {channel[0]}| {channel[-1]}\n')
    f.write(f'MidXForXcoord| {receiver[0]}\n')
    f.write(f'XMinMax| {receiver[0]}| {receiver[-1]}\n')
    f.write('   Distance Unit: meter\n')
    f.write('TitleLabel|Dispersion\n')
    f.write('FRQLabel|Frequency (Hz)\n')
    f.write('PHSLabel|Phase Velocity (m/sec)\n')
    f.write('RTOLabel|Signal-To-Noise Ratio (S/N)\n')
    f.write(f'   Record No.      = {sn}\n')
    f.write('Data Type = Dispersion\n')
    f.close()


def read_DC_Park(fname):
    """read a dispersion curve file from ParkSEIS and store as csv with x,freq,phase_vel,snr columns"""

    f = open(fname)  # open file
    lines = f.readlines()  # lines in file

    lsp = lines[0].split()
    ndata = int(lsp[1])

    dat = np.zeros((ndata, 3))
    row = 0
    for line in lines[1:]:
        lsp = line.split()

        if (lsp[0] == 'DATA') & (len(lsp) == 4):
            dat[row, 0] = float(lsp[1])  # freq
            dat[row, 1] = float(lsp[2])  # phase vel
            dat[row, 2] = float(lsp[3])  # snr

            row += 1

        if lsp[0] == '>>End':
            print('end of line')
            break

    if ndata != len(dat):
        print('data size not matching')

    x = 0
    for line in lines[len(dat) + 2:]:

        lsp = line.split()
        if lsp[0] == 'X-Coord:':
            x = float(lsp[1])
            break

    return dat, x


def DC2csv(fpath,prjdir):
    """convert a dispersion curve file from ParkSEIS to a csv file"""

    dat,x = read_DC_Park(fpath)

    if os.path.isdir(prjdir + "0c_csv/") == False:
        os.mkdir(prjdir + "0c_csv/")

    path, fname = os.path.split(fpath)
    pre, ext = os.path.splitext(fname)
    outfile = prjdir + f"0c_csv/{pre}.csv"

    f = open(outfile,'w')
    f.write('#Frequency,Velocity\n')
    for line in range(len(dat)):
        f.write('%.9f,%.9f\n' %
                (dat[line,0],
                 dat[line,1]))
    f.close()

    return outfile,x


def read_DC_csv(fname):
    """read a dispersion curve file from a csv file"""
    dat = np.genfromtxt(fname,skip_header=1,delimiter=',')
    return dat,None


def safe_makedirs(*args):
    """safe generation of directories"""
    try:
        return os.makedirs(*args)
    except OSError:
        pass  # Ignore errors


def combine_dict(d1, d2):
    """combine two dictionaries"""

    for key, value in d2.items():
        if key in d1:
            d1[key].append(value)
        else:
            d1[key] = [value]
    return d1


# %% helper functions for waveform transformation
def nextpow2(A):
    """exponent of next higher power of 2 (see matlab)"""
    p = 1
    count = 0
    while p < abs(A):
        p *= 2
        count+=1
    return count,p

# %% Interpolation
def interp(x,y,xx,yerr = None, kind='cubic',**kwargs):
    """interpolate data"""

    f = interpolate.interp1d(x, y, kind=kind, **kwargs)
    yy = f(xx)

    if yerr is not None:
        ferr = interpolate.interp1d(x, yerr, kind=kind, **kwargs)
        yyerr = ferr(xx)
        return xx,yy,yyerr
    else:
        return xx, yy, None