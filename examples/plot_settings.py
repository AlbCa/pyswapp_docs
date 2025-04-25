from swa import *

# font
fs = 12
plt.rcParams['font.family'] = "sans-serif"
plt.rcParams['font.weight'] = 'regular'
plt.rcParams['font.size'] = fs
plt.rcParams['axes.labelsize'] = fs
plt.rcParams['axes.labelweight'] = 'regular'
plt.rcParams['xtick.labelsize'] = fs
plt.rcParams['ytick.labelsize'] = fs
plt.rcParams['legend.fontsize'] = fs

# legend
plt.rcParams['legend.edgecolor'] = 'k'
plt.rcParams['legend.framealpha'] =  0.75
#plt.rcParams['legend.edgewidth'] =  1.5

# fig
plt.rcParams["savefig.dpi"] = 300
plt.rcParams["savefig.bbox"] = "tight"
plt.rcParams["savefig.pad_inches"] = 0.1
plt.rcParams['grid.linestyle'] = 'dashed'
plt.rcParams['grid.color'] = 'lightgrey'
plt.rcParams['axes.facecolor'] = 'whitesmoke'
plt.rcParams['axes.linewidth'] = 1.5
#plt.rcParams['axes.titlepad'] = 4

# ticks
plt.rcParams['xtick.major.size'] = 4.5
plt.rcParams['xtick.major.width'] = 1.5
plt.rcParams['xtick.minor.visible'] = 'False'
plt.rcParams['ytick.major.size'] = 4.5
plt.rcParams['ytick.major.width'] = 1.5
plt.rcParams['ytick.minor.visible'] = 'False'

# %% MOPA
# directories
prj_dir = '../data/syn_data'
path2raw = os.path.join(prj_dir,'raw')
path2geom = f'{prj_dir}/geometry_v2_test.csv'
ext = '.sgy' # shot file extension