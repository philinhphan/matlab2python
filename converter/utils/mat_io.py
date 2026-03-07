"""Shared helpers emitted into every converted file that uses load() or special MATLAB functions."""

import numpy as np


def _convert_value(val):
    """Recursively convert a numpy value from scipy.io.loadmat to a Python type."""
    if not isinstance(val, np.ndarray):
        return val

    # Structured array (MATLAB struct) → nested dict
    if val.dtype.names is not None:
        return _struct_to_dict(val)

    # Object array (MATLAB cell array) → Python list
    if val.dtype == object:
        return _cell_to_list(val)

    # String array → Python str
    if val.dtype.kind == 'U' or val.dtype.kind == 'S':
        squeezed = val.squeeze()
        if squeezed.ndim == 0:
            return str(squeezed)
        return str(squeezed)

    # Numeric scalar (1,1) → Python int/float
    squeezed = val.squeeze()
    if squeezed.ndim == 0:
        return squeezed.item()

    return squeezed


def _struct_to_dict(arr):
    """Convert a MATLAB struct (numpy structured array) to a nested Python dict."""
    squeezed = arr.squeeze()
    if squeezed.ndim == 0:
        # Single struct: extract each named field
        s = squeezed[()]
        return {name: _convert_value(s[name]) for name in arr.dtype.names}
    else:
        # Array of structs: convert each element
        result = []
        for item in squeezed.flat:
            result.append({name: _convert_value(item[name]) for name in arr.dtype.names})
        return result


def _cell_to_list(arr):
    """Convert a MATLAB cell array (numpy object array) to a Python list."""
    result = [_convert_value(elem) for elem in arr.flat]
    # Unwrap single-element list
    if len(result) == 1:
        return result[0]
    return result


def mat_to_dict(mat):
    """Clean scipy.io.loadmat output: remove metadata, recursively convert types.

    Handles MATLAB structs → dicts, cell arrays → lists, scalars → Python types.
    """
    result = {}
    for k, v in mat.items():
        if k.startswith('__'):
            continue
        result[k] = _convert_value(v)
    return result


def lighten_color(color, amount=0.5):
    """Lighten a matplotlib color by mixing with white.

    Equivalent to MATLAB's Light() custom function.
    amount=0 → original color, amount=1 → white.
    """
    import matplotlib.colors as mc
    import colorsys
    try:
        c = mc.cnames[color]
    except KeyError:
        c = color
    c = colorsys.rgb_to_hls(*mc.to_rgb(c))
    return colorsys.hls_to_rgb(c[0], 1 - amount * (1 - c[1]), c[2])


def subtightplot(n_rows, n_cols, idx, gap=(0.1, 0.05), marg_h=(0.1, 0.06), marg_w=(0.05, 0.05)):
    """Create a subplot with tight control over spacing.

    Equivalent to MATLAB's subtightplot().
    idx is 1-based (MATLAB convention), converted to 0-based internally.
    gap=(hspace, wspace), marg_h=(top_margin, bottom_margin),
    marg_w=(left_margin, right_margin).
    """
    import matplotlib.pyplot as plt
    import matplotlib.gridspec as gridspec
    gs = gridspec.GridSpec(
        n_rows, n_cols,
        hspace=gap[0],
        wspace=gap[1],
        top=1 - marg_h[0],
        bottom=marg_h[1],
        left=marg_w[0],
        right=1 - marg_w[1],
    )
    return plt.subplot(gs[idx - 1])  # MATLAB idx is 1-based
