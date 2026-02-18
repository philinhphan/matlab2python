"""Shared helpers emitted into every converted file that uses load() or special MATLAB functions."""


def mat_to_dict(mat):
    """Clean scipy.io.loadmat output: remove metadata, squeeze arrays.

    scipy.io.loadmat wraps everything in extra dimensions and adds __header__,
    __version__, __globals__ keys. This function strips those and squeezes
    single-element arrays to scalars.
    """
    result = {}
    for k, v in mat.items():
        if k.startswith('__'):
            continue
        squeezed = v.squeeze()
        if squeezed.ndim == 0:
            result[k] = squeezed.item()
        else:
            result[k] = squeezed
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
