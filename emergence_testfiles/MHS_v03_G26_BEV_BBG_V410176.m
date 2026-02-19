addpath("emergence\")
clc;
clear all; 

%% Input Parameter
% Name der Berechnung
Par.Name_MHS_Kurven_plot = 'G26 BEV BBG V410176 (14.11.2019 08:16)';     % Title Plots
Par.Name_MHS_Kurven_save = 'G26_BEV_BBG_V410176';                        % Name des Speicher-Ordners im Ordner "MHS Kurven"

% Geschwindigkeitsziele
Par.v = 10:10:150;                                           % Geschwindigkeiten der Wind-Roll-Geräusch Kurven (10:10:150)
Par.Mic_Pos_Liste = {'VL_li','VL_re','HR_li','HR_re'};       % Bezeichnung Position Mikrophon {'VL_li','VL_re','HR_li','HR_re'};

%% Berechnungen
% Auswertungsschleife für die verschiedenen Mikros
for i = 1:length(Par.Mic_Pos_Liste)                      
    Par.Mic_Pos_Name = Par.Mic_Pos_Liste{i};
    G_MHS_Berechnung_v03(Par);
end
