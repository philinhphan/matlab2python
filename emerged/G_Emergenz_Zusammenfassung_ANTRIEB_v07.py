"""
Converted from emergence/G_Emergenz_Zusammenfassung_ANTRIEB_v07.m
Summary across two microphone positions (ZF = Zusammenfassung).
"""
import os
import numpy as np
import scipy.io
import matplotlib.pyplot as plt
from utils import mat_to_dict


def G_Emergenz_Zusammenfassung_ANTRIEB_v07(Par):
    Mic_Pos_Name = Par['Mic_Pos_Name']
    Mic_Pos_Name_ZF = Par['Mic_Pos_Name_ZF']
    Name_Emergenz_save = Par['Name_Emergenz_save']
    Name_Emergenz_save_ZF = f"{Par['Name_Emergenz_save']}_{Mic_Pos_Name_ZF}"
    save_path_ZF = os.path.join('Emergenz', Name_Emergenz_save_ZF)
    os.makedirs(save_path_ZF, exist_ok=True)
    Name_Messung_Plot_ZF = f"{Par['Name_Messung_Plot']} {Mic_Pos_Name_ZF}"

    ziel_fahrzeug_charakter = Par.get('ziel_fahrzeug_charakter', 1)
    plot_max = True
    plot_median = True

    # Load per-vehicle analyses
    path1 = os.path.join('Emergenz', f"{Name_Emergenz_save}_{Mic_Pos_Name[0]}", 'Emergenz_Spinne.mat')
    path2 = os.path.join('Emergenz', f"{Name_Emergenz_save}_{Mic_Pos_Name[1]}", 'Emergenz_Spinne.mat')
    raw1 = scipy.io.loadmat(path1)
    raw2 = scipy.io.loadmat(path2)
    Par_Fzg_1 = mat_to_dict(raw1)
    Par_Fzg_2 = mat_to_dict(raw2)

    Emergenz_Array_Max = np.maximum(Par_Fzg_1['Emergenz_Array_Max'], Par_Fzg_2['Emergenz_Array_Max'])
    Emergenz_Array_Max_Abgl_Max = np.minimum(Par_Fzg_1['Emergenz_Array_Max_Abgl_Max'], Par_Fzg_2['Emergenz_Array_Max_Abgl_Max'])
    Emergenz_Array_Max_Abgl_Median = np.minimum(Par_Fzg_1['Emergenz_Array_Max_Abgl_Median'], Par_Fzg_2['Emergenz_Array_Max_Abgl_Median'])

    v = 10 * np.unique(np.concatenate([Par_Fzg_1['id_langsam'], Par_Fzg_2['id_langsam'], Par_Fzg_1['id_stadt'], Par_Fzg_2['id_stadt'], Par_Fzg_1['id_land'], Par_Fzg_2['id_land'], Par_Fzg_1['id_bab'], Par_Fzg_2['id_bab']]))
    id_langsam = np.unique(np.concatenate([Par_Fzg_1['id_langsam'], Par_Fzg_2['id_langsam']]))
    id_stadt = np.unique(np.concatenate([Par_Fzg_1['id_stadt'], Par_Fzg_2['id_stadt']]))
    id_land = np.unique(np.concatenate([Par_Fzg_1['id_land'], Par_Fzg_2['id_land']]))
    id_bab = np.unique(np.concatenate([Par_Fzg_1['id_bab'], Par_Fzg_2['id_bab']]))

    # Recreate spider figure
    fig = plt.figure()
    ax = fig.add_subplot(111, polar=True)
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)

    angles = np.linspace(0, 2*np.pi, 101)
    ax.plot(angles, 4*np.ones_like(angles), '--', linewidth=2.5, color=np.array([132,60,12])/255)
    ax.plot(angles, 5*np.ones_like(angles), '--', linewidth=2.5, color=np.array([197,90,17])/255)
    ax.plot(angles, 6*np.ones_like(angles), '--', linewidth=2.5, color=np.array([237,125,49])/255)
    ax.plot(angles, 7*np.ones_like(angles), '--', linewidth=2.5, color=np.array([244,177,131])/255)
    ax.plot(angles, 8*np.ones_like(angles), '--', linewidth=2.5, color='k')
    angles_small = np.linspace(0, 2*np.pi, 51)
    ax.plot(angles_small, (8 - ziel_fahrzeug_charakter) * np.ones_like(angles_small), 'go', linewidth=5)

    legend_text_max = ['E-Antrieb "dominant"','E-Antrieb "präsent"','E-Antrieb "dezent"','E-Antrieb "leise"','E-Antrieb "unhörbar"','Fahrzeug Emergenz-Ziel']

    ct = 1
    plot_color = 'b'
    id_names = ['langsam', 'stadt', 'land', 'bab']
    for i in range(1,5):
        arr1 = Par_Fzg_1.get(f'id_{id_names[i-1]}', np.array([]))
        arr2 = Par_Fzg_2.get(f'id_{id_names[i-1]}', np.array([]))
        if arr1.size != 0 or arr2.size != 0:
            if plot_max:
                # angles for segment
                theta = np.linspace((i-1)*np.pi/2 - 2*np.pi/20, (i-1)*np.pi/2 + 2*np.pi/20, Emergenz_Array_Max_Abgl_Max.shape[1])
                ax.plot(theta, Emergenz_Array_Max_Abgl_Max[i-1, :], ':o', linewidth=5, color=plot_color)
                legend_text_max.append(f"{Name_Messung_Plot_ZF}\n- Maximale Emergenz")
                ct += 1
            if plot_median:
                theta = np.linspace((i-1)*np.pi/2 - 2*np.pi/20, (i-1)*np.pi/2 + 2*np.pi/20, Emergenz_Array_Max_Abgl_Median.shape[1])
                ax.plot(theta, Emergenz_Array_Max_Abgl_Median[i-1, :], '-s', linewidth=6, color=plot_color)
                legend_text_max.append(f"{Name_Messung_Plot_ZF}\n- Mediane Emergenz")
                ct += 1

    # Radial boundary lines
    ax.plot(np.full(9, np.pi/2), np.arange(0,9), 'k', linewidth=5)
    ax.plot(np.zeros(9), np.arange(0,9), 'k', linewidth=5)
    ax.plot(np.full(9, np.pi), np.arange(0,9), 'k', linewidth=5)
    ax.plot(np.full(9, -np.pi/2), np.arange(0,9), 'k', linewidth=5)

    plt.legend(legend_text_max, loc='upper right', fontsize=14)
    fig.savefig(os.path.join(save_path_ZF, 'Emergenz_Spinne.png'), dpi=300, bbox_inches='tight')
    plt.close('all')

    scipy.io.savemat(os.path.join(save_path_ZF, 'Emergenz_Zusammenfassung.mat'), {'Emergenz_Array_Max': Emergenz_Array_Max, 'Emergenz_Array_Max_Abgl_Max': Emergenz_Array_Max_Abgl_Max, 'Emergenz_Array_Max_Abgl_Median': Emergenz_Array_Max_Abgl_Median})


if __name__ == '__main__':
    Par = {'Mic_Pos_Name': ['VL_li','VL_re'],'Mic_Pos_Name_ZF':'Fahrer','Name_Emergenz_save':'test','Name_Messung_Plot':'test','ziel_fahrzeug_charakter':1}
    try:
        G_Emergenz_Zusammenfassung_ANTRIEB_v07(Par)
    except Exception as e:
        print('Test run failed (expected if .mat files missing):', e)
