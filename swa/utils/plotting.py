import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import *
from matplotlib.cm import ScalarMappable,get_cmap
from matplotlib.collections import PatchCollection
from matplotlib.patches import Rectangle

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


def plot_colorBar(ax,vmin,vmax, orientation='vertical', size=0.2, pad=None,**kwargs):
    """create and plot a colorbar"""
    from mpl_toolkits.axes_grid1 import make_axes_locatable

    divider = make_axes_locatable(ax)
    if orientation == 'horizontal':
        if pad is None:
            pad = 0.5
        cax = divider.append_axes("bottom", size=size, pad=pad)

    else:
        if pad is None:
            pad = 0.1
        cax = divider.append_axes("right", size=size, pad=pad)

    cmap = kwargs.setdefault('cmap', 'viridis')
    label = kwargs.setdefault('label','vr (m/s)')

    norm = plt.Normalize(vmin, vmax)
    sm = ScalarMappable(norm=norm, cmap=mpl.colormaps[cmap])
    fig = ax.figure
    cbar = fig.colorbar(sm, cax=cax, orientation = orientation, **kwargs)
    cbar.set_label(label)

    return cbar
