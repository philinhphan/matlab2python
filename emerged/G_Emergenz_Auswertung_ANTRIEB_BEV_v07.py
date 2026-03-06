"""
Converted from emergence/G_Emergenz_Auswertung_ANTRIEB_BEV_v07.m
Primary evaluation of emergence (delta drive tones / MHS) for a given microphone position.
"""
import os
import numpy as np
import scipy.io
import math
import matplotlib.pyplot as plt
from utils import mat_to_dict


def G_Emergenz_Auswertung_ANTRIEB_BEV_v07(Par):
    """Evaluate emergence for given parameters dictionary Par.

    Par is a dict with keys used in the MATLAB script.
    """
    Mic_Pos_Name = Par['Mic_Pos_Name']
    Name_Emergenz_save = f"{Par['Name_Emergenz_save']}_{Mic_Pos_Name}"
    Name_MHS_Kurven_Ordner = Par['Name_MHS_Kurven_Ordner']
    Name_Messdaten_Ordner = Par['Name_Messdaten_Ordner']
    Name_Messung = Par['Name_Messung']
    Name_Messung_Plot = f"{Par['Name_Messung_Plot']} {Mic_Pos_Name}"

    # Map Mic_Pos_Name to variable prefix used in .mat files
    if Mic_Pos_Name == 'VL_li':
        Mic_Pos = 'Mic__VL_li_Ohr_S'
    elif Mic_Pos_Name == 'VL_re':
        Mic_Pos = 'Mic__VL_re_Ohr_S'
    elif Mic_Pos_Name == 'VR_li':
        Mic_Pos = 'Mic__VR_li_Ohr_S'
    elif Mic_Pos_Name == 'VR_re':
        Mic_Pos = 'Mic__VR_re_Ohr_S'
    elif Mic_Pos_Name == 'HL_li':
        Mic_Pos = 'Mic__HL_li_Ohr_S'
    elif Mic_Pos_Name == 'HL_re':
        Mic_Pos = 'Mic__HL_re_Ohr_S'
    elif Mic_Pos_Name == 'HR_li':
        Mic_Pos = 'Mic__HR_li_Ohr_S'
    elif Mic_Pos_Name == 'HR_re':
        Mic_Pos = 'Mic__HR_re_Ohr_S'
    else:
        raise ValueError(f'Unknown Mic_Pos_Name: {Mic_Pos_Name}')
    Par['Mic_Pos'] = Mic_Pos

    # Load measurement curves
    meas_curves_path = os.path.join('MHS Kurven', f"{Name_MHS_Kurven_Ordner}_{Mic_Pos_Name}", f"{Name_MHS_Kurven_Ordner}_{Mic_Pos_Name}_Ziele_Innenraum.mat")
    raw = scipy.io.loadmat(meas_curves_path)
    meas_curves = mat_to_dict(raw)
    freq = meas_curves['freq']
    fy = meas_curves['fy']
    Lmhs_array = meas_curves['Lmhs_array']
    specs = meas_curves['specs']

    v = Par['v']
    v_meas = Par['v_meas']
    v_aufloesung = 2

    meas_ges_path = os.path.join('Messdaten', Name_Messdaten_Ordner, Mic_Pos_Name, f"{Name_Messung}APS_Gesamt.mat")
    raw = scipy.io.loadmat(meas_ges_path)
    meas_ges = mat_to_dict(raw)

    freq_meas = meas_ges[f"{Mic_Pos}_X"]
    meas = np.zeros((len(freq), len(v)))

    iGes = Par['iGes']
    RB = Par['RB']
    QV = Par['QV']
    FD = Par['FD']
    KY = 0.97
    Udyn = (25.4 * FD + 2 * RB * QV / 100) * (math.pi * KY / 1000)

    Abgl_Z = sorted(Par['Abgl_Z'])
    freq_PWM = Par['freq_PWM']

    os.makedirs(os.path.join('Emergenz', Name_Emergenz_save), exist_ok=True)
    save_path = os.path.join('Emergenz', Name_Emergenz_save)

    # Fill meas matrix from meas_ges dynamic fields
    for jj in range(1, len(v)+1):
        if jj == 1:
            meas[:, jj-1] = 20 * np.log10(meas_ges[Mic_Pos] / (2 * 10**-5))
        elif jj < 11:
            key = f"{Mic_Pos}_0{jj-1}"
            meas[:, jj-1] = 20 * np.log10(meas_ges[key] / (2 * 10**-5))
        else:
            key = f"{Mic_Pos}_{jj-1}"
            meas[:, jj-1] = 20 * np.log10(meas_ges[key] / (2 * 10**-5))

    Emergenz_Array = np.zeros((len(v), len(Abgl_Z) + 1))
    v_meas_ungefiltert = [[5,15],[15,25],[25,35],[35,45],[45,55],[55,65],[65,75],[75,85],[85,95],[95,105],[105,115],[115,125],[125,135],[135,145],[145,155]]
    v_meas_ungefiltert = v_meas_ungefiltert[:len(v_meas)]

    # CONVERSION NOTE: MATLAB save('pre_convert_state') saved workspace. We do not replicate saving all variables.
    scipy.io.savemat('pre_convert_state.mat', {'v': v, 'v_meas': v_meas})

    for kk in range(1, len(v)+1):
        v_grenzen = v_meas[2*kk-2:2*kk]
        v_grenzen_anfang = str(v_grenzen[0])
        # v_grenzen_anfang = str2num(v_grenzen_anfang(end)); in MATLAB they take last char; here take last digit
        v_grenzen_anfang = int(v_grenzen_anfang[-1])
        v_grenzen_ungefiltert = v_meas_ungefiltert[2*kk-2:2*kk]
        verschiebung = math.floor((v_grenzen[0] - v_grenzen_ungefiltert[0]) / v_aufloesung)
        anzahl_v_bereiche = math.ceil((v_grenzen[1] - v_grenzen[0]) / v_aufloesung)

        meas_kmh_path = os.path.join('Messdaten', Name_Messdaten_Ordner, Mic_Pos_Name, f"{Name_Messung}APS_{v[kk-1]}kmh.mat")
        raw = scipy.io.loadmat(meas_kmh_path)
        meas_kmh = mat_to_dict(raw)

        freq_meas_unterteilt = meas_kmh[f"{Mic_Pos}_X"]
        meas_unterteilt = np.zeros((len(freq), anzahl_v_bereiche))

        for vv in range(1, anzahl_v_bereiche+1):
            if vv == 1:
                if v_grenzen_anfang in [5, 6]:
                    meas_unterteilt[:, vv-1] = 20 * np.log10(meas_kmh[Mic_Pos] / (2 * 10**-5))
                else:
                    key = f"{Mic_Pos}_0{verschiebung}"
                    meas_unterteilt[:, vv-1] = 20 * np.log10(meas_kmh[key] / (2 * 10**-5))
            elif vv < 11:
                key = f"{Mic_Pos}_0{vv-1+verschiebung}"
                meas_unterteilt[:, vv-1] = 20 * np.log10(meas_kmh[key] / (2 * 10**-5))
            else:
                key = f"{Mic_Pos}_{vv-1+verschiebung}"
                meas_unterteilt[:, vv-1] = 20 * np.log10(meas_kmh[key] / (2 * 10**-5))

        for vv in range(1, anzahl_v_bereiche+1):
            v_grenzen_unterteilt = [v_grenzen[0] + 2*(vv-1), v_grenzen[0] + 2*(vv)]
            OF_v = np.zeros((len(Abgl_Z), 2))
            for iz in range(1, len(Abgl_Z)+1):
                OF_v[iz-1, :] = (Abgl_Z[iz-1] * iGes * v_grenzen_unterteilt) / (60 * 0.06 * Udyn)
                idx = np.where((freq_meas_unterteilt <= math.ceil(1.01 * OF_v[iz-1, 1])) & (freq_meas >= math.floor(0.99 * OF_v[iz-1, 0])))[0]
                Emergenz = 0
                for i in range(len(idx)):
                    freq_temp = freq_meas_unterteilt[idx[i]]
                    idxi = np.where(fy == freq_temp)[0]
                    if idxi.size == 0:
                        continue
                    Emergenz_temp = meas_unterteilt[idx[i], vv-1] - Lmhs_array[idxi[0], kk-1]
                    if Emergenz_temp > Emergenz:
                        Emergenz = Emergenz_temp
                if Emergenz > Emergenz_Array[kk-1, iz-1]:
                    Emergenz_Array[kk-1, iz-1] = Emergenz

            # Auswertung LE
            # Use explicit last order index instead of relying on loop variable 'iz'
            last_iz = len(Abgl_Z)
            freq_suchbereich = [max(4000, freq_PWM/2), freq_meas[-1]]
            if freq_PWM + OF_v[last_iz-1, 1] < freq_meas[-1]:
                freq_suchbereich[1] = freq_PWM + OF_v[last_iz-1, 1]
            if freq_PWM - OF_v[last_iz-1, 1] > max(4000, freq_PWM/2):
                freq_suchbereich[0] = freq_PWM - OF_v[last_iz-1, 1]
            Emergenz = 0
            for i in range(len(freq_meas_unterteilt)):
                if (freq_meas_unterteilt[i] >= freq_suchbereich[0]) and (freq_meas_unterteilt[i] <= freq_suchbereich[1]):
                    idxj = np.where((OF_v[:,0] - 100 <= freq_meas_unterteilt[i]) & (OF_v[:,1] + 100 >= freq_meas_unterteilt[i]))[0]
                    if idxj.size == 0:
                        idxi = np.where(fy == freq_meas_unterteilt[i])[0]
                        if idxi.size == 0:
                            continue
                        Emergenz_temp = meas_unterteilt[i, vv-1] - Lmhs_array[idxi[0], kk-1]
                        if Emergenz_temp > Emergenz:
                            Emergenz = Emergenz_temp
            # Save LE result in last column (index = len(Abgl_Z))
            if Emergenz > Emergenz_Array[kk-1, last_iz]:
                Emergenz_Array[kk-1, last_iz] = Emergenz

        # Emergenz from orders vs LE
        id_le = np.where(Emergenz_Array[kk-1, :len(Abgl_Z)] == Emergenz_Array[kk-1, -1])[0]
        if id_le.size != 0:
            Emergenz_Array[kk-1, -1] = 0

    # Plots
    cmap = plt.get_cmap('jet')(np.linspace(0,1,len(Abgl_Z)))
    for kk in range(1, len(v)+1):
        legendInfo = []
        fig, ax = plt.subplots()
        ax.semilogx(fy, Lmhs_array[:, kk-1], color='k', linewidth=5)
        legendInfo.append(f'Mithörschwelle {v[kk-1]} km/h')
        ax.semilogx(freq, specs[:, kk-1], color=[0.5,0.5,0.5], linewidth=5)
        legendInfo.append(f'Mittelung WRG {v[kk-1]} km/h')
        ax.semilogx(freq_meas, meas[:, kk-1], color='k', linewidth=1)
        legendInfo.append(f'Max gemessen {v[kk-1]} km/h')
        for iz in range(1, len(Abgl_Z)+1):
            v_grenzen = [v[kk-1]-5, v[kk-1]+5]
            OF_v[iz-1, :] = (Abgl_Z[iz-1]*iGes*v_grenzen)/(60*0.06*Udyn)
            idx = np.where((freq_meas[:,0] <= OF_v[iz-1,1]) & (freq_meas[:,0] >= OF_v[iz-1,0]))[0]
            if idx.size != 0:
                ax.semilogx(freq_meas[idx,0], meas[idx, kk-1], color=cmap[iz-1], linewidth=2)
                Emergenz = Emergenz_Array[kk-1, iz-1]
                if Emergenz <= 0:
                    legendInfo.append(f'Max gemessen {v[kk-1]} km/h - {Abgl_Z[iz-1]}. Ordnung')
                else:
                    legendInfo.append(f'Max gemessen {v[kk-1]} km/h - {Abgl_Z[iz-1]}. Ordnung - Emergenz {round(Emergenz*10)/10} dB')
        ax.semilogx(freq_meas, meas[:, kk-1], color='k', linewidth=1, visible='off')
        le_col = len(Abgl_Z)
        if Emergenz_Array[kk-1, le_col] <= 0:
            legendInfo.append(f'Max gemessen {v[kk-1]} km/h - LE')
        else:
            legendInfo.append(f"Max gemessen {v[kk-1]} km/h - LE - Emergenz {round(Emergenz_Array[kk-1, le_col]*10)/10} dB")
        # screen_size = get(0,'ScreenSize')  # Not portable; skip
        fig.set_size_inches(16, 9)
        ax.set_xlim([10, 15000])
        ax.tick_params(labelsize=14)
        ax.legend(legendInfo, loc='best', fontsize=14)
        ax.grid(True)
        ax.set_xlabel('Frequenz [Hz]', fontsize=14)
        ax.set_ylabel('Innenraum Schalldruckpegel [dB(A)]', fontsize=14)
        ax.set_title(f'LS Abgleich Schmallband aus der Messung "{Name_Messung_Plot}" / Mithörschwelle aus dem Ausrollen (nach DIN 45681) - {v[kk-1]} km/h', fontsize=18)
        plt.tight_layout()
        # Save
        fig.savefig(os.path.join(save_path, f'Emergenz_{v[kk-1]}_kmh.png'), dpi=300, bbox_inches='tight')

    # Summary bar plot
    fig, ax = plt.subplots()
    cmap = np.vstack([plt.get_cmap('jet')(np.linspace(0,1,len(Abgl_Z))), np.array([[0,0,0,1]])])
    legendInfo = []
    for iz in range(1, len(Abgl_Z)+2):
        mittelwert_temp = str(round(np.mean(Emergenz_Array[:, iz-1])*10)/10)
        maxwert_temp = str(round(np.max(Emergenz_Array[:, iz-1])*10)/10)
        if iz <= len(Abgl_Z):
            legendInfo.append(f'Emergenz {Abgl_Z[iz-1]}. Ordnung (Mittel {mittelwert_temp} dB, Max {maxwert_temp} dB)')
        else:
            legendInfo.append(f'Emergenz LE (Mittel {mittelwert_temp} dB, Max {maxwert_temp} dB)')
    x_tick_labels = [str(vv) for vv in v]
    ax.bar(np.arange(len(v)), Emergenz_Array)
    fig.set_size_inches(16, 9)
    ax.set_xlim([0, 15])
    ax.set_ylim([0, 20])
    ax.set_xticklabels(x_tick_labels)
    ax.tick_params(labelsize=14)
    ax.legend(legendInfo, loc='best', fontsize=14)
    ax.grid(True)
    ax.set_xlabel('Geschwindigkeit [km/h]', fontsize=14)
    ax.set_ylabel('Emergenz [dB(A)]', fontsize=14)
    ax.set_title(f'LS Abgleich Schmallband aus der Messung "{Name_Messung_Plot}" / Mithörschwelle aus dem Ausrollen (nach DIN 45681)', fontsize=18)

    fig.savefig(os.path.join(save_path, 'Emergenz_Zusammenfassung.png'), dpi=300, bbox_inches='tight')

    plt.close('all')

    # Save mat
    scipy.io.savemat(os.path.join(save_path, 'Emergenz_Auswertung.mat'), {'Emergenz_Array': Emergenz_Array})


if __name__ == '__main__':
    # Minimal smoke test
    Par = {'Mic_Pos_Name': 'VL_li', 'Name_Emergenz_save': 'test', 'Name_MHS_Kurven_Ordner': 'G26_BEV_BBG_V410176', 'Name_Messdaten_Ordner': 'SDSA', 'Name_Messung': 'BMW i4 80 sD #H019370#14.11.2019#10_59#SD#', 'Name_Messung_Plot': 'test', 'v': [10], 'v_meas': [[5,15]], 'iGes': 11.12, 'RB': 245, 'QV': 45, 'FD': 18, 'Abgl_Z': [1,2,3], 'freq_PWM':8000}
    try:
        G_Emergenz_Auswertung_ANTRIEB_BEV_v07(Par)
    except Exception as e:
        print('Test run failed (expected if .mat files missing):', e)
