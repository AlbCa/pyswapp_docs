import os
import numpy as np
import pandas as pd
import re
import warnings

from collections.abc import Iterable

from _stream import SeismicStream
from utils import get_num_from_str, natural_sort


def create_geometry_from_sht(path2shts, rep=0, path2geom = 'geometry.csv'):
    """
    create a geometry.csv from shot files

    :param path2shts: path to shot files
    :param rep: number of max. repeated shots per shot point
    :param path2geom: path to geometry file
    """

    # read first file to get receiver x-coordinates and number of geophones
    stream0 = SeismicStream(path2shts[0])
    receiver = stream0.receiver
    ngeo = stream0.nchannels

    ncol = 7 + rep
    fmt = '%.3f,%.3f,%.3f,' + ','.join(['%d'] * (ncol - 3))

    geom = np.zeros((len(receiver), ncol))
    geom[:, 0] = receiver # x-coordinates
    geom[:, 3] = 1  # is geophone flag (1=True)

    # shot file indices (-1=no shot)
    for i in range(0, rep + 1):
        geom[:, 4 + i] = -1

    geom[:, -2] = 1  # first geophone (always 1, change for roll-along)
    geom[:, -1] = -1  # number of active geophones (-1 if no shot)

    for i in range(len(path2shts)):

        stream = SeismicStream(path2shts[i])
        name = stream.pre # file name
        sin = int(get_num_from_str(name)[0]) # get shot index number from file name
        source = stream.source # source x-coordinate

        # change flags if source coordinate already in geom
        if source in geom[:, 0]:

            id = np.where(geom[geom[:, 0] == source, 4:(4 + rep + 1)][0] == -1)[0]

            if len(id) > 0:
                geom[geom[:, 0] == source, 4 + id[0]] = sin
            else:
                geom[geom[:, 0] == source, 4] = sin

            geom[geom[:, 0] == source, -1] = ngeo

        # otherwise add new row for source
        else:
            row = np.zeros((1, ncol))
            row[0, 0] = source
            row[0, 3] = 0
            row[0, 4] = sin
            row[0, -1] = ngeo
            geom = np.vstack((geom, row))

    geom = geom[np.argsort(geom[:, 0])] # sort based on x-coordinate
    np.savetxt(path2geom, geom, fmt)
