"""
Converted from matlab_test.m
Simple test calling Light and saving result.
"""
import scipy.io
from Light import Light


def main():
    color = [0.2, 0.5, 0.7]
    percent = 50
    out_color = Light(color, percent)
    scipy.io.savemat('out_color.mat', {'out_color': out_color})


if __name__ == '__main__':
    main()
