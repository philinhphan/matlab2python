"""
Converted from Emergenz_ANTRIEB_BEV_v07_G26_BEV_BBG_V410176_Schub.m
Main orchestrator script to run Emergence analysis for multiple microphones and summarize.
"""

from G_Emergenz_Auswertung_ANTRIEB_BEV_v07 import G_Emergenz_Auswertung_ANTRIEB_BEV_v07
from G_Emergenz_Verteilung_ANTRIEB_BEV_v07 import G_Emergenz_Verteilung_ANTRIEB_BEV_v07
from G_Emergenz_Spinne_ANTRIEB_BEV_v07 import G_Emergenz_Spinne_ANTRIEB_BEV_v07
from G_Emergenz_Zusammenfassung_ANTRIEB_v07 import G_Emergenz_Zusammenfassung_ANTRIEB_v07


def main():
    # Input Parameter
    Par = {}
    Par['Name_MHS_Kurven_Ordner'] = 'G26_BEV_BBG_V410176'               # Source folder under "MHS Kurven"
    Par['Name_Messdaten_Ordner'] = 'SDSA'                               # Source folder under "Messdaten"
    Par['Name_Messung'] = 'BMW i4 80 sD #H019370#14.11.2019#10_59#SD#'  # Name of exported measurement data
    Par['Name_Emergenz_save'] = 'G26_BEV_BBG_V410176_Schub_test02'       # Output folder for Emergence analysis (auto-created)
    Par['Name_Messung_Plot'] = 'G26 BEV BBG V410176 Schub (14.11.2019 10:57)'

    Par['Mic_Pos_Liste'] = ['VL_li','VL_re','HR_li','HR_re']
    Par['Mic_Pos_Liste_ZF'] = ['Fahrer','Fond']

    Par['v'] = list(range(10, 141, 10))
    Par['v_meas'] = [[5,15],[15,25],[25,35],[35,45],[45,55],[55,65],[65,75],[75,85],[85,95],[95,105],[105,115],[115,125],[125,135],[135,145]]

    Par['iGes'] = 11.12
    Par['RB'] = 245
    Par['QV'] = 45
    Par['FD'] = 18

    Par['Abgl_Z'] = sorted([1,2,3,4,5,6,7,14,18,23,46,54])
    Par['freq_PWM'] = 8000

    Par['ziel_fahrzeug_charakter'] = 1

    # Calculation and evaluation
    # Loop over microphones
    for i in range(1, len(Par['Mic_Pos_Liste'])+1):
        Par['Mic_Pos_Name'] = Par['Mic_Pos_Liste'][i-1]
        G_Emergenz_Auswertung_ANTRIEB_BEV_v07(Par)
        G_Emergenz_Verteilung_ANTRIEB_BEV_v07(Par)
        G_Emergenz_Spinne_ANTRIEB_BEV_v07(Par)

    # Summary over two microphones
    for i in range(1, len(Par['Mic_Pos_Liste_ZF'])+1):
        # MATLAB: Par.Mic_Pos_Name = Par.Mic_Pos_Liste(1,2*i-1:2*i);
        # Convert to selecting pair from list
        start = 2*i-2
        Par['Mic_Pos_Name'] = Par['Mic_Pos_Liste'][start:start+2]
        Par['Mic_Pos_Name_ZF'] = Par['Mic_Pos_Liste_ZF'][i-1]
        G_Emergenz_Zusammenfassung_ANTRIEB_v07(Par)


if __name__ == '__main__':
    main()
