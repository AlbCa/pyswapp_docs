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
prj_dir = '../data/testdata_ilaria/syn_data'
path2raw = os.path.join(prj_dir,'raw')
path2geom = f'{prj_dir}/geometry_test.csv'
path2fk = f'{prj_dir}/proc/fk_filter'
path2diffs = f"{prj_dir}/proc/phase_diffs"
ext = '.sgy' # shot file extension

# processing and plotting settings
settings = create_settings_dict(trafo = 'fdbf',             # transformation type
                         zero_padding=False, freq_step=0.5,  # zero padding
                         normalize = True,local_max = True, # amplitude normalization
                         picking = 'manual',                # picking mode ("manual" or "auto")
                         fmin=5, fmax=50,                  # frequency range
                         vmin=50, vmax=1000, velstep=1)     # testing phase velocity range and step


# get paths to shot files
path2sht = [f.path for f in os.scandir(path2raw) if f.is_file()]
path2sht = natural_sort(path2sht)
path2sht = [[f] for f in path2sht]

# file containing all phase differences per shots
with open(f"{path2diffs}/all_phase_diffs.pickle", "rb") as fp:
    all_phase_diffs = pickle.load(fp)

# define offset range for forward shots
min_offset_fw = 3
max_offset_fw = 1e6

# define offset range for reverse shots
min_offset_rw = -3
max_offset_rw = -1e6

# regularization parameter
lam = 20

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
    dphi = np.zeros((2*nshots*nrec-1)) # phase vector
    weights = np.ones((2*nshots*nrec-1)) # weight vector
    iii = 0

    for kk in range(0, len(path2sht)):

        stream = SeismicStream(path2sht[kk][0], settings)

        # %% process forward shots
        # define offset range
        offset = stream.receiver - stream.source        # signed offset vector
        omin = np.argmin(np.abs(offset - min_offset_fw))
        omax = np.argmin(np.abs(offset - max_offset_fw))
        oids = np.arange(omin, omax)

        # fill A and dphi
        for ii in oids:
            if all_phase_diffs[kk][jj,ii]<0:
                iii += 1
                A[iii,ii] = dx
                dphi[iii] = all_phase_diffs[kk][jj,ii]

        # %% process reverse shots
        # define offset range
        omin = np.argmin(np.abs(offset - min_offset_rw))
        omax = np.argmin(np.abs(offset - max_offset_rw))
        oids = np.arange(omin, omax)

        # fill A and dphi
        for ii in oids:
            if all_phase_diffs[kk][jj,ii]>0:
                iii += 1
                A[iii,ii] = dx
                dphi[iii] = all_phase_diffs[kk][jj,ii]

    # solve equations
    w = np.diag(weights)
    phi_vel, phi_model = tomo2D_phasediff(lam=lam, f=f, A=A, dphi=dphi, w=w)
    phi_vel_all[:,jj] = phi_vel

# save dispersion curves
for i in range(len(phi_vel_all)):
    dc = Curve()
    dc._init_data(freq_sel, phi_vel_all[i,:], err = None)
    dc._save(os.path.join(prj_dir,'dc'), f'dc{i}', format = 'csv')

# %% compare results
min_offset = 3
max_offset = 48

xmid = int((48-3)/2+3)

rec0._trim_by_offsets(min_offset, max_offset)
rec0._fdbf()
rec0._dcpicking(pck_mode='auto')
f_fdbf = rec0._picks['auto'][0]['f']
v_fdbf = rec0._picks['auto'][0]['v']

v_tomo_ave = np.mean(phi_vel_all,axis=0)
f_tomo_ave = freq_sel

fig,ax = plt.subplots()
ax.plot(f_tomo_ave,v_tomo_ave)
ax.plot(f_fdbf,v_fdbf)
plt.show()

# %% show results
fig, ax = plt.subplots(3,1,figsize = (10,4), constrained_layout=True)

for kk in range(0, len(path2sht)):
    if kk == 0:
        label = f'f={round(freq_sel[0])} Hz'
    else:
        label = None
    ax[0].plot(range(nrec - 1), all_phase_diffs[kk][0,:], 'k.', label=label)

ax[0].set_ylabel(r'$\Delta phase$ (rad)')
ax[0].set_xlabel('x (m)')
ax[0].set_xlim(rec0.receiver[0],rec0.receiver[-1])
ax[0].legend(loc='lower right', edgecolor = 'k', frameon = True)

ax[1].plot(range(nrec-1),phi_vel_all[:,0], 'k.-', label=f'f={round(freq_sel[0])} Hz')
ax[1].set_ylabel(r'$v_r$ (m/s)')
ax[1].set_xlabel('x (m)')
ax[1].set_xlim(rec0.receiver[0],rec0.receiver[-1])
ax[1].legend(loc='lower right', edgecolor = 'k', frameon = True)

im = ax[2].pcolor(range(nrec-1),freq_sel,phi_vel_all.T, vmin = 300, vmax = 600)
cbar = fig.colorbar(im, ax=ax[2], label = r'$v_r$ (m/s)')
ax[2].set_ylabel('f (Hz)')
ax[2].set_xlabel('x (m)')
plt.show()

