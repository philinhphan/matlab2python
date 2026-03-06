"""
Converted from Darstellung_a_v_Diagramm_v2.m
Original MATLAB lines retained and translated. Plots vehicle speed vs acceleration.
"""
import numpy as np
import matplotlib.pyplot as plt
from utils import choose_mat_file


def smooth(x, frac, method='rloess'):
    """Simple moving average smoothing to approximate MATLAB smooth.

    CONVERSION NOTE: MATLAB's smooth with 'rloess' is a robust locally
    weighted regression. Here we approximate with a symmetric moving average
    using a window size proportional to frac fraction of the signal length.
    This is a heuristic replacement; tests may require adjustment.
    """
    n = max(3, int(len(x) * frac))
    if n % 2 == 0:
        n += 1
    # pad and convolve
    pad = n // 2
    x_padded = np.pad(x, pad, mode='edge')
    kernel = np.ones(n) / n
    sm = np.convolve(x_padded, kernel, mode='valid')
    return sm


def main():
    # NOTE: The MATLAB script used workspace variables Fzg__GesFzg_S and Fzg__GesFzg_S_X
    # These should be provided in the .mat file or set beforehand. We attempt to auto-load a .mat file.
    import scipy.io

    try:
        full_path = choose_mat_file('*.mat')
        data = scipy.io.loadmat(full_path)
        data = {k: v.squeeze() for k, v in data.items() if not k.startswith('__')}
    except FileNotFoundError:
        # If no .mat file available, create dummy data to avoid crashing.
        # CONVERSION NOTE: Original script cleared workspace at end; here we provide sample data.
        t = np.linspace(0, 10, 100)
        v = 20 + 2 * np.sin(t)
        data = {'Fzg__GesFzg_S': v, 'Fzg__GesFzg_S_X': t}

    # Preserve original variable names where possible
    v_vector = data.get('Fzg__GesFzg_S')
    zeit = data.get('Fzg__GesFzg_S_X')

    if v_vector is None or zeit is None:
        raise ValueError('Required variables Fzg__GesFzg_S or Fzg__GesFzg_S_X not found in .mat file')

    v_vector = np.asarray(v_vector)
    zeit = np.asarray(zeit)

    v_vector_kmh = 3.6 * v_vector

    fig1, ax1 = plt.subplots()
    ax1.plot(zeit, v_vector_kmh, color='r')
    ax1.set_title('Speed (km/h) over time')

    acc = np.diff(v_vector) / np.diff(zeit)
    acc_smooth = smooth(acc, 0.3, 'rloess')

    fig2, ax2 = plt.subplots()
    ax2.plot(zeit[1:], acc, color='r')
    ax2.plot(zeit[1:], acc_smooth)
    ax2.set_title('Acceleration over time')

    fig3, ax3 = plt.subplots()
    ax3.plot(v_vector_kmh[1:], acc, color='r')
    ax3.plot(v_vector_kmh[1:], acc_smooth)
    ax3.set_ylim([-2, 6])
    ax3.set_title('Acceleration vs Speed')

    # Build a_v array similar to MATLAB
    # MATLAB:
    # a_v(:,1) = v_vector_kmh;
    # a_v(2:end,2) = acc_smooth;
    a_v = np.zeros((len(v_vector_kmh), 2)) * np.nan
    a_v[:, 0] = v_vector_kmh
    a_v[1:, 1] = acc_smooth

    # sortrows by first column
    idx = np.argsort(a_v[:, 0])
    a_v = a_v[idx, :]

    plt.show()


if __name__ == '__main__':
    main()
