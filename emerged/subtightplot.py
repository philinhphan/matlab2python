"""
Converted from subtightplot.m
Creates a subplot with tighter spacing similar to MATLAB's subtightplot.
"""
import matplotlib.pyplot as plt


def subtightplot(m, n, p, gap=None, marg_h=None, marg_w=None, *args, **kwargs):
    if gap is None or (hasattr(gap, '__len__') and len(gap) == 0):
        gap = (0.01, 0.01)
    if marg_h is None or (hasattr(marg_h, '__len__') and len(marg_h) == 0):
        marg_h = (0.05, 0.05)
    if marg_w is None or (hasattr(marg_w, '__len__') and len(marg_w) == 0):
        marg_w = marg_h
    if isinstance(gap, (int, float)):
        gap = (gap, gap)
    if isinstance(marg_h, (int, float)):
        marg_h = (marg_h, marg_h)
    if isinstance(marg_w, (int, float)):
        marg_w = (marg_w, marg_w)

    gap_vert = gap[0]
    gap_horz = gap[1]
    marg_lower = marg_h[0]
    marg_upper = marg_h[1]
    marg_left = marg_w[0]
    marg_right = marg_w[1]

    # p may be scalar or iterable of positions (MATLAB allows merged subplots)
    if hasattr(p, '__len__'):
        # assume 1-based indices pair list
        positions = [int(x) for x in p]
        min_p = min(positions)
        max_p = max(positions)
    else:
        positions = [int(p)]
        min_p = int(p)
        max_p = int(p)

    # convert linear index to row/col assuming column-wise ordering
    def ind2sub(ncols, nrows, index):
        # MATLAB ind2sub([n,m],p) where n=columns, m=rows
        col = (index - 1) % ncols + 1
        row = (index - 1) // ncols + 1
        return col, row

    subplot_cols = 1 + (max_p - min_p)  # approximation
    subplot_rows = 1
    # single subplot dimensions
    height = (1 - (marg_lower + marg_upper) - (m - 1) * gap_vert) / m
    width = (1 - (marg_left + marg_right) - (n - 1) * gap_horz) / n

    # merged subplot dimensions (approximate for contiguous blocks)
    merged_height = subplot_rows * (height + gap_vert) - gap_vert
    merged_width = subplot_cols * (width + gap_horz) - gap_horz

    merged_bottom = (m - ((min_p - 1) // n + 1)) * (height + gap_vert) + marg_lower
    merged_left = ((min_p - 1) % n) * (width + gap_horz) + marg_left
    pos_vec = [merged_left, merged_bottom, merged_width, merged_height]

    ax = plt.subplot(111, position=pos_vec, *args, **kwargs)
    return ax


if __name__ == '__main__':
    import numpy as np
    fig = plt.figure()
    ax = subtightplot(2,2,1)
    ax.plot(np.arange(10))
    plt.show()
