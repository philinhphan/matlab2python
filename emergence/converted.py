from scipy.io import loadmat, savemat
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

workplace = loadmat("temp.mat", simplify_cells=True)
del workplace["__header__"]
del workplace["__version__"]
del workplace["__globals__"]
locals_pre_matlab = locals().copy()
locals().update(workplace)

Mic_Pos_Name = Par['Mic_Pos_Name']
Name_Messung_Plot = Par['Name_Messung_Plot'] + ' ' + Mic_Pos_Name
Name_Emergenz_save = Par['Name_Emergenz_save'] + '_' + Mic_Pos_Name
save_path = 'Emergenz/' + Name_Emergenz_save + '/'

FBereiche = [0, 1413, 1413, 4467, 4467, 30000]  # Grenzen der Frequenzbereiche in Hz
Anzahl_FBereiche = len(FBereiche) // 2

meas = loadmat(save_path + 'Emergenz_Auswertung.mat', simplify_cells=True)
Emergenz_Array = meas['Emergenz_Array']
v = meas['v']
Abgl_Z = meas['Abgl_Z']
iGes = float(meas['iGes'])
Udyn = meas['Udyn']

Emergenz_Array_Gruppen = Emergenz_Array.copy()  # < v x Abgl_Z > mit Nummer des entsprechenden Frequenzbereiches
Emergenz_Array_Mittelfrequenz = Emergenz_Array.copy()  # < v x Abgl_Z > mit Frequenz bei der mittlerer Gschwindigkeit des Schnittes

for kk in range(len(v)):
    for iz in range(len(Abgl_Z)):
        freq_temp = (Abgl_Z[iz] * iGes * v[kk]) / (60 * 0.06 * Udyn)
        Emergenz_Array_Mittelfrequenz[kk][iz] = freq_temp
        fb = 1  # Nummer des Frequenzbereiches
        while freq_temp > FBereiche[2 * fb + 1]:
            fb += 1
        Emergenz_Array_Gruppen[kk][iz] = fb
    Emergenz_Array_Gruppen[kk][iz + 1] = Anzahl_FBereiche  # LE-Auswertung in der höheren Gruppe

Emergenz_Array_Summiert = np.zeros((len(v),
                                    Anzahl_FBereiche))  # Energetische Summe der Tonalität der Ordnungen, die im gleichen v-Schnitt im gleichen Frequenzbereich liegen
Emergenz_Array_Max = np.zeros((len(v),
                               Anzahl_FBereiche))  # Maximale Tonalität der Ordnungen, die im gleichen v-Schnitt im gleichen Frequenzbereich liegen
Emergenz_Array_Verteilung_N_Z = np.zeros((len(v), Anzahl_FBereiche))  # Anzahl an Ordnungen im jeweiligen Bereich
Emergenz_Array_Verteilung_N_Z_Ton = np.zeros(
    (len(v), Anzahl_FBereiche))  # Anzahl an Ordnungen mit Tonalität > 0 dB im jeweiligen Bereich

for kk in range(len(v)):
    for fb in range(Anzahl_FBereiche):
        sum = 0
        max_temp = 0
        idf = np.where(Emergenz_Array_Gruppen[kk, :] == fb)[0]
        if idf.size > 0:
            Emergenz_Array_Verteilung_N_Z[kk][fb] = len(idf)
            for iz in range(len(idf)):
                if Emergenz_Array[kk][idf[iz]] > 0:
                    sum += 10 ** (Emergenz_Array[kk][idf[iz]] / 10)  # energetische Summe der Tonalitäten > 0 dB
                    Emergenz_Array_Verteilung_N_Z_Ton[kk][fb] += 1
                if Emergenz_Array[kk][idf[iz]] > max_temp:
                    max_temp = Emergenz_Array[kk][idf[iz]]
            if sum > 0:
                emergenz_temp = 10 * np.log10(sum)  # summierte Tonalität im Frequenzbereich
                Emergenz_Array_Summiert[kk][fb] = emergenz_temp
            Emergenz_Array_Max[kk][fb] = max_temp

# Plot der Ordnungsverteilung
f = plt.figure()
screen_size = (1440, 900)
f.set_size_inches(0.99 * screen_size[0] / 100.0, 0.85 * screen_size[1] / 100.0)
cmap = list(mcolors.TABLEAU_COLORS.values())
for fb in range(Anzahl_FBereiche):
    lengendInfo = ['', '']
    # subtightplot(2, 2, fb + 1, [0.1, 0.05], [0.1, 0.06], [0.05, 0.05])
    plt.plot(v, Emergenz_Array_Verteilung_N_Z_Ton[:, fb], color=cmap[fb], linewidth=5)
    plt.plot(v, Emergenz_Array_Verteilung_N_Z[:, fb], '--', color=cmap[fb], linewidth=5)
    plt.xlim(0, 150)
    plt.xticks(range(0, 151, 10), fontsize=14)
    plt.ylim(0, 10)
    plt.yticks(range(0, 11, 1), fontsize=14)
    plt.xlabel('Geschwindigkeit [km/h]', fontsize=14)
    plt.ylabel('Anzahl Ordnungen [-]', fontsize=14)
    lengendInfo[0] = 'Anzahl der hörbaren Ordnungen im Bereich ' + str(FBereiche[2 * fb + 1] / 1000) + '-' + str(
        FBereiche[2 * fb + 1] / 1000) + ' kHz'
    lengendInfo[1] = 'Anzahl der vorhandenen Ordnungen im Bereich ' + str(FBereiche[2 * fb + 1] / 1000) + '-' + str(
        FBereiche[2 * fb + 1] / 1000) + ' kHz'
    plt.legend(lengendInfo, loc='upper right')
    if fb == 0:
        plt.title('Luftschall Tonhaltigkeit "' + Name_Messung_Plot + '"', fontsize=18, loc='left')

plt.savefig(save_path + 'Emergenz_Verteilung')
f.savefig(save_path + 'Emergenz_Verteilung', bbox_inches='tight', dpi=300)

# Plot der summierten Tonhaltigkeit
f = plt.figure()
f.set_size_inches(0.99 * screen_size[0] / 100.0, 0.85 * screen_size[1] / 100.0)
x_tick_labels = [str(i) for i in v]
for fb in range(Anzahl_FBereiche):
    lengendInfo = ['']
    # subtightplot(2, 2, fb + 1, [0.1, 0.05], [0.1, 0.06], [0.05, 0.05])
    plt.bar(range(len(v)), Emergenz_Array_Summiert[:, fb], color=cmap[fb])
    plt.xlim(0, 15)
    plt.ylim(0, 20)
    plt.xticks(range(len(v)), x_tick_labels, fontsize=14)
    plt.yticks(range(0, 21, 2), fontsize=14)
    plt.grid(True)
    plt.xlabel('Geschwindigkeit [km/h]', fontsize=14)
    plt.ylabel('Emergenz [dB(A)]', fontsize=14)
    lengendInfo[0] = 'Summierte Tonhaltigkeit im Bereich ' + str(FBereiche[2 * fb + 1] / 1000) + '-' + str(
        FBereiche[2 * fb + 1] / 1000) + ' kHz'
    plt.legend(lengendInfo, loc='upper right')
    if fb == 0:
        plt.title('Luftschall Tonhaltigkeit "' + Name_Messung_Plot + '"', fontsize=18, loc='left')

plt.savefig(save_path + 'Emergenz_Summiert')
f.savefig(save_path + 'Emergenz_Summiert', bbox_inches='tight', dpi=300)

# Plot der summierten Tonhaltigkeit mit maximaler Tonalität
f = plt.figure()
f.set_size_inches(0.99 * screen_size[0] / 100.0, 0.85 * screen_size[1] / 100.0)
x_tick_labels = [str(i) for i in v]
for fb in range(Anzahl_FBereiche):
    lengendInfo = ['', '']
    # subtightplot(2, 2, fb + 1, [0.1, 0.05], [0.1, 0.06], [0.05, 0.05])
    # h = plt.bar(range(len(v)), np.column_stack((Emergenz_Array_Summiert[:, fb], Emergenz_Array_Max[:, fb])), color=cmap[Light(cmap[fb], 20), cmap[fb]], width=1.5)
    plt.xlim(0, 15)
    plt.ylim(0, 20)
    plt.xticks(range(len(v)), x_tick_labels, fontsize=14)
    plt.yticks(range(0, 21, 2), fontsize=14)
    plt.grid(True)
    plt.xlabel('Geschwindigkeit [km/h]', fontsize=14)
    plt.ylabel('Emergenz [dB(A)]', fontsize=14)
    lengendInfo[0] = 'Summierte Tonhaltigkeit im Bereich ' + str(FBereiche[2 * fb + 1] / 1000) + '-' + str(
        FBereiche[2 * fb + 1] / 1000) + ' kHz'
    lengendInfo[1] = 'Maximale Tonalität im Bereich ' + str(FBereiche[2 * fb + 1] / 1000) + '-' + str(
        FBereiche[2 * fb + 1] / 1000) + ' kHz'
    plt.legend(lengendInfo, loc='upper right')

    if fb == 0:
        plt.title('Luftschall Tonhaltigkeit "' + Name_Messung_Plot + '"', fontsize=18, loc='left')

plt.savefig(save_path + 'Emergenz_Summiert_Max')
f.savefig(save_path + 'Emergenz_Summiert_Max', bbox_inches='tight', dpi=300)

# Plot der maximalen Tonhaltigkeit im Vergleich mit den Emergenz-Zielkurven
zk = loadmat('Emergenz_Zielkurven_v2.mat', simplify_cells=True)
Zielkurven = np.zeros((15, 5, 3))
Zielkurven[:, :, 0] = zk['Zielkurven_0_1250Hz_Heulen']
Zielkurven[:, :, 1] = zk['Zielkurven_1250_4000Hz_Pfeifen']
Zielkurven[:, :, 2] = zk['Zielkurven_4000Hz_Piepsen']

f = plt.figure()
f.set_size_inches(0.99 * screen_size[0] / 100.0, 0.85 * screen_size[1] / 100.0)
cmap = list(mcolors.TABLEAU_COLORS.values())
cmap_zielkurven = np.asarray([[0, 0, 0], [244, 177, 131], [237, 125, 49], [197, 90, 17], [132, 60, 12]]) / 255
x_tick_labels = [str(i) for i in v]
for fb in range(Anzahl_FBereiche):
    lengendInfo = ['']
    # subtightplot(2, 2, fb + 1, [0.1, 0.05], [0.1, 0.06], [0.05, 0.05])
    plt.bar(range(len(v)), Emergenz_Array_Max[:, fb], color=cmap[fb])
    plt.xlim(0, 15)
    plt.ylim(0, 20)
    plt.xticks(range(len(v)), x_tick_labels, fontsize=14)
    plt.yticks(range(0, 21, 2), fontsize=14)
    plt.grid(True)
    plt.xlabel('Geschwindigkeit [km/h]', fontsize=14)
    plt.ylabel('Emergenz [dB(A)]', fontsize=14)
    lengendInfo[0] = 'Maximale Tonalität im Bereich ' + str(FBereiche[2 * fb + 1] / 1000) + '-' + str(
        FBereiche[2 * fb + 1] / 1000) + ' kHz'
    plt.plot(range(1, 16), Zielkurven[:, :, fb], linewidth=3, color=cmap_zielkurven[1])
    if fb == 0:  # Legende für die Zielkurven nur im linken oberen Bild
        lengendInfo.append('Obergrenze für "unhörbar"')
        lengendInfo.append('Obergrenze für "leise"')
        lengendInfo.append('Obergrenze für "dezent"')
        lengendInfo.append('Obergrenze für "präsent"')
        lengendInfo.append('Obergrenze für "dominant"')
    plt.legend(lengendInfo, loc='upper right')
    if fb == 0:
        plt.title('Luftschall Tonhaltigkeit "' + Name_Messung_Plot + '"', fontsize=18, loc='left')

plt.savefig(save_path + 'Emergenz_Max')
f.savefig(save_path + 'Emergenz_Max', bbox_inches='tight', dpi=300)

plt.close('all')
np.save(save_path + 'Emergenz_Verteilung.npy',
        [Emergenz_Array_Summiert, Emergenz_Array_Max, Emergenz_Array_Verteilung_N_Z, Emergenz_Array_Verteilung_N_Z_Ton])


export_vars = {key: val for key, val in locals().items() if key not in locals_pre_matlab and key != 'locals_pre_matlab'}
savemat('python_export_vars.mat', export_vars)



