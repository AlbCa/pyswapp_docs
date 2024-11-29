"""python class for manipulating an Obspy stream"""
import numpy as np
from matplotlib.widgets import PolygonSelector
from matplotlib.offsetbox import AnchoredText

from utils import *
from _curve import Curve

import warnings

warnings.simplefilter(action='ignore', category=FutureWarning)

# TODO: select a whole curve by clicking a single point -> highlight curve with option to delete it
# TODO: imbed processing of dc

class CombineCurves:
    """combine dispersion curves and perform simple statistics"""

    def __init__(self,prjdir=None, path2cmb = None):

        self.path2pck = prjdir
        if (prjdir is not None) and (path2cmb is None):
            self.path2cmb = prjdir.replace('/pck/','/cmb/')
        if path2cmb is not None:
            self.path2cmb = path2cmb

        self.settings = None
        self.all_datas_dict = {}
        self.dc_mean = None

    def _import_data(self):
        """import data sets and apply processing"""

        all_datas_dict = {}

        subfolders = []; xmids = []
        for f in os.scandir(self.path2pck):
            if f.is_dir():
                subfolders.append(f.path)
                xmids.append(f.name)

        subfolders = natural_sort(subfolders)
        xmids = natural_sort(xmids)

        for i,(xmid,subfolder) in enumerate(zip(xmids,subfolders)):

            all_datas_dict[xmid] = {}

            dir = os.path.join(subfolder, '0_csv')
            if os.path.isdir(dir):

                fnames = []
                for fname in os.listdir(dir):
                    fnames.append(os.path.join(dir, fname))
                fnames = natural_sort(fnames)

                color = plt.cm.viridis(np.linspace(0, 0.9, len(fnames)))

                for i, fname in enumerate(fnames):

                    all_datas_dict[xmid][i] = {}

                    head,tail = os.path.split(fname)

                    dc = Curve()
                    dc._read(fname)

                    all_datas_dict[xmid][i] = {'data': dc,
                                               'data_filt': dc,
                                              'label': tail,
                                              'color': color[i]}

        self.all_datas_dict = all_datas_dict

    def _append(self,curve,xmid,i = 0, source=None,color = 'b'):

        if xmid not in self.all_datas_dict.keys():
            self.all_datas_dict[xmid] = {}

        self.all_datas_dict[xmid][i] = {}
        self.all_datas_dict[xmid][i] = {'data': curve,
                                 'data_filt': curve,
                                 'label': source,
                                 'color': color}

    # if self.settings is not None:
    #     if self.settings['resample']['apply']:
    #         dc._resample(pmin=self.settings['resample']['min'],
    #                      pmax=self.settings['resample']['max'],
    #                      pn=self.settings['resample']['pn'],
    #                      pspace=self.settings['resample']['pspace'],
    #                      param=self.settings['resample']['param'],
    #                      kind=self.settings['resample']['kind'],
    #                      inplace=True)
    #     if self.settings['filter']['apply']:
    #         dc._markInvalid(pmin=self.settings['resample']['min'],
    #                         pmax=self.settings['resample']['max'],
    #                         param=self.settings['resample']['param'])
    #         dc._dropInvalid(inplace=True)
    #
    #     if self.settings['smooth']['apply']:
    #         dc._smooth(kernel_size=self.settings['smooth']['kernel_size'], inplace=True)



    @staticmethod
    def _plot_lambda_intervals(lam_min = 0.1, lam_max = 180,a_range = range(2,8)):
        """plot wavelength intervals"""

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

        data_dict = data_dict.copy()
        if 'cmb' in data_dict.keys():
            data_dict.pop('cmb')

        ndcs = len(data_dict)  # number of dispersion curves
        len_dcs_vec = np.zeros((ndcs, 1))  # npts of each dispersion curves

        for i in range(ndcs):
            npts = data_dict[i]['data_filt'].npts
            len_dcs_vec[i] = npts

        lam_data = np.zeros((ndcs, int(np.max(len_dcs_vec))))
        v_data = np.zeros((ndcs, int(np.max(len_dcs_vec))))

        for i in range(ndcs):
            data = data_dict[i]['data_filt'].data
            lam_data[i, range(len(data.lam))] = data.lam
            v_data[i, range(len(data.lam))] = data.vr

        sz1, sz2 = lam_data.shape
        lam_vec = np.transpose(lam_data).reshape(sz1 * sz2, 1)
        v_vec = np.transpose(v_data).reshape(sz1 * sz2, 1)

        lam_zeros = np.where(lam_vec > 0)[0]
        lam_vec = lam_vec[lam_zeros]
        v_vec = v_vec[lam_zeros]

        return lam_vec, v_vec

    @staticmethod
    def _binning(lam_vec, vel_vec, lam_min = 1, lam_max = 150, a=3, **kwargs):
        """combination of dispersion curves from SW measurements (Olafsdottir, 2018)"""

        # %% binning process
        # a ... log_a spaced intervals
        # qmin ... start wavelength of first wavelength interval
        # qmax ... start wavelength of last wavelength interval
        # lam_eq ... reference point of the qth interval
        # lam_lo, lam_up ... lower and upper bounds

        #minvelerr = kwargs.pop('minvelerr', None) # minimum error (in m/s)

        # define wavelength intervals
        qmin = int(np.round((np.log(lam_min) / np.log(2) + 1 / (2 * a)) * a - 1))

        lam_eq = []
        lam_lo = []
        lam_up = []
        lam_max_bound = 0

        qmax = qmin

        while lam_max_bound <= lam_max:

            lam_eqi = 2 ** ((qmax - 1) / a)
            lam_min_bound = lam_eqi * (2 ** (-1 / (2 * a)))
            lam_max_bound = lam_eqi * (2 ** (1 / (2 * a)))

            lam_eq.append(lam_eqi)
            lam_lo.append(lam_min_bound)
            lam_up.append(lam_max_bound)

            qmax += 1

        # compute statistics for data inside bins
        vel_mean = []
        vel_std = []
        lam_mean = []

        for i in range(len(lam_eq)):
            idx_inside = np.where((lam_vec <= lam_up[i]) & (lam_vec>= lam_lo[i]))[0]
            if len(idx_inside) > 1:
                vel_mean.append(np.nanmean(vel_vec[idx_inside]))
                vel_std.append(np.nanstd(vel_vec[idx_inside]))
                lam_mean.append(lam_eq[i])

        vel_mean = np.array(vel_mean)
        vel_std = np.array(vel_std)
        lam_mean = np.array(lam_mean)

        if 'minvelerr' in kwargs:
            delta_lo = np.where(vel_std < kwargs['minvelerr'])[0]
            if len(delta_lo) > 0:
                vel_std[delta_lo] = kwargs['minvelerr']

        f_mean = vel_mean/lam_mean

        return f_mean, vel_mean, vel_std

    def _resample(self,data_dict, pmin = -np.inf, pmax = np.inf, pn = 30, pspace = 'log', param = 'f', kind = 'cubic'):
        """resample all curves"""

        data_dict = data_dict.copy()
        if 'cmb' in data_dict.keys():
            data_dict.pop('cmb')

        # determine/check common range
        for i in data_dict.keys():
            dc_tmp = data_dict[i]['data_filt']
            data = dc_tmp.data
            pmin_tmp = np.min(data[param])
            pmax_tmp = np.max(data[param])

            if pmin_tmp > pmin:
                pmin = pmin_tmp

            if pmax_tmp < pmax:
                pmax = pmax_tmp

        for i in data_dict.keys():
            dc_tmp = data_dict[i]['data_filt']
            dc_tmp._resample(pmin,
                             pmax,
                             pn,
                             pspace,
                             param,
                             kind,
                             inplace=True)
            data_dict[i]['data_filt'] = dc_tmp

    def _compute_mean(self,data_dict):
        """compute the mean of all curves"""

        data_dict = data_dict.copy()
        if 'cmb' in data_dict.keys():
            data_dict.pop('cmb')

        ndcs = len(data_dict)  # number of dispersion curves
        len_dcs_vec = np.zeros((ndcs, 1))  # npts of each dispersion curves

        for i in range(ndcs):
            npts = data_dict[i]['data_filt'].npts
            len_dcs_vec[i] = npts

        f_data = np.zeros((ndcs, int(np.max(len_dcs_vec))))
        v_data = np.zeros((ndcs, int(np.max(len_dcs_vec))))

        for i in range(ndcs):
            data = data_dict[i]['data_filt'].data
            f_data[i, range(len(data.lam))] = data.f
            v_data[i, range(len(data.lam))] = data.vr

        vel_mean = np.mean(v_data, axis = 0)
        vel_std = np.std(v_data, axis = 0)

        return f_data[0,:],vel_mean,vel_std

    def _filter_all(self):
        """filter data points at several x-locations if necessary"""

        all_datas_dict = self.all_datas_dict
        for key in all_datas_dict.keys():
            self._filter_xmid(key)

    def _filter_xmid(self, key):
        """filter data points at one x-locations if necessary"""

        all_datas_dict = self.all_datas_dict

        verts = [0]

        while len(verts) > 0:
            fig, ax = plt.subplots(figsize=(10, 6),constrained_layout = True)
            for i in all_datas_dict[key].keys():

                dc = all_datas_dict[key][i]['data_filt']
                dc._plotdata(axes = ax,
                             color = all_datas_dict[key][i]['color'].reshape(1,-1),
                             label = all_datas_dict[key][i]['label'],
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

                for i in all_datas_dict[key].keys():

                    dc_tmp = all_datas_dict[key][i]['data_filt']
                    dc_tmp._markInvalid_by_poly(vertices=verts)
                    dc_tmp._dropInvalid(inplace=True)
                    all_datas_dict[key][i]['data_filt'] = dc_tmp

        self.all_datas_dict = all_datas_dict

    def _combine_all(self, **kwargs):
        """combine curves for all xmid locations"""

        all_datas_dict = self.all_datas_dict
        for key in all_datas_dict.keys():
            self._combination(key,**kwargs)

    def _combination(self, xmid, mode = 0, axes = None, show=False, outfile=None, save = True, **kwargs):
        """run combination of dispersion curves"""

        all_datas_dict = self.all_datas_dict
        key = xmid

        xlim = kwargs.pop('xlim',[0,80])
        ylim = kwargs.pop('ylim',[0,800])

        if mode == 0:
            lam_vec, vel_vec = self._dc2vec(all_datas_dict[key])
            lam_min, lam_max = np.min(lam_vec),np.max(lam_vec)
            f_mean, vel_mean, vel_std = self._binning(lam_vec, vel_vec,
                                                    lam_min=lam_min,
                                                    lam_max=lam_max,
                                                    a = kwargs.pop('a',4))
        if mode == 1:
            self._resample(all_datas_dict[key],
                           pmin = kwargs.pop('pmin',-np.inf),
                           pmax = kwargs.pop('pmax',np.inf),
                           pn = kwargs.pop('pn',30),
                           pspace = kwargs.pop('pspace','log'),
                           param = kwargs.pop('param','f'),
                           kind = kwargs.pop('kind','cubic'))
            f_mean, vel_mean, vel_std = self._compute_mean(all_datas_dict[key])

        dc_mean = Curve()
        dc_mean._init_data(freq=f_mean,vel=vel_mean,err=vel_std)
        self.all_datas_dict[key]['cmb'] = dc_mean

        if save:
            dc_mean._save(self.path2cmb, f'xmid{key}', 'csv')

        # plot
        if show:
            if axes is None:
                fig, ax = plt.subplots(figsize=(6, 4))
            else:
                ax = axes

            for i in all_datas_dict[key].keys():
                if i != 'cmb':
                    dc = all_datas_dict[key][i]['data_filt']
                    dc._plotdata(axes=ax,
                                 color=all_datas_dict[key][i]['color'].reshape(1, -1),
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




