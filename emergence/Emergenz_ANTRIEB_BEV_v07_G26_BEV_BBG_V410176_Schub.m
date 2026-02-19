addpath("emergence\")
clc;
clear all; 

%% Input Parameter
Par.Name_MHS_Kurven_Ordner = 'G26_BEV_BBG_V410176';               % Quelle-Ordner unter "MHS Kurven" --> Mithörschwellen aus Wind-Roll-Geräusch
Par.Name_Messdaten_Ordner = 'SDSA';                               % Quelle-Ordner unter "Messdaten" --> Zyklus auszuwerten
Par.Name_Messung = 'BMW i4 80 sD #H019370#14.11.2019#10_59#SD#';  % Name der exportierten PAK-Messdaten
Par.Name_Emergenz_save = 'G26_BEV_BBG_V410176_Schub_test02';             % Output-Ordner für die Emergenz-Auswertung (wird automatisch angelegt)
Par.Name_Messung_Plot = 'G26 BEV BBG V410176 Schub (14.11.2019 10:57)';    % Titel Plots

Par.Mic_Pos_Liste = {'VL_li','VL_re','HR_li','HR_re'};     % Bezeichnung Position Mikrophon {'VL_li','VL_re','HR_li','HR_re'}; 
Par.Mic_Pos_Liste_ZF = {'Fahrer','Fond'};                  % Bezeichnung Sitzposition (Zusammenfassung 2 Mikrophone)     {'Fahrer','Fond'}; 

Par.v = 10:10:140; % Geschwindigkeitsschritte des Antriebszyklus auszuwerten
% Grenzwerte der Geschwindigkeitsschritte (exportierte Spektren inkl. Filtern um Störgeräusche auszuschliessen) 
Par.v_meas = [[5 15] [15 25] [25 35] [35 45] [45 55] [55 65] [65 75] [75 85] [85 95] [95 105] [105 115] [115 125] [125 135] [135 145]]; % [untere v, obere v]

Par.iGes = 11.12;     % Gesamtübersetzung im x. Gang 

Par.RB = 245;     % Reifenbreite (mm)
Par.QV = 45;      % Querschnittsverhältnis (%)
Par.FD = 18;      % Felgendurchmesser (Zoll)

Par.Abgl_Z = sort([1 2 3 4 5 6 7 14 18 23 46 54]);   % Motor-Ordnungen auszuwerten 
Par.freq_PWM = 8000;                                 % PWM-Frequenz der Leistungselektronik

% Spinne-Darstellung 
Par.ziel_fahrzeug_charakter = 1;    % 0 = unhörbar, 1 = leise, 2 = dezent, 3 = präsent, 4 = dominant

%% Berechnung und Auswertung
% Auswertungsschleife für die verschiedenen Mikros
for i = 1:length(Par.Mic_Pos_Liste)                      
    Par.Mic_Pos_Name = Par.Mic_Pos_Liste{i};  
    G_Emergenz_Auswertung_ANTRIEB_BEV_v07(Par);   % primäre Auswertung der Deltas Antriebstöne/MHS
    G_Emergenz_Verteilung_ANTRIEB_BEV_v07(Par);   % Verteilung der Emergenz-Werte in Frequenzbereichen und Abgleich mit Grenzkurven
    G_Emergenz_Spinne_ANTRIEB_BEV_v07(Par);       % Darstellung der Emergenz im Spinne-Diagramm
end
% Zusammenfassung von 2 Mikros
for i = 1:length(Par.Mic_Pos_Liste_ZF)
    Par.Mic_Pos_Name = Par.Mic_Pos_Liste(1,2*i-1:2*i);
    Par.Mic_Pos_Name_ZF = Par.Mic_Pos_Liste_ZF{i};
    G_Emergenz_Zusammenfassung_ANTRIEB_v07(Par);   % Emergenz-Maximum über 2 Ohrpositionen (z.B. Fahrerohr links/rechts)
end
