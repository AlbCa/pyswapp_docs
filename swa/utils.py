import os
import re
from collections.abc import Iterable

import numpy as np
import pandas as pd

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import *
from matplotlib.cm import ScalarMappable,get_cmap
from matplotlib.collections import PatchCollection
from matplotlib.patches import Rectangle

import warnings

# %% helper function to create settings for the SWA
def create_settings_dict(
                         trafo = 'phaseshift',
                         zero_padding=False, freq_step=1,
                         normalize = True,local_max = True,
                         picking = 'manual',
                         fmin=0, fmax=100, vmin=100,
                         vmax=1000, velstep=1, SFR_time = 2,
                         ):
    """create settings dictionary"""
    settings_dict = {"preproc":{"zero_padding": {"apply": bool(zero_padding),
                                                "df": freq_step},
                                "normalize_amps": {"apply": bool(normalize),
                                                    "local_max": bool(local_max)}},
                     "trafo": {"type": str(trafo),
                                 "fmin": float(fmin),
                                 "fmax": float(fmax),
                                 "vmin": float(vmin),
                                 "vmax": float(vmax),
                                 "velstep": int(velstep),
                                 "SFR_time": float(SFR_time)},
                     "picking": {"mode": str(picking)},}

    return settings_dict

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


def read_FKfilter(fin):
    """import existing FK filters from file"""
    f = open(fin, 'r')
    lines = f.readlines()
    points_dict= {}

    for i,line in enumerate(lines):

        line_split = line.split('\t')

        if len(line_split) == 3:
            key = line_split[1]
            npoints = int(line_split[2])
            points = np.loadtxt(fin,skiprows=i+1,max_rows=npoints,delimiter='\t')

            if key not in points_dict.keys():
                points_dict[key] = [points]
            else:
                points_dict[key].append(points)

    return points_dict

# %% helper function to read and create geometry files
def read_geometry(geometry):
    """read formikoj geometry files"""

    geom = pd.read_csv(geometry,delimiter=',',header=None)#np.loadtxt(geometry,delimiter=',')
    geom = np.asarray(geom)

    nchannels = np.unique(geom[geom[:,-1]!=-1,-1])[0].astype(int)
    receiver_coordinates = geom[geom[:,3]==1,0:3]

    if nchannels != len(receiver_coordinates):
        warnings.warn(f'Number of channels ({nchannels}) and '
              f'actual receiver count ({len(receiver_coordinates)}) not matching!')

    source_coordinates = geom[geom[:, 4] != -1,0:3]
    shot_files = geom[geom[:, 4] != -1, 4:-2]

    return shot_files, source_coordinates, receiver_coordinates

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
                sfn = int(re.findall(r'\d+', fname.replace(extension,''))[0])

                for rep in sht:
                    if rep ==sfn:
                        sht_reps.append(os.path.join(path2raw, fnames[i]))

            path2sht.append(sht_reps)
        else:

            for i, fname in enumerate(fnames):
                sfn = int(re.findall(r'\d+', fname.replace(extension,''))[0])

                if sht == sfn:
                    path2sht.append(os.path.join(path2raw, fnames[i]))

    return path2sht

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
    # TODO

    dat = np.genfromtxt(fname,skip_header=1,delimiter=',')
    head, tail = os.path.split(fname)

    if head.split('/')[-2] != 'cmb':
        try:
            x = float(head.split('/')[-2])
        except IndexError:
            return dat,0
        except ValueError:
            return dat,0
    else:
        x = float(tail.split('xmid')[1].replace('.csv',''))

    return dat,x


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


# %% helper functions for waveform transformation and inversion
def nextpow2(A):
    """exponent of next higher power of 2 (see matlab)"""
    p = 1
    count = 0
    while p < abs(A):
        p *= 2
        count+=1
    return count,p

def linear_LSQR(x,y,w=None):
    """estimate coefficients of a line y = k*x+phi0"""

    if w is None:
        W = np.diag(np.ones(len(x)))
    else:
        W = np.diag(w) # weighted LSQR

    A = np.vstack([-x, np.ones(len(x))]).T # design matrix

    N = np.transpose(A) @ W @ A
    beta = np.linalg.inv(N) @ np.transpose(A)@ W @ y

    k = beta[0]
    phi0 = beta[1]

    return k, phi0

def phase_response(x, k, phi0):
    """return the phase"""
    return -k * x + phi0


def compute_chi2(data, resp, error):
    """compute rms and chi^2"""
    misfit = data - resp
    error_weighted_misfit = np.abs(misfit) / error

    rms = np.sqrt(np.mean(np.abs(misfit) ** 2))
    rrms = np.sqrt(np.mean((np.abs(misfit)/np.abs(data)) ** 2))
    chi2 = np.mean(error_weighted_misfit ** 2)
    return rrms, chi2


def tomo2D_phasediff(lam,f,A,dphi,w):
    """
    Tomographic like approach (Barone et al., 2019)

    Args:
        lam: regularization strength
        f: frequency value of the analysis
        A: design matrix
        dphi: phase differences
        w: weight matrix

    """
    nm = len(A[0,:]) # corresponds to number of receivers
    G = np.zeros((nm-1,nm)) # first-order differential operator
    for i in range(nm-1):
        G[i,i] = 1
        G[i,i+1] = -1

    Ni = np.transpose(A) @ w @ A
    Mi = np.transpose(G) @  G

    m = np.linalg.inv(Ni + lam ** 2 * Mi) @ np.transpose(A) @ dphi
    phi_vel = -2*np.pi*f/m
    phi_model = A@m

    return phi_vel, phi_model


# %% physics
def wavenumber(f,vph):
    """compute wavenumber"""
    return 2*np.pi*f/vph


def phase_velocity(f,k):
    """compute phase velocity"""
    return 2*np.pi*f/k


def slowness(vel):
    """compute seismic slowness"""
    return 1./vel


def wavelength(f,vel):
    """compute wavelength"""
    return vel/f


def frequency(lam,vel):
    """compute frequency"""
    return vel/lam

def recordParam2freq(dt,npts):
    """compute frequency from recording parameters"""
    omega_fs = 2 * np.pi * 1 / dt
    omega = np.arange(npts) * (omega_fs / npts)
    return omega / (2 * np.pi)

def poisson(vp,vs,check = False):
    """compute poisson's ratio"""
    nu = np.ones_like(vp)
    for i, (vpi, vsi) in enumerate(zip(vp, vs)):

        nui = (vpi ** 2 - 2 * vsi ** 2) / (2 * (vpi ** 2 - vsi ** 2))
        nu[i] = nui

        if check:
            if vpi <= vsi:
                raise ValueError("vp must be greater than vs")
            if nui <= 0:
                raise ValueError("Poisson's ratio is negative.")
            if nui > 0.5:
                raise ValueError("Poisson's ratio is higher than 0.5.")

    return nu

def vpvs_ratio(vp,vs):
    """compute vp/vs ratio"""
    return vp/vs


def vs2vp(vs,nu):
    """compute vp from vs and nu"""
    return np.sqrt(2*(1-nu)/(1-2*nu))*vs


def vp2vs(vp,nu):
    """compute vs from vp and nu"""
    return np.sqrt((1-2*nu)/(2+(1-nu)))*vp


def estimate_vs_range(vr):
    """estimate the vs range from vr velocity (Cox and Teague, 2016)"""

    vs_min = np.min(vr)*1.04
    vs_max = np.max(vr)*1.16

    return (vs_min, vs_max)


def lorentzian_err(offsets, vel, f, nchannels = 24, dx = 1, **kwargs):
    """estimate dispersion curve error if only one dispersion curve is provided
       after O'Neill (2002)"""

    # some parameters
    maxerr = kwargs.pop('maxerr',0.4)  # Maximum error ratio (0.4 = error won't be higher than 40% of the velocity)
    minvelerr = kwargs.pop('minvelerr', 20)  # Minimum error (in m/s)
    a = kwargs.pop('a', 0.3)  # default a parameter (0.5 recommended by A. O'Neill,
    # 0.75 seems to fit better according to Pasquet) increase to tighten errorbars

    if offsets is not None:
        nchannels = len(offsets) # number of active receiver
        dx = abs(offsets[1]-offsets[0]) # number of receiver separation
    else:
        nchannels = nchannels
        dx = dx

    lam = wavelength(f,vel)
    fac = 10 ** (1 / np.sqrt(nchannels * dx))

    # error calculation
    avec = 1/vel - 1 / (2*vel/lam * (nchannels * fac) * dx)
    bvec = 1/vel + 1 / (2*vel/lam * (nchannels * fac) * dx)
    deltac = (10**(-a))*abs(1/avec - 1/bvec)

    if not isinstance(f, Iterable):
        vel = np.array([vel])
        deltac = np.array([deltac])

    delta_up = np.where(deltac > (maxerr * vel))[0]
    delta_lo = np.where(deltac < minvelerr)[0]

    if (len(delta_up) > 0) & isinstance(vel, Iterable):
        deltac[delta_up] = maxerr * vel[delta_up]

    if len(delta_lo) > 0:
        deltac[delta_lo] = minvelerr

    if isinstance(f, Iterable):
        return deltac
    else:
        return deltac[0]


# %% helper functions for plotting
def calculate_new_limit(fixed, dependent, limit):
    """Calculates the min/max of the dependent axis given
    a fixed axis with limits"""
    if len(fixed) > 2:
        mask = (fixed > limit[0]) & (fixed < limit[1])
        window = dependent[mask]
        if len(window) > 0:
            low, high = window.min(), window.max()
        else:
            low = dependent[0]
            high = dependent[-1]
    else:
        low = dependent[0]
        high = dependent[-1]
        if low == 0.0 and high == 1.0:
            # This is a axhline in the autoscale direction
            low = np.inf
            high = -np.inf
    return low, high


def get_xy(artist):
    """get the xy coordinates of a given artist"""
    if "Collection" in str(artist):
        x, y = artist.get_offsets().T
    elif "Line" in str(artist):
        x, y = artist.get_xdata(), artist.get_ydata()
    return x, y


def autoscale(ax=None, axis='y', margin=0.1):
    """autoscales the x or y axis of a given matplotlib ax object"""
    if ax is None:
        ax = plt.gca()
    newlow, newhigh = np.inf, -np.inf

    for artist in ax.collections + ax.lines:
        x, y = get_xy(artist)
        if axis == 'y':
            setlim = ax.set_ylim
            lim = ax.get_xlim()
            fixed, dependent = x, y
        else:
            setlim = ax.set_xlim
            lim = ax.get_ylim()
            fixed, dependent = y, x

        low, high = calculate_new_limit(fixed, dependent, lim)
        newlow = low if low < newlow else newlow
        newhigh = high if high > newhigh else newhigh

    margin = margin * (newhigh - newlow)

    setlim(newlow - margin, newhigh + margin)


def discrete_cmap(N, base_cmap=None):
    """Create an N-bin discrete colormap from the specified input map"""

    base = plt.cm.get_cmap(base_cmap)
    color_list = base(np.linspace(0, 1, N))
    cmap_name = base.name + str(N)
    return LinearSegmentedColormap.from_list(cmap_name, color_list, N)


def draw1DColumn(ax, x, val, thk=None, depth = None, width=1, vmin=1, vmax=1000,
                 cmap=None):
    """draw a 1D column based on thicknesses or depths"""

    if depth is None and thk is not None:
        depth = np.hstack((0., np.cumsum(thk), np.sum(thk) * 1.5))

    recs = []
    for i in range(len(val)):
        recs.append(Rectangle((x - width / 2., depth[i]), width, depth[i + 1] - depth[i]))

    pp = PatchCollection(recs)
    col = ax.add_collection(pp)

    pp.set_edgecolor(None)
    pp.set_linewidths(0.0)

    if cmap is not None:
        pp.set_cmap(cmap)

    pp.set_norm(Normalize(vmin, vmax))
    pp.set_array(np.array(val))
    pp.set_clim(vmin, vmax)

    return col


def plot_vphase(ax, val, f=None, lam=None, xmid=0, vmin=100, vmax=1000, y_value = 'lam',width = 1,**kwargs):
    """draw dispersion curve as 1D column"""

    cmap = kwargs.setdefault('cmap','viridis')

    if y_value == 'lam':

        if lam is not None:
            wavelength = lam
        elif f is not None:
            wavelength = val / f

        wavelength = np.array(wavelength)
        sort_idx = np.argsort(wavelength)
        wavelength = wavelength[sort_idx]
        values = np.array(val)[sort_idx]
        draw1DColumn(ax, xmid, values, depth=np.hstack((wavelength, wavelength[-1])),
                         cmap=cmap, vmin=vmin, vmax=vmax,width = width)
        ax.set_ylabel(r'$\lambda$ (m)')
    else:
        sort_idx = np.argsort(f)
        f = f[sort_idx]
        values = np.array(val)[sort_idx]
        draw1DColumn(ax, xmid, values, depth=np.hstack((f, f[-1])),
                         cmap=cmap, vmin=vmin, vmax=vmax, width=width)
        ax.set_ylabel(r'$f$ (Hz)')

    ax.set_xlabel('x (m)')

    ax.grid(True, linestyle=':')

    return ax, cmap


def plot_colorBar(ax,vmin,vmax,**kwargs):
    """create and plot a colorbar"""

    cmap = kwargs.setdefault('cmap', 'viridis')
    label = kwargs.setdefault('label','vr (m/s)')

    norm = plt.Normalize(vmin, vmax)
    sm = ScalarMappable(norm=norm, cmap=mpl.colormaps[cmap])
    cbMt = plt.colorbar(sm, ax=ax, **kwargs)
    cbMt.set_label(label)
