"""
Converted from Light.m
Adjust color brightness by percentage.
"""
import numpy as np


def Light(Col, Percent):
    """Return adjusted RGB color scaled by Percent.

    Col: iterable of 3 values in [0,1]
    Percent: scalar percentage (0-100)
    """
    Col = np.asarray(Col)
    R = 255 * Col[0]
    G = 255 * Col[1]
    B = 255 * Col[2]
    # MATLAB rounds and does an odd -1 and division; replicate exactly
    R = (round((R * Percent / 100) + round(255 - Percent / 100 * 255)) - 1) / 255
    G = (round((G * Percent / 100) + round(255 - Percent / 100 * 255)) - 1) / 255
    B = (round((B * Percent / 100) + round(255 - Percent / 100 * 255)) - 1) / 255
    out1 = [R, G, B]
    return out1


if __name__ == '__main__':
    # simple test
    print(Light([1, 0.5, 0], 50))
