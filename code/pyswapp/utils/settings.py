import pandas as pd
import numpy as np

# %% helper function to create settings for the SWA
def create_settings(
        zero_padding=False,
        freq_step=1,
        normalize = True,
        local_max = True,
        picking = 'manual',
        fmin=0,
        fmax=100,
        vmin=100,
        vmax=1000,
        velstep=1,
        SFR_time = 2,
        kmin = 0,
        kmax = None,
        normalize_power = True,
        local_max_power = False,
        window_length = 10 ,
        window_min_offset = -np.inf,
        window_max_offset = np.inf,
        window_move_increment = 1,
):
    """create settings dictionary"""
    dictionary = {"zero_padding": [bool(zero_padding)],
                     "df": [float(freq_step)],
                     "normalize_amps": [bool(normalize)],
                     "local_max": [bool(local_max)],
                     "fmin": [float(fmin)],
                     "fmax": [float(fmax)],
                     "vmin": [float(vmin)],
                     "vmax": [float(vmax)],
                     "velstep": [int(velstep)],
                     "kmin": [float(kmin)],
                     "kmax": [kmax],
                     "SFR_time": [float(SFR_time)],
                     "picking_mode": [str(picking)],
                     "normalize_power": [bool(normalize_power)],
                     "local_max_power": [bool(local_max_power)],
                     "window_length": [int(window_length)],
                     "window_min_offset": [float(window_min_offset)],
                     "window_max_offset": [float(window_max_offset)],
                     "window_move": [int(window_move_increment)]}

    df = pd.DataFrame.from_dict(dictionary)

    return df