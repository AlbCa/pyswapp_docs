import sys
import matplotlib.pyplot as plt
import numpy as np
import pickle

sys.path.insert(1, '../../swa')

from utils import *
from _stream import SeismicStream
from _curve import Curve

# %% STEP 2: run tomographic like approach for each frequency

# directories
version = 'v6'
prj_dir = '../data/testdata_ilaria/syn_data/'
path2raw = '../../../data/Synthetic_data/resampled/'
path2geom = f'{prj_dir}/geometry_test.csv'
path2diffs = f"{prj_dir}/proc/{version}/tomo2d/phase_diffs"
path2dc = f"{prj_dir}/proc/{version}/tomo2d/dc"
path2plot = f'{prj_dir}/proc/{version}/plots/'

safe_makedirs(path2plot)

ext = '.sgy' # shot file extension

# processing and plotting settings
settings = create_settings_dict(
                         fmin=10, fmax=50,                  # frequency range
                         vmin=10, vmax=1000, velstep=1)     # testing phase velocity range and step


# get paths to shot files
path2sht = [f.path for f in os.scandir(path2raw) if f.is_file()]
path2sht = natural_sort(path2sht)
path2sht = [[f] for f in path2sht]

# file containing all phase differences per shots
with open(f"{path2diffs}/all_phase_diffs.pickle", "rb") as fp:
    all_phase_diffs = pickle.load(fp)

# define offset range
min_offset = 10
max_offset = 20

# regularization parameter
lam = 50
rel_err = 15/100

# recording parameters
rec0 = SeismicStream(path2sht[0][0], settings)      # record0
nshots = len(path2sht)                              # number of shots
nrec = len(rec0.receiver)                           # number of receivers
dx = np.mean(np.diff(rec0.receiver))                # receiver separataion
dt = rec0.dt                                        # sampling rate in s
npts = rec0.npts                                    # number of samples
fids = rec0._argfreq()

# frequency range
freq = recordParam2freq(dt,npts)
freq_sel = freq[fids]

# allocate space
phi_vel_all = np.zeros((nrec-1,len(freq_sel)))

for jj,f in enumerate(freq_sel):

    A = np.zeros((2*nshots*nrec-1,nrec-1)) # design matrix
    dphi = np.zeros((2*nshots*nrec-1,1)) # phase vector
    error = np.zeros((2*nshots*nrec-1,1)) # error vector
    iii = 0

    for kk in range(0, len(path2sht)):

        stream = SeismicStream(path2sht[kk][0], settings)

        # %% process forward shots
        # define offset range
        offset = stream.receiver[:-1] - stream.source  # signed offset vector
        oids = np.argwhere((offset >= min_offset) & (offset <= max_offset))[:, 0]

        # fill A and dphi
        for ii in oids:
            if all_phase_diffs[kk][jj,ii]<0:
                iii += 1
                A[iii,ii] = dx
                dphi[iii] = all_phase_diffs[kk][jj,ii]
                abs_err = rel_err * all_phase_diffs[kk][jj,ii]
                error[iii] = abs_err

        # %% process reverse shots
        #define offset range
        oids = np.argwhere((offset >= -max_offset) & (offset <= -min_offset))[:, 0]

        # fill A and dphi
        for ii in oids:
            if all_phase_diffs[kk][jj,ii]>0:
                iii += 1
                A[iii,ii] = -dx
                dphi[iii] = all_phase_diffs[kk][jj,ii]
                abs_err = rel_err * all_phase_diffs[kk][jj,ii]
                error[iii] = abs_err

    # solve equations
    #weights /= np.var(error)
    A = A[~np.all(A == 0, axis=1)]
    dphi = dphi[~np.all(dphi == 0, axis=1)].reshape((-1,))
    error = error[~np.all(error == 0, axis=1)].reshape((-1,))

    weights = 1/error**2
    w = np.diag(weights)
    phi_vel, phi_model = tomo2D_phasediff(lam=lam, f=f, A=A, dphi=dphi, w=w)
    phi_vel_all[:,jj] = phi_vel

# save dispersion curves
for i in range(len(phi_vel_all)):
    dc = Curve()
    dc._init_data(freq_sel, phi_vel_all[i,:], err = None)
    dc._save(path2dc, f'dc{i}', format = 'csv')


# %% plot result
vmin = 200
vmax = 500
xmids = rec0.receiver[:-1] + dx/2

fig,ax = plt.subplots(figsize=(8,6), constrained_layout = True)
for i in range(len(phi_vel_all)):
    curve = Curve()
    curve._init_data(freq_sel, phi_vel_all[i,:], err = None)

    curve._plotColumn(axes = ax,
                  xmid = xmids[i],
                  vmin = vmin, vmax = vmax,
                  cmap = 'viridis', y_value = 'f',
                  width = 0.5)

plot_colorBar(ax, vmin, vmax, cmap='viridis', orientation='vertical')
ax.set_xlim([rec0.receiver[0],rec0.receiver[-1]])
ax.set_ylim([5,50])

ax.set_title('Tomo 2D')
fig.savefig(os.path.join(path2plot,'tomo2d.png'))
plt.show()

# %% compare results
# min_offset = 3
# max_offset = 48
#
# xmid = int((48-3)/2+3)

# rec0_cp
# rec0._trim_by_offsets(min_offset, max_offset)
# rec0._fdbf()
# rec0._dcpicking(pck_mode='auto')
# f_fdbf = rec0._picks['auto'][0]['f']
# v_fdbf = rec0._picks['auto'][0]['v']
#
# v_tomo_ave = np.mean(phi_vel_all,axis=0)
# f_tomo_ave = freq_sel

# fig,ax = plt.subplots()
# rec0._plotDispersionImage(axes = ax)
# ax.plot(f_tomo_ave,v_tomo_ave, color = 'b', label = r'$tomo_{ave}$')
# ax.plot(f_tomo_ave,phi_vel_all[xmid,:],color = 'r', label = f'tomo at xmid = {xmid} m')
# ax.plot(f_fdbf,v_fdbf, color = 'k', label = f'fdbf at xmid = {xmid} m')
# ax.legend(loc = 'upper right')
# plt.show()
#
# # %% show results
# fig, ax = plt.subplots(3,1,figsize = (10,4), constrained_layout=True)
#
# for kk in range(0, len(path2sht)):
#     if kk == 0:
#         label = f'f={round(freq_sel[0])} Hz'
#     else:
#         label = None
#     ax[0].plot(range(nrec - 1), all_phase_diffs[kk][0,:], 'k.', label=label)
#
# ax[0].set_ylabel(r'$\Delta phase$ (rad)')
# ax[0].set_xlabel('x (m)')
# ax[0].set_xlim(rec0.receiver[0],rec0.receiver[-1])
# ax[0].legend(loc='lower right', edgecolor = 'k', frameon = True)
#
# ax[1].plot(range(nrec-1),phi_vel_all[:,0], '.-', label=f'f={round(freq_sel[0])} Hz')
# ax[1].plot(range(nrec-1),phi_vel_all[:,10], '.-', label=f'f={round(freq_sel[10])} Hz')
# ax[1].plot(range(nrec-1),phi_vel_all[:,20], '.-', label=f'f={round(freq_sel[20])} Hz')
# ax[1].plot(range(nrec-1),phi_vel_all[:,40], '.-', label=f'f={round(freq_sel[40])} Hz')
# ax[1].set_ylabel(r'$v_r$ (m/s)')
# ax[1].set_xlabel('x (m)')
# ax[1].set_xlim(rec0.receiver[0],rec0.receiver[-1])
# ax[1].legend(loc='lower right', edgecolor = 'k', frameon = True)
#
# im = ax[2].pcolor(range(nrec-1),freq_sel,phi_vel_all.T, vmin = 150, vmax = 500)
# cbar = fig.colorbar(im, ax=ax[2], label = r'$v_r$ (m/s)')
# ax[2].set_ylabel('f (Hz)')
# ax[2].set_xlabel('x (m)')
# plt.show()




