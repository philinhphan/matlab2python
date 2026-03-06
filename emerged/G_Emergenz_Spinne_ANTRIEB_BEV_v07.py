"""
Converted from emergence/G_Emergenz_Spinne_ANTRIEB_BEV_v07.m
Creates spider (radar) plot summarizing Emergenz per vehicle character.
"""
import os
import numpy as np
import scipy.io
import matplotlib.pyplot as plt
from utils import mat_to_dict


def G_Emergenz_Spinne_ANTRIEB_BEV_v07(Par):
    Mic_Pos_Name = Par['Mic_Pos_Name']
    Name_Messung_Plot = f"{Par['Name_Messung_Plot']} {Mic_Pos_Name}"
    Name_Emergenz_save = f"{Par['Name_Emergenz_save']}_{Mic_Pos_Name}"
    save_path = os.path.join('Emergenz', Name_Emergenz_save)

    data = scipy.io.loadmat(os.path.join(save_path, 'Emergenz_Verteilung.mat'))
    data = mat_to_dict(data)
    # load Zielkurven
    raw = scipy.io.loadmat('Emergenz_Zielkurven_v2.mat')
    ziel = mat_to_dict(raw)

    plot_max = True
    plot_median = True
    ziel_fahrzeug_charakter = Par.get('ziel_fahrzeug_charakter', 1)

    Emergenz_Array_Max = data.get('Emergenz_Array_Max')
    Emergenz_Array_Max_Abgl = Emergenz_Array_Max.copy()
    Emergenz_Array_Max_Abgl_Max = np.full((4,4), np.nan)
    Emergenz_Array_Max_Abgl_Median = np.full((4,4), np.nan)

    v = Par['v']
    id_langsam = np.where(np.array(v) <= 30)[0]
    id_stadt = np.where((np.array(v) > 30) & (np.array(v) <= 80))[0]
    id_land = np.where((np.array(v) > 80) & (np.array(v) <= 120))[0]
    id_bab = np.where(np.array(v) >= 130)[0]

    Anzahl_FBereiche = int(ziel.get('Anzahl_FBereiche', 3))

    for fb in range(1, Anzahl_FBereiche+1):
        if fb == 1:
            toleranz_ziel = 1
            zielkurven = ziel['Zielkurven_0_1250Hz_Heulen']
        elif fb == 2:
            toleranz_ziel = 1
            zielkurven = ziel['Zielkurven_1250_4000Hz_Pfeifen']
        elif fb == 3:
            toleranz_ziel = 0.5
            zielkurven = ziel['Zielkurven_4000Hz_Piepsen']
        else:
            toleranz_ziel = 1
            zielkurven = ziel['Zielkurven_0_1250Hz_Heulen']

        for i in range(0, Emergenz_Array_Max.shape[0]):
            emergenz_messwert = Emergenz_Array_Max[i, fb-1]
            pos_messwert = 8.0
            j = 1
            while j < 6:
                if emergenz_messwert > zielkurven[i, j-1] + toleranz_ziel:
                    pos_messwert = pos_messwert - 0.5
                    if (j < 5) and (emergenz_messwert > zielkurven[i, j] - toleranz_ziel):
                        pos_messwert = pos_messwert - 0.5
                    if (j == 5) and (emergenz_messwert > zielkurven[i, j-1] + 2 * toleranz_ziel):
                        pos_messwert = pos_messwert - 0.5
                j += 1
            Emergenz_Array_Max_Abgl[i, fb-1] = pos_messwert

        if id_langsam.size != 0:
            Emergenz_Array_Max_Abgl_Max[0, fb-1] = np.nanmin(Emergenz_Array_Max_Abgl[id_langsam, fb-1])
            Emergenz_Array_Max_Abgl_Median[0, fb-1] = np.nanmedian(Emergenz_Array_Max_Abgl[id_langsam, fb-1])
        if id_stadt.size != 0:
            Emergenz_Array_Max_Abgl_Max[1, fb-1] = np.nanmin(Emergenz_Array_Max_Abgl[id_stadt, fb-1])
            Emergenz_Array_Max_Abgl_Median[1, fb-1] = np.nanmedian(Emergenz_Array_Max_Abgl[id_stadt, fb-1])
        if id_land.size != 0:
            Emergenz_Array_Max_Abgl_Max[2, fb-1] = np.nanmin(Emergenz_Array_Max_Abgl[id_land, fb-1])
            Emergenz_Array_Max_Abgl_Median[2, fb-1] = np.nanmedian(Emergenz_Array_Max_Abgl[id_land, fb-1])
        if id_bab.size != 0:
            Emergenz_Array_Max_Abgl_Max[3, fb-1] = np.nanmin(Emergenz_Array_Max_Abgl[id_bab, fb-1])
            Emergenz_Array_Max_Abgl_Median[3, fb-1] = np.nanmedian(Emergenz_Array_Max_Abgl[id_bab, fb-1])

    # Create spider plot (radar)
    # CONVERSION NOTE: openfig('.fig') cannot be loaded. Recreate spider plot programmatically.
    fig = plt.figure()
    ax = fig.add_subplot(111, polar=True)
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)

    # Draw concentric target circles
    angles = np.linspace(0, 2*np.pi, 101)
    ax.plot(angles, 4*np.ones_like(angles), '--', linewidth=2.5, color=np.array([132,60,12])/255)
    ax.plot(angles, 5*np.ones_like(angles), '--', linewidth=2.5, color=np.array([197,90,17])/255)
    ax.plot(angles, 6*np.ones_like(angles), '--', linewidth=2.5, color=np.array([237,125,49])/255)
    ax.plot(angles, 7*np.ones_like(angles), '--', linewidth=2.5, color=np.array([244,177,131])/255)
    ax.plot(angles, 8*np.ones_like(angles), '--', linewidth=2.5, color='k')
    angles_small = np.linspace(0, 2*np.pi, 51)
    ax.plot(angles_small, (8 - ziel_fahrzeug_charakter) * np.ones_like(angles_small), 'go', linewidth=5)

    legend_text = ['E-Antrieb "dominant"','E-Antrieb "präsent"','E-Antrieb "dezent"','E-Antrieb "leise"','E-Antrieb "unhörbar"','Fahrzeug Emergenz-Ziel']

    # Plot slices if available
    plot_color = 'b'
    ct = 1
    if id_langsam.size != 0:
        if plot_max:
            angles_segment = np.linspace(np.pi, np.pi/2, Emergenz_Array_Max_Abgl_Max.shape[1])
            ax.plot(angles_segment, Emergenz_Array_Max_Abgl_Max[0, :], ':o', linewidth=5, color=plot_color)
            legend_text.append(f"{Name_Messung_Plot}\n- Maximale Emergenz")
            ct += 1
        if plot_median:
            angles_segment = np.linspace(np.pi, np.pi/2, Emergenz_Array_Max_Abgl_Median.shape[1])
            ax.plot(angles_segment, Emergenz_Array_Max_Abgl_Median[0, :], '-s', linewidth=6, color=plot_color)
            legend_text.append(f"{Name_Messung_Plot}\n- Mediane Emergenz")
            ct += 1
    if id_stadt.size != 0:
        if plot_max:
            angles_segment = np.linspace(np.pi/2, 2*np.pi/20, Emergenz_Array_Max_Abgl_Max.shape[1])
            ax.plot(angles_segment, Emergenz_Array_Max_Abgl_Max[1, :], ':o', linewidth=5, color=plot_color)
            ct += 1
        if plot_median:
            angles_segment = np.linspace(np.pi/2, 2*np.pi/20, Emergenz_Array_Max_Abgl_Median.shape[1])
            ax.plot(angles_segment, Emergenz_Array_Max_Abgl_Median[1, :], '-s', linewidth=6, color=plot_color)
            ct += 1
    if id_land.size != 0:
        if plot_max:
            angles_segment = np.linspace(-2*np.pi/20, -np.pi/2, Emergenz_Array_Max_Abgl_Max.shape[1])
            ax.plot(angles_segment, Emergenz_Array_Max_Abgl_Max[2, :], ':o', linewidth=5, color=plot_color)
            ct += 1
        if plot_median:
            angles_segment = np.linspace(-2*np.pi/20, -np.pi/2, Emergenz_Array_Max_Abgl_Median.shape[1])
            ax.plot(angles_segment, Emergenz_Array_Max_Abgl_Median[2, :], '-s', linewidth=6, color=plot_color)
            ct += 1
    if id_bab.size != 0:
        if plot_max:
            angles_segment = np.linspace(-2*np.pi/20-np.pi/2, -np.pi, Emergenz_Array_Max_Abgl_Max.shape[1])
            ax.plot(angles_segment, Emergenz_Array_Max_Abgl_Max[3, :], ':o', linewidth=5, color=plot_color)
            ct += 1
        if plot_median:
            angles_segment = np.linspace(-2*np.pi/20-np.pi/2, -np.pi, Emergenz_Array_Max_Abgl_Median.shape[1])
            ax.plot(angles_segment, Emergenz_Array_Max_Abgl_Median[3, :], '-s', linewidth=6, color=plot_color)
            ct += 1

    # Radial boundary lines
    ax.plot(np.full(9, np.pi/2), np.arange(0,9), 'k', linewidth=5)
    ax.plot(np.zeros(9), np.arange(0,9), 'k', linewidth=5)
    ax.plot(np.full(9, np.pi), np.arange(0,9), 'k', linewidth=5)
    ax.plot(np.full(9, -np.pi/2), np.arange(0,9), 'k', linewidth=5)

    plt.legend(legend_text, loc='upper right', fontsize=14)

    # Save
    fig.savefig(os.path.join(save_path, 'Emergenz_Spinne.png'), dpi=300, bbox_inches='tight')
    plt.close('all')

    scipy.io.savemat(os.path.join(save_path, 'Emergenz_Spinne.mat'), {'Emergenz_Array_Max_Abgl': Emergenz_Array_Max_Abgl})


if __name__ == '__main__':
    Par = {'Mic_Pos_Name':'VL_li','Name_Emergenz_save':'test','Name_Messung_Plot':'test','v':[10,20,30],'ziel_fahrzeug_charakter':1}
    try:
        G_Emergenz_Spinne_ANTRIEB_BEV_v07(Par)
    except Exception as e:
        print('Test run failed (expected if .mat files missing):', e)
