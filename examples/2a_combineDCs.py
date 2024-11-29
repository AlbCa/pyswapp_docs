import sys
import copy
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(1, '../../swa')

from geometry import *
from utils import *
from _stream import SeismicStream
from _curve import Curve
from _combineCurves import CombineCurves

# %% Wavefield transformation, dc picking and combination

# directories
prj_dir = '../data/testdata_ilaria/syn_data'
path2raw = os.path.join(prj_dir,'raw')
path2geom = f'{prj_dir}/geometry_test.csv'
path2disp = f'{prj_dir}/proc/dc_pick/test_cmb/picks/'
path2cmb = f'{prj_dir}/proc/dc_pick/test_cmb/cmb/'
ext = '.sgy' # shot file extension

# processing and plotting settings
settings = create_settings_dict(trafo = 'fdbf',             # transformation type
                         zero_padding=True, freq_step=0.5,  # zero padding
                         normalize = True,local_max = True, # amplitude normalization
                         picking = 'manual',                # picking mode ("manual" or "auto")
                         fmin=3, fmax=100,                  # frequency range
                         vmin=50, vmax=1000, velstep=1)     # testing phase velocity range and step


# get paths to shot files, survey geometry from geometry.csv
shot_files, source_coordinates, receiver_coordinates = read_geometry(path2geom)
path2sht = get_shotfiles_from_geometry(path2raw, shot_files, extension = ext, sort_ascending = False)

# define subset range
mintrace = 5
maxtrace = 20

# %% extract dispersion curves
for i in range(len(path2sht)):
    stream = SeismicStream(path2sht[i][0], settings) # record

    # select a subset of the data
    trace_select = range(mintrace, maxtrace)
    stream_sub = copy.deepcopy(stream)
    stream_sub._select_traces(trace_select=trace_select)

    # obtain the dispersion curve
    stream_sub._apply_trafo(save_dc = True,                # save the resulting pick file
                            do_pick = True,                # pick a dc in dispersion image
                            path2disp = path2disp,)        # path to dc


# %% combine dispersion curves
combCurves = CombineCurves(prjdir=path2disp,        # location where dcs are stored
                           path2cmb = path2cmb)     # location where combined dcs shall be stored

# import the data located in path2disp
combCurves._import_data()

# interactive filtering of data
combCurves._filter_all()

# combine all dispersion curves with same xmid
combCurves._combine_all(a=8,            # parameter controlling the wavelength interval
                        xlim = [5,80],  # xlimit for plotting
                        ylim = [50,400],# ylimit for plotting
                        save=True,     # save the combined dc
                        show=True)      # show the combined dc

# %% further manipulate the mean dispersion curve
# loop through xmids
for key in combCurves.all_datas_dict.keys():

    # mean dispersion curve after combination
    dc_mean = combCurves.all_datas_dict[key]['cmb']

    # smoothed curve
    dc_smooth = dc_mean._smooth(kernel_size=5, inplace=False)

    # resampling
    dc_resample = dc_mean._resample(pmin = 10, pmax = 60,   # parameter limits
                                    pn = 30,                # number of points
                                    pspace = 'log',         # linear or log scaling
                                    param = 'f',            # target parameter (can be 'f' or 'lam')
                                    kind = 'linear',        # interpolation kind
                                    inplace = False)

    # filtering
    dc_mean._markInvalid(pmin=10,  # min value
                         pmax=50,  # max value
                         param='f')# target parameter (can be 'f', 'vr', 'lam', 'k', 'err')
    dc_filter = dc_mean._dropInvalid(inplace=False)

    # show resulting curves
    fig, ax = plt.subplots(figsize=(10, 5), constrained_layout = True)
    dc_mean._plotdata(axes=ax,
                 color='k',
                 label='Mean',
                 show_orig=False)
    dc_smooth._plotdata(axes=ax,
                 color='red',
                 label='Mean, smooth',
                 show_orig=False)
    dc_resample._plotdata(axes=ax,
                 color='dodgerblue',
                 label='Mean, resampled',
                 show_orig=False)
    dc_filter._plotdata(axes=ax,
                 color='goldenrod',
                 label='Mean, filtered',
                 show_orig=False)
    ax.set_xlim([0,100])
    plt.show()
