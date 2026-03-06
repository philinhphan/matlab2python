"""
Shared utilities for converted MATLAB -> Python code.
Contains mat_to_dict and subtightplot helpers used across converted files.
Translated comments where appropriate.
"""
import os
from pathlib import Path
import numpy as np
import scipy.io
import matplotlib.pyplot as plt


def mat_to_dict(mat):
    """Clean scipy.io.loadmat output: remove metadata, squeeze arrays.

    Returns a dict mapping variable names to NumPy arrays or scalars.
    """
    out = {}
    for k, v in mat.items():
        if k.startswith('__'):
            continue
        try:
            arr = np.array(v)
        except Exception:
            arr = v
        # squeeze arrays where possible
        try:
            if hasattr(arr, 'shape'):
                arr = np.squeeze(arr)
        except Exception:
            pass
        out[k] = arr
    return out


def subtightplot(n_rows, n_cols, idx, gap=(0.1, 0.05), marg_h=(0.1, 0.06), marg_w=(0.05, 0.05)):
    """Create a subplot with tighter spacing similar to MATLAB's subtightplot.

    Parameters:
        n_rows, n_cols: grid dimensions
        idx: 1-based subplot index (MATLAB style)
        gap: tuple(hspace, wspace)
        marg_h: tuple(top_margin, bottom_margin)
        marg_w: tuple(left_margin, right_margin)

    Returns:
        matplotlib.axes.Axes
    """
    import matplotlib.gridspec as gridspec
    gs = gridspec.GridSpec(n_rows, n_cols,
                           hspace=gap[0], wspace=gap[1],
                           top=1 - marg_h[0], bottom=marg_h[1],
                           left=marg_w[0], right=1 - marg_w[1])
    # MATLAB idx is 1-based
    ax = plt.subplot(gs[idx - 1])
    return ax


def choose_mat_file(pattern='*.mat', recursive=False, directory=None):
    """Auto-select a .mat file using glob. Replacement for uigetfile.

    Returns full path to selected file.
    Raises FileNotFoundError if no match.
    """
    import glob
    search_dir = directory if directory is not None else '.'
    path = os.path.join(search_dir, pattern)
    if recursive:
        files = sorted(glob.glob(path, recursive=True))
    else:
        files = sorted(glob.glob(path))
    if not files:
        raise FileNotFoundError(f'No files matching pattern: {path}')
    return files[0]
