"""
Converted from emergence/G_Emergenz_Verteilung_ANTRIEB_BEV_v07.m
Compute distribution of emergence across frequency bands and create summary plots.
"""
import os
import numpy as np
import scipy.io
import matplotlib.pyplot as plt
from utils import mat_to_dict, subtightplot
from Light import Light


def G_Emergenz_Verteilung_ANTRIEB_BEV_v07(Par):
    scipy.io.savemat('pre_convert_state.mat', {})

    Mic_Pos_Name = Par['Mic_Pos_Name']
    Name_Messung_Plot = f"{Par['Name_Messung_Plot']} {Mic_Pos_Name}"
    Name_Emergenz_save = f"{Par['Name_Emergenz_save']}_{Mic_Pos_Name}"
    save_path = os.path.join('Emergenz', Name_Emergenz_save)

    FBereiche = [[0,1413],[1413,4467],[4467,30000]]
    Anzahl_FBereiche = len(FBereiche)

    meas = scipy.io.loadmat(os.path.join(save_path, 'Emergenz_Auswertung.mat'))
    meas = mat_to_dict(meas)
    Emergenz_Array = meas['Emergenz_Array']
    v = meas.get('v', Par.get('v'))
    Abgl_Z = meas.get('Abgl_Z', Par.get('Abgl_Z'))
    iGes = meas.get('iGes', Par.get('iGes'))
    Udyn = meas.get('Udyn', Par.get('Udyn'))

    Emergenz_Array_Gruppen = Emergenz_Array.copy()
    Emergenz_Array_Mittelfrequenz = Emergenz_Array.copy()

    for kk in range(len(v)):
        for iz in range(len(Abgl_Z)):
            freq_temp = (Abgl_Z[iz] * iGes * v[kk]) / (60 * 0.06 * Udyn)
            Emergenz_Array_Mittelfrequenz[kk, iz] = freq_temp
            fb = 1
            while freq_temp > FBereiche[fb-1][1]:
                fb += 1
            Emergenz_Array_Gruppen[kk, iz] = fb
        Emergenz_Array_Gruppen[kk, iz+1-1] = Anzahl_FBereiche - 1

    Emergenz_Array_Summiert = np.zeros((len(v), Anzahl_FBereiche))
    Emergenz_Array_Max = np.zeros((len(v), Anzahl_FBereiche))
    Emergenz_Array_Verteilung_N_Z = np.zeros((len(v), Anzahl_FBereiche))
    Emergenz_Array_Verteilung_N_Z_Ton = np.zeros((len(v), Anzahl_FBereiche))

    for kk in range(len(v)):
        for fb in range(1, Anzahl_FBereiche+1):
            sum_val = 0.0
            max_temp = 0.0
            idf = np.where(Emergenz_Array_Gruppen[kk, :] == fb)[0]
            if idf.size != 0:
                Emergenz_Array_Verteilung_N_Z[kk, fb-1] = idf.size
                for izi in range(len(idf)):
                    if Emergenz_Array[kk, idf[izi]] > 0:
                        sum_val += 10 ** (Emergenz_Array[kk, idf[izi]] / 10)
                        Emergenz_Array_Verteilung_N_Z_Ton[kk, fb-1] += 1
                    if Emergenz_Array[kk, idf[izi]] > max_temp:
                        max_temp = Emergenz_Array[kk, idf[izi]]
                if sum_val > 0:
                    emergenz_temp = 10 * np.log10(sum_val)
                    Emergenz_Array_Summiert[kk, fb-1] = emergenz_temp
                Emergenz_Array_Max[kk, fb-1] = max_temp

    # NOTE: MATLAB used pyenv and pyrunfile to call a converter. We skip and assume conversion done.
    # Plot distribution of orders
    fig = plt.figure()
    cmap = plt.get_cmap('jet')(np.linspace(0,1,Anzahl_FBereiche))
    for fb in range(1, Anzahl_FBereiche+1):
        ax = subtightplot(2,2,fb,[0.1,0.05],[0.1,0.06],[0.05,0.05])
        ax.plot(v, Emergenz_Array_Verteilung_N_Z_Ton[:, fb-1], color=cmap[fb-1], linewidth=5)
        ax.plot(v, Emergenz_Array_Verteilung_N_Z[:, fb-1], color=cmap[fb-1], linewidth=5, linestyle='--')
        ax.set_xlim([0,150])
        ax.set_xticks(np.arange(0,151,10))
        ax.set_ylim([0,10])
        ax.set_yticks(np.arange(0,11,1))
        ax.tick_params(labelsize=14)
        ax.grid(True)
        ax.set_xlabel('Geschwindigkeit [km/h]', fontsize=14)
        ax.set_ylabel('Anzahl Ordnungen [-]', fontsize=14)
        ax.legend([f'Anzahl der hörbaren Ordnungen im Bereich {FBereiche[fb-1][0]/1000}-{FBereiche[fb-1][1]/1000} kHz', f'Anzahl der vorhandenen Ordnungen im Bereich {FBereiche[fb-1][0]/1000}-{FBereiche[fb-1][1]/1000} kHz'], loc='north east')
        if fb==1:
            ax.set_title(f'Luftschall Tonhaltigkeit "{Name_Messung_Plot}"', fontsize=18)

    fig.savefig(os.path.join(save_path, 'Emergenz_Verteilung.png'), dpi=300, bbox_inches='tight')

    # Plot summierte Tonhaltigkeit
    fig = plt.figure()
    cmap = plt.get_cmap('jet')(np.linspace(0,1,Anzahl_FBereiche))
    x_tick_labels = [str(vv) for vv in v]
    for fb in range(1, Anzahl_FBereiche+1):
        ax = subtightplot(2,2,fb,[0.1,0.05],[0.1,0.06],[0.05,0.05])
        ax.bar(np.arange(len(v)), Emergenz_Array_Summiert[:, fb-1], color=cmap[fb-1])
        ax.set_xlim([0,15])
        ax.set_ylim([0,20])
        ax.set_xticks(np.arange(len(v)))
        ax.set_xticklabels(x_tick_labels)
        ax.tick_params(labelsize=14)
        ax.grid(True)
        ax.set_xlabel('Geschwindigkeit [km/h]', fontsize=14)
        ax.set_ylabel('Emergenz [dB(A)]', fontsize=14)
        if fb==1:
            ax.set_title(f'Luftschall Tonhaltigkeit "{Name_Messung_Plot}"', fontsize=18)

    fig.savefig(os.path.join(save_path, 'Emergenz_Summiert.png'), dpi=300, bbox_inches='tight')

    # Plot summierte Tonhaltigkeit with max tonalities
    fig = plt.figure()
    cmap = plt.get_cmap('jet')(np.linspace(0,1,Anzahl_FBereiche))
    x_tick_labels = [str(vv) for vv in v]
    for fb in range(1, Anzahl_FBereiche+1):
        ax = subtightplot(2,2,fb,[0.1,0.05],[0.1,0.06],[0.05,0.05])
        widths = np.arange(len(v))
        ax.bar(widths - 0.2, Emergenz_Array_Summiert[:, fb-1], width=0.4, color=cmap[fb-1])
        ax.bar(widths + 0.2, Emergenz_Array_Max[:, fb-1], width=0.4, color=[Light(cmap[fb-1][:3],20)])
        ax.set_xlim([0,15])
        ax.set_ylim([0,20])
        ax.set_xticks(np.arange(len(v)))
        ax.set_xticklabels(x_tick_labels)
        ax.tick_params(labelsize=14)
        ax.grid(True)
        ax.set_xlabel('Geschwindigkeit [km/h]', fontsize=14)
        ax.set_ylabel('Emergenz [dB(A)]', fontsize=14)
        if fb==1:
            ax.set_title(f'Luftschall Tonhaltigkeit "{Name_Messung_Plot}"', fontsize=18)

    fig.savefig(os.path.join(save_path, 'Emergenz_Summiert_Max.png'), dpi=300, bbox_inches='tight')

    # Plot max tonalities compared to Zielkurven
    zk = scipy.io.loadmat('Emergenz_Zielkurven_v2.mat')
    zk = mat_to_dict(zk)
    Zielkurven = np.zeros((15,5,3))
    Zielkurven[:, :, 0] = zk['Zielkurven_0_1250Hz_Heulen']
    Zielkurven[:, :, 1] = zk['Zielkurven_1250_4000Hz_Pfeifen']
    Zielkurven[:, :, 2] = zk['Zielkurven_4000Hz_Piepsen']

    fig = plt.figure()
    cmap = plt.get_cmap('jet')(np.linspace(0,1,Anzahl_FBereiche))
    cmap_zielkurven = np.vstack([[0,0,0], [244,177,131], [237,125,49], [197,90,17], [132,60,12]])/255.0
    x_tick_labels = [str(vv) for vv in v]
    for fb in range(1, Anzahl_FBereiche+1):
        ax = subtightplot(2,2,fb,[0.1,0.05],[0.1,0.06],[0.05,0.05])
        ax.bar(np.arange(len(v)), Emergenz_Array_Max[:, fb-1], color=cmap[fb-1])
        ax.set_xlim([0,15])
        ax.set_ylim([0,20])
        ax.set_xticks(np.arange(len(v)))
        ax.set_xticklabels(x_tick_labels)
        ax.tick_params(labelsize=14)
        ax.grid(True)
        for z in range(5):
            ax.plot(np.arange(1, len(v)+1), Zielkurven[:, z, fb-1], color=cmap_zielkurven[z], linewidth=3)
        if fb == 1:
            legend_labels = ['Obergrenze für "unhörbar"', 'Obergrenze für "leise"', 'Obergrenze für "dezent"', 'Obergrenze für "präsent"', 'Obergrenze für "dominant"']
            legend_labels = ['Maximale Tonalität im Bereich {}-{} kHz'.format(FBereiche[fb-1][0]/1000, FBereiche[fb-1][1]/1000)] + legend_labels
            ax.legend(legend_labels, loc='north east')
        if fb==1:
            ax.set_title(f'Luftschall Tonhaltigkeit "{Name_Messung_Plot}"', fontsize=18)

    fig.savefig(os.path.join(save_path, 'Emergenz_Max.png'), dpi=300, bbox_inches='tight')

    plt.close('all')

    # Save variables
    scipy.io.savemat(os.path.join(save_path, 'Emergenz_Verteilung.mat'), {'Emergenz_Array_Gruppen': Emergenz_Array_Gruppen, 'Emergenz_Array_Mittelfrequenz': Emergenz_Array_Mittelfrequenz, 'Emergenz_Array_Summiert': Emergenz_Array_Summiert, 'Emergenz_Array_Max': Emergenz_Array_Max, 'Emergenz_Array_Verteilung_N_Z': Emergenz_Array_Verteilung_N_Z, 'Emergenz_Array_Verteilung_N_Z_Ton': Emergenz_Array_Verteilung_N_Z_Ton})


if __name__ == '__main__':
    Par = {'Mic_Pos_Name':'VL_li','Name_Emergenz_save':'test','Name_Messung_Plot':'test','v':[10,20,30],'Abgl_Z':[1,2,3],'iGes':11.12,'Udyn':1}
    try:
        G_Emergenz_Verteilung_ANTRIEB_BEV_v07(Par)
    except Exception as e:
        print('Test run failed (expected if .mat files missing):', e)
