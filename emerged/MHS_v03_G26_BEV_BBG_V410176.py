"""
Converted from MHS_v03_G26_BEV_BBG_V410176.m
Script to run MHS calculations for multiple microphone positions.
"""
from G_MHS_Berechnung_v03 import G_MHS_Berechnung_v03


def main():
    Par = {}
    Par['Name_MHS_Kurven_plot'] = 'G26 BEV BBG V410176 (14.11.2019 08:16)'
    Par['Name_MHS_Kurven_save'] = 'G26_BEV_BBG_V410176'

    Par['v'] = list(range(10, 151, 10))
    Par['Mic_Pos_Liste'] = ['VL_li','VL_re','HR_li','HR_re']

    for i in range(1, len(Par['Mic_Pos_Liste'])+1):
        Par['Mic_Pos_Name'] = Par['Mic_Pos_Liste'][i-1]
        G_MHS_Berechnung_v03(Par)


if __name__ == '__main__':
    main()
