from collections.abc import Iterable
import numpy as np

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


def poisson(vp,vs):
    """compute poisson's ratio"""
    vp = np.asarray(vp)
    vs = np.asarray(vs)

    return (vp ** 2 - 2 * vs ** 2) / (2 * (vp ** 2 - vs ** 2))


def vpvs_ratio(vp, vs):
    """compute vp/vs ratio"""
    return vp / vs


def vs2vp(vs, nu):
    """compute vp from vs and nu"""
    return vs*np.sqrt(2 * (1 - nu) / (1 - 2 * nu))


def vp2vs(vp, nu):
    """compute vs from vp and nu"""
    return vp / ( np.sqrt(2 * (1 - nu) / (1 - 2 * nu)))
#
#
# def estimate_vs_range(vr):
#     """estimate the vs range from vr velocity (Cox and Teague, 2016)"""
#
#     vs_min = np.min(vr)*1.04
#     vs_max = np.max(vr)*1.16
#
#     return (vs_min, vs_max)


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
