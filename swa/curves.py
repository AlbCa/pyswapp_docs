"""python class for manipulating an Obspy stream"""
import numpy as np
from matplotlib.widgets import PolygonSelector
from matplotlib.offsetbox import AnchoredText

from .utils import *
from .curve import DispersionCurve

import warnings

# TODO improve the class, especially the interactive filtering etc

warnings.simplefilter(action='ignore', category=FutureWarning)

class CombineCurves:
    """combine dispersion curves and perform simple statistics"""

    def __init__(self):

        self.data = {}
        self.dc_mean = None

    def append(self,curve, xmid, source=None,color = 'b'):

        if xmid not in self.data.keys():
            self.data[xmid] = {}
            i = 0
        else:
            ids = [key for key in self.data[xmid].keys()]

            i = np.max(ids)+1

        self.data[xmid][i] = {}
        self.data[xmid][i] = {'data': curve,
                                         'data_filt': curve,
                                         'label': source,
                                         'color': color}

    @staticmethod
    def _plot_lambda_intervals(lam_min = 0.1, lam_max = 180,a_range = range(2,8)):
        """plot wavelength intervals (Olafsdottir, 2018)"""

        qmin = int(np.round((np.log(lam_min) / np.log(2) + 1 / 6) * 3 - 1))

        fig, ax = plt.subplots(figsize = (6,3))

        for i,a in enumerate(a_range):

            lam_eq = []
            lam_lo = []
            lam_up = []

            a_vec = []
            lam_max_bound = 0
            q = qmin

            while lam_max_bound <= lam_max:

                lam_eqi = 2 ** ((q - 1) / a)
                lam_min_bound = lam_eqi * (2 ** (-1 / (2 * a)))
                lam_max_bound = lam_eqi * (2 ** (1 / (2 * a)))

                lam_eq.append(lam_eqi)
                lam_lo.append(lam_min_bound)
                lam_up.append(lam_max_bound)
                a_vec.append(a)

                q+=1

            ax.plot(lam_up,a_vec, marker = '|',
                    color = 'k',zorder = 1)

            ax.scatter(lam_eq,a_vec, marker = 'o',
                    color = 'r',s=10,zorder = 2)

        ax.set_xlabel('wavelength (m)')
        ax.set_ylabel('a')
        ax.grid(linestyle = 'dotted')
        ax.invert_yaxis()
        ax.set_title('Wavelength intervals', fontweight = 'bold')
        plt.tight_layout()
        plt.show()

    @staticmethod
    def _dc2vec(data_dict):
        """convert dict containing all dcs to vector"""

        # Remove 'cmb' if present
        data_dict = {k: v for k, v in data_dict.items() if k != 'cmb'}

        lam_list = []
        vr_list = []

        for entry in data_dict.values():
            data = entry['data_filt'].data
            lam = np.asarray(data.lam)
            vr = np.asarray(data.vr)

            # Ensure matching shapes and exclude invalid/masked/zero values
            valid = (lam > 0) & np.isfinite(vr)
            lam_list.append(lam[valid])
            vr_list.append(vr[valid])

        if lam_list:
            lam_vec = np.concatenate(lam_list).reshape(-1, 1)
            vr_vec = np.concatenate(vr_list).reshape(-1, 1)
        else:
            lam_vec = np.empty((0, 1))
            vr_vec = np.empty((0, 1))

        return lam_vec, vr_vec

    @staticmethod
    def _binning(lam_vec, vel_vec, lam_min = 1, lam_max = 150, a=3, minvelerr=None, **kwargs):
        """combination of dispersion curves from SW measurements (Olafsdottir, 2018)"""

        # %% binning process
        # a ... log_a spaced intervals
        # qmin ... start wavelength of first wavelength interval
        # qmax ... start wavelength of last wavelength interval
        # lam_eq ... reference point of the qth interval
        # lam_lo, lam_up ... lower and upper bounds

        #minvelerr = kwargs.pop('minvelerr', None) # minimum error (in m/s)

        # define wavelength intervals
        lam_vec = lam_vec.flatten()
        vel_vec = vel_vec.flatten()

        qmin = int(np.round((np.log2(lam_min) + 1 / (2 * a)) * a - 1))

        lam_eq, vel_mean, vel_std = [], [], []

        q = qmin
        while True:
            lam_eqi = 2 ** ((q - 1) / a)
            lam_lo = lam_eqi * 2 ** (-1 / (2 * a))
            lam_up = lam_eqi * 2 ** (1 / (2 * a))

            if lam_lo > lam_max:
                break

            idx = (lam_vec >= lam_lo) & (lam_vec <= lam_up)
            if np.count_nonzero(idx) > 1:
                vels = vel_vec[idx]
                vel_mean.append(np.nanmean(vels))
                vel_std.append(np.nanstd(vels))
                lam_eq.append(lam_eqi)

            q += 1

        lam_eq = np.array(lam_eq)
        vel_mean = np.array(vel_mean)
        vel_std = np.array(vel_std)

        if minvelerr is not None:
            vel_std = np.maximum(vel_std, minvelerr)

        f_mean = vel_mean / lam_eq

        return f_mean, vel_mean, vel_std

    def _resample(self,data_dict, pmin = -np.inf, pmax = np.inf, pn = 30, **kwargs):
        """resample all curves"""

        data_dict = {k: v for k, v in data_dict.items() if k != 'cmb'}

        # Determine common min/max
        for v in data_dict.values():
            data = v['data_filt'].data
            pmin = max(pmin, np.min(data[kwargs.get('param', 'f')]))
            pmax = min(pmax, np.max(data[kwargs.get('param', 'f')]))

        for v in data_dict.values():
            v['data_filt'].resample(
                pmin=pmin,
                pmax=pmax,
                pn=pn,
                inplace=True,
                **kwargs
            )

    def _compute_mean(self,data_dict):
        """compute the mean of all curves"""

        data_dict = {k: v for k, v in data_dict.items() if k != 'cmb'}

        all_data = [v['data_filt'].data for v in data_dict.values()]
        df = pd.concat(all_data)
        grouped = df.groupby('f')

        return grouped.mean().index.values, grouped['vr'].mean().values, grouped['vr'].std().fillna(0).values

    def filter_all(self):
        """filter data points at several x-locations if necessary"""

        data = self.data
        for key in data.keys():
            self.filter_xmid(key)

    def filter_xmid(self, key):
        """filter data points at one x-locations if necessary"""

        data = self.data

        verts = [0]

        while len(verts) > 0:
            fig, ax = plt.subplots(figsize=(10, 6),constrained_layout = True)
            for i in data[key].keys():

                dc = data[key][i]['data_filt']
                dc.plot(axes = ax,
                             color = data[key][i]['color'],
                             label = data[key][i]['label'],
                             fontsize = 6,
                             show_orig=False)

            autoscale(ax,'y',margin=0.2)
            autoscale(ax,'x',margin=0.2)

            ax.set_title(f'Dispersion Curve Combination\nxmid = {key} m',fontweight = 'bold')
            text = '\n'.join((
                r'$\bf{Polygon \quad selector:}$',
                r'1. Draw a polygon to remove points within.',
                r'2. Close figure to update plot.',
                r'3. To stop: draw no polygons and close figure.'))
            at = AnchoredText(text,
                               loc='lower right', prop=dict(size=6), frameon=True,bbox_to_anchor=(1., 1.),
                       bbox_transform=ax.transAxes)
            ax.add_artist(at)

            selector = PolygonSelector(ax, lambda *args: None)
            plt.show()

            verts = selector.verts

            if len(verts) >= 3:

                for i in data[key].keys():

                    dc_tmp = data[key][i]['data_filt']
                    dc_tmp.markInvalid_by_poly(vertices=verts)
                    dc_tmp.dropInvalid(inplace=True)
                    data[key][i]['data_filt'] = dc_tmp

        self.data = data

    def combine_all(self, **kwargs):
        """combine curves for all xmid locations"""

        data = self.data
        for id,key in enumerate(data.keys()):
            self.combination(key,**kwargs)

    def combination(self, key, mode = 0, axes = None, show=True, outfile=None, **kwargs):
        """run combination of dispersion curves"""

        data = self.data

        xlim = kwargs.pop('xlim',[0,80])
        ylim = kwargs.pop('ylim',[0,800])

        if mode == 0:
            lam_vec, vel_vec = self._dc2vec(data[key])
            lam_min, lam_max = np.min(lam_vec),np.max(lam_vec)
            f_mean, vel_mean, vel_std = self._binning(lam_vec, vel_vec,
                                                    lam_min=lam_min,
                                                    lam_max=lam_max,
                                                    a = kwargs.pop('a',4))
        elif mode == 1:
            self._resample(data[key],
                           pmin = kwargs.pop('pmin',-np.inf),
                           pmax = kwargs.pop('pmax',np.inf),
                           pn = kwargs.pop('pn',30),
                           pspace = kwargs.pop('pspace','log'),
                           param = kwargs.pop('param','f'),
                           kind = kwargs.pop('kind','cubic'))
            f_mean, vel_mean, vel_std = self._compute_mean(data[key])

        else:
            f_mean, vel_mean, vel_std = self._compute_mean(data[key])

        dc_mean = DispersionCurve()
        dc_mean.init_data(freq=f_mean,vel=vel_mean,err=vel_std)
        self.data[key]['cmb'] = dc_mean

        # plot
        if show:
            if axes is None:
                fig, ax = plt.subplots(figsize=(6, 4))
            else:
                ax = axes

            for i in data[key].keys():
                if i != 'cmb':
                    dc = data[key][i]['data_filt']
                    dc.plot(axes=ax,
                                 color=data[key][i]['color'],
                                 label=None,
                                 show_orig=False)

            ax.errorbar(x=f_mean, y=vel_mean, yerr = vel_std, capsize = 2,capthick = 1.5,
                            color='k', elinewidth=1.5, label=r'$s_{v_r}$',linewidth = 0)
            ax.scatter(f_mean, vel_mean, marker="s", s=30, c='w', edgecolor='k',
                       linewidth=1.5, zorder=2, label=r'$\overline{v_r}$')

            ax.legend(loc='upper right', edgecolor = 'k', frameon = True)

            ax.set_xlim(xlim)
            ax.set_ylim(ylim)

            if axes is not None:
                return ax

            plt.tight_layout()

            if outfile:
                fig.savefig(outfile)

            plt.show()




