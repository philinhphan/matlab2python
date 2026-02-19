import scipy.io
import numpy as np

workplace = scipy.io.loadmat('pre_convert_state.mat', simplify_cells=True)
del workplace['__header__']
del workplace['__version__']
del workplace['__globals__']
locals_pre_matlab = locals().copy()

locals().update(workplace)

Mic_Pos_Name = Par['Mic_Pos_Name']
Name_Messung_Plot = Par['Name_Messung_Plot'] + ' ' + Mic_Pos_Name
Name_Emergenz_save = Par['Name_Emergenz_save'] + '_' + Mic_Pos_Name
save_path = 'Emergenz/' + Name_Emergenz_save + '/'

FBereiche = [0, 1413, 1413, 4467, 4467, 30000] # Grenzen der Frequenzbereiche in Hz
Anzahl_FBereiche = len(FBereiche) // 2

meas = scipy.io.loadmat(save_path + 'Emergenz_Auswertung.mat', simplify_cells=True)
Emergenz_Array = meas['Emergenz_Array']
v = meas['v']
Abgl_Z = meas['Abgl_Z']
iGes = meas['iGes']
Udyn = meas['Udyn']

Emergenz_Array_Gruppen = Emergenz_Array.copy() # < v x Abgl_Z > mit Nummer des entsprechenden Frequenzbereiches
Emergenz_Array_Mittelfrequenz = Emergenz_Array.copy() # < v x Abgl_Z > mit Frequenz bei der mittlerer Gschwindigkeit des Schnittes

for kk in range(len(v)):
    for iz in range(len(Abgl_Z)):
        freq_temp = (Abgl_Z[iz] * iGes * v[kk]) / (60 * 0.06 * Udyn)
        Emergenz_Array_Mittelfrequenz[kk, iz] = freq_temp
        fb = 0 # Nummer des Frequenzbereiches
        while freq_temp > FBereiche[2 * fb + 1]:
            fb += 1
        Emergenz_Array_Gruppen[kk, iz] = fb
    Emergenz_Array_Gruppen[kk, iz+1] = Anzahl_FBereiche # LE-Auswertung in der höheren Gruppe

Emergenz_Array_Summiert = np.zeros((len(v), Anzahl_FBereiche)) # Energetische Summe der Tonalität der Ordnungen, die im gleichen v-Schnitt im gleichen Frequenzbereich liegen
Emergenz_Array_Max = np.zeros((len(v), Anzahl_FBereiche)) # Maximale Tonalität der Ordnungen, die im gleichen v-Schnitt im gleichen Frequenzbereich liegen
Emergenz_Array_Verteilung_N_Z = np.zeros((len(v), Anzahl_FBereiche)) # Anzahl an Ordnungen im jeweiligen Bereich
Emergenz_Array_Verteilung_N_Z_Ton = np.zeros((len(v), Anzahl_FBereiche)) # Anzahl an Ordnungen mit Tonalität > 0 dB im jeweiligen Bereich
for kk in range(len(v)):
    for fb in range(Anzahl_FBereiche):
        sum = 0
        max_temp = 0
        idf = np.where(Emergenz_Array_Gruppen[kk,:] == fb)[0]
        if idf.size != 0:
            Emergenz_Array_Verteilung_N_Z[kk,fb] = len(idf)
            for iz in range(len(idf)):
                if Emergenz_Array[kk, idf[iz]] > 0:
                    sum += 10**(Emergenz_Array[kk, idf[iz]]/10) # energetische Summe der Tonalitäten > 0 dB
                    Emergenz_Array_Verteilung_N_Z_Ton[kk,fb] += 1
                if Emergenz_Array[kk, idf[iz]] > max_temp:
                    max_temp = Emergenz_Array[kk, idf[iz]]
            if sum > 0:
                emergenz_temp = 10 * np.log10(sum) # summierte Tonalität im Frequenzbereich
                Emergenz_Array_Summiert[kk,fb] = emergenz_temp
            Emergenz_Array_Max[kk,fb] = max_temp

Anzahl_FBereiche = float(Anzahl_FBereiche)
export_vars = {key: val for key, val in locals().items() if key not in locals_pre_matlab and key != 'locals_pre_matlab'}
scipy.io.savemat('python_export_vars.mat', export_vars)



