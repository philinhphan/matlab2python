function [] = G_Emergenz_Auswertung_ANTRIEB_BEV_v07(Par)


%%% Refactor to use multiple named arguments instead of Par var

%% Parameter und Daten einlesen
Mic_Pos_Name = Par.Mic_Pos_Name;
%Mic_Pos_Liste = Par.Mic_Pos_Liste;
Name_Emergenz_save = [Par.Name_Emergenz_save '_' Mic_Pos_Name];
Name_MHS_Kurven_Ordner = Par.Name_MHS_Kurven_Ordner;
Name_Messdaten_Ordner = Par.Name_Messdaten_Ordner;
Name_Messung = Par.Name_Messung;
Name_Messung_Plot = [Par.Name_Messung_Plot ' ' Mic_Pos_Name];


%%% Use strcat for ('Mic__', Mic_Pos_Name, '_Ohr_S')?
%%% Use predefined dictionary?
%%% Use spacing for math equations?


if strcmp(Mic_Pos_Name,'VL_li') > 0
    Mic_Pos = 'Mic__VL_li_Ohr_S';
elseif strcmp(Mic_Pos_Name,'VL_re') > 0
    Mic_Pos = 'Mic__VL_re_Ohr_S';
elseif strcmp(Mic_Pos_Name,'VR_li') > 0
    Mic_Pos = 'Mic__VR_li_Ohr_S';
elseif strcmp(Mic_Pos_Name,'VR_re') > 0
    Mic_Pos = 'Mic__VR_re_Ohr_S';    
elseif strcmp(Mic_Pos_Name,'HL_li') > 0
    Mic_Pos = 'Mic__HL_li_Ohr_S';
elseif strcmp(Mic_Pos_Name,'HL_re') > 0
    Mic_Pos = 'Mic__HL_re_Ohr_S';    
elseif strcmp(Mic_Pos_Name,'HR_li') > 0
    Mic_Pos = 'Mic__HR_li_Ohr_S';
elseif strcmp(Mic_Pos_Name,'HR_re') > 0
    Mic_Pos = 'Mic__HR_re_Ohr_S';
end
Par.Mic_Pos = Mic_Pos;


%%% Separate load from main script

meas_curves = load(['MHS Kurven\' Name_MHS_Kurven_Ordner '_' Mic_Pos_Name '\' Name_MHS_Kurven_Ordner '_' Mic_Pos_Name '_Ziele_Innenraum.mat']);

freq = meas_curves.('freq');
fy = meas_curves.('fy');
Lmhs_array = meas_curves.('Lmhs_array');
specs = meas_curves.('specs');


v = Par.v;                         % v_WRG
v_meas = Par.v_meas;               % [untere Freq,obere Freq]
v_aufloesung = 2;                  % km/h (Auflösung der v-Schritte im PAK-Export)

meas_ges = load(['Messdaten\' Name_Messdaten_Ordner '\' Mic_Pos_Name '\' Name_Messung 'APS_Gesamt.mat']);

freq_meas = meas_ges.([Mic_Pos '_X']);
meas = zeros(length(freq),length(v));

iGes = Par.iGes; % Gesamtübersetzung im x. Gang

RB=Par.RB;    % Reifenbreite (mm)
QV=Par.QV;    % Querschnittsverhältnis (%)
FD=Par.FD;    % Felgendurchmesser (Zoll)
KY=0.97;      % Koeffizient stat->dyn Radumfang (-)
Udyn = (25.4*FD + 2*RB*QV/100)*(pi*KY/1000); % dynamischer Radumfang

Abgl_Z = sort(Par.Abgl_Z);

freq_PWM = Par.freq_PWM;

mkdir('Emergenz\',Name_Emergenz_save);
save_path = ['Emergenz\',Name_Emergenz_save,'\'];


%%% Use proper iterator name?
%%% Use array slicing?

for jj = 1:length(v)
    if jj == 1
        meas(:,jj) = 20*log10(meas_ges.(Mic_Pos)/(2*10^-5));
    elseif jj < 11
        meas(:,jj) = 20*log10(meas_ges.([Mic_Pos '_0' num2str(jj-1)])/(2*10^-5));
    else
        meas(:,jj) = 20*log10(meas_ges.([Mic_Pos '_' num2str(jj-1)])/(2*10^-5));
    end
end

%% Berechnung
% Emergenz_Array = pyrunfile('converter_test.py', 'Emergenz_Array');

Emergenz_Array = zeros(length(v),length(Abgl_Z)+1);
v_meas_ungefiltert = [[5 15] [15 25] [25 35] [35 45] [45 55] [55 65] [65 75] [75 85] [85 95] [95 105] [105 115] [115 125] [125 135] [135 145] [145 155]]; % [untere v, obere v]
v_meas_ungefiltert = v_meas_ungefiltert(1:length(v_meas));

save('pre_convert_state')
for kk = 1:length(v)
        
    v_grenzen = v_meas(2*kk-1:2*kk);
    v_grenzen_anfang = num2str(v_grenzen(1));
    v_grenzen_anfang = str2num(v_grenzen_anfang(end));  % Beginnt der v-Bereich mit 5/15/25... km/h? --> v_grenzen_anfang=5
    v_grenzen_ungefiltert = v_meas_ungefiltert(2*kk-1:2*kk);
    verschiebung = floor((v_grenzen(1)-v_grenzen_ungefiltert(1))/v_aufloesung); % Beispiel: [7 15] --> verschiebung=1 
    anzahl_v_bereiche = ceil((v_grenzen(2)-v_grenzen(1))/v_aufloesung);
    
    meas_kmh = load(['Messdaten\' Name_Messdaten_Ordner '\' Mic_Pos_Name '\' Name_Messung 'APS_' num2str(v(kk)) 'kmh.mat']);   

    freq_meas_unterteilt = meas_kmh.([Mic_Pos '_X']);
    meas_unterteilt = zeros(length(freq),anzahl_v_bereiche);
    
    for vv=1:anzahl_v_bereiche
        if vv == 1
            if ismember(v_grenzen_anfang,[5 6])
                meas_unterteilt(:,vv) = 20*log10(meas_kmh.(Mic_Pos)/(2*10^-5));                
            else                
                meas_unterteilt(:,vv) = 20*log10(meas_kmh.([Mic_Pos '_0' num2str(verschiebung)])/(2*10^-5));                
            end
        elseif vv < 11
            meas_unterteilt(:,vv) = 20*log10(meas_kmh.([Mic_Pos '_0' num2str(vv-1+verschiebung)])/(2*10^-5));            
        else
            meas_unterteilt(:,vv) = 20*log10(meas_kmh.([Mic_Pos '_' num2str(vv-1+verschiebung)])/(2*10^-5));
        end
    end
    
    for vv=1:anzahl_v_bereiche
        v_grenzen_unterteilt = [v_grenzen(1)+2*(vv-1) v_grenzen(1)+2*(vv)];
        for iz=1:length(Abgl_Z)
            OF_v(iz,:) = (Abgl_Z(iz)*iGes*v_grenzen_unterteilt)./(60*0.06*Udyn);
            idx = find(freq_meas_unterteilt(:,1)<=ceil(1.01*OF_v(iz,2)) & freq_meas(:,1)>=floor(0.99*OF_v(iz,1)));  % Annahme 1% Fehler in der Geschwindkeit bzw. Frequenz der Ordnung
            Emergenz = 0;
            for i=1:length(idx)
                freq_temp = freq_meas_unterteilt(idx(i),1);
                idxi = find(fy(:,1) == freq_temp);
                Emergenz_temp = meas_unterteilt(idx(i),vv)-Lmhs_array(idxi,kk);
                if Emergenz_temp > Emergenz
                    Emergenz = Emergenz_temp;
                end
            end
            if Emergenz > Emergenz_Array(kk,iz)
                Emergenz_Array(kk,iz) = Emergenz;
            end
        end
        % Auswertung LE
        freq_suchbereich = [max(4000,freq_PWM/2) freq_meas(end)];
        if freq_PWM+OF_v(iz,2) < freq_meas(end)
            freq_suchbereich(2) = freq_PWM+OF_v(iz,2);
        end
        if freq_PWM-OF_v(iz,2) > max(4000,freq_PWM/2)
            freq_suchbereich(1) = freq_PWM-OF_v(iz,2);
        end
        Emergenz = 0;
        for i=1:length(freq_meas_unterteilt)
            if (freq_meas_unterteilt(i) >= freq_suchbereich(1)) && (freq_meas_unterteilt(i) <= freq_suchbereich(2))
                idxj = find((OF_v(:,1)-100 <= freq_meas_unterteilt(i)) & (OF_v(:,2)+100 >= freq_meas_unterteilt(i)));
                if isempty(idxj)
                    idxi = find(fy(:,1) == freq_meas_unterteilt(i));
                    Emergenz_temp = meas_unterteilt(i,vv)-Lmhs_array(idxi,kk);
                    if Emergenz_temp > Emergenz
                        Emergenz = Emergenz_temp;
                    end
                end
            end
        end
        if Emergenz > Emergenz_Array(kk,iz+1)
            Emergenz_Array(kk,iz+1) = Emergenz;
        end
    end
    % Emergenz aus Ordnungen unterscheiden von Emergenz aus LE
    id_le = find(Emergenz_Array(kk,1:length(Abgl_Z)) == Emergenz_Array(kk,end));
    if ~isempty(id_le)
        Emergenz_Array(kk,end) = 0;
    end
end


%% Plots

%load(['Messdaten\' Name_Messdaten_Ordner '\' Mic_Pos_Name '\' Name_Messung 'APS_Gesamt.mat']);

cmap = colormap(jet(length(Abgl_Z)));
for kk = 1:length(v)
    legendInfo = {};
    f = figure;
    semilogx(fy,Lmhs_array(:,kk),'Color','k','LineWidth',5);
    legendInfo{1} = ['Mithörschwelle ' num2str(v(kk)) ' km/h'];
    hold on;
    semilogx(freq,specs(:,kk),'Color',[0.5 0.5 0.5],'LineWidth',5);
    legendInfo{2} = ['Mittelung WRG ' num2str(v(kk)) ' km/h'];
    hold on;
    semilogx(freq_meas,meas(:,kk),'Color','k','LineWidth',1);
    legendInfo{3} = ['Max gemessen ' num2str(v(kk)) ' km/h'];    
    for iz=1:length(Abgl_Z)
        v_grenzen = [v(kk)-5 v(kk)+5];
        OF_v(iz,:) = (Abgl_Z(iz)*iGes*v_grenzen)./(60*0.06*Udyn);
        idx = find(freq_meas(:,1)<=OF_v(iz,2) & freq_meas(:,1)>=OF_v(iz,1));
        if ~isempty(idx)
            semilogx(freq_meas(idx,1),meas(idx,kk),'Color',cmap(iz,:),'LineWidth',2);
            Emergenz = Emergenz_Array(kk,iz);
            size_legendInfo = length(legendInfo);
            if Emergenz <= 0
                legendInfo{size_legendInfo+1} = ['Max gemessen ' num2str(v(kk)) ' km/h - ' num2str(Abgl_Z(iz)) '. Ordnung'];
            else
                legendInfo{size_legendInfo+1} = ['Max gemessen ' num2str(v(kk)) ' km/h - ' num2str(Abgl_Z(iz)) '. Ordnung - Emergenz ' num2str(round(Emergenz*10)/10) ' dB'];
            end            
        end
    end
    semilogx(freq_meas,meas(:,kk),'Color','k','LineWidth',1,'visible','off');
    size_legendInfo = length(legendInfo);
    if Emergenz_Array(kk,iz+1) <= 0
        legendInfo{size_legendInfo+1} = ['Max gemessen ' num2str(v(kk)) ' km/h - LE'];
    else
        legendInfo{size_legendInfo+1} = ['Max gemessen ' num2str(v(kk)) ' km/h - LE - Emergenz ' num2str(round(Emergenz_Array(kk,iz+1)*10)/10) ' dB'];
    end
    screen_size = get(0,'ScreenSize');
    set(gcf, 'Position', [10 31 0.99*screen_size(3) 0.85*screen_size(4)]);
    set(gca,'XLim',[10 15000],'FontSize',14);
    h_legend=legend(legendInfo,'Location','Best');
    set(h_legend,'FontSize',14);
    grid on; xlabel('Frequenz [Hz]','FontSize',14);ylabel('Innenraum Schalldruckpegel [dB(A)]','FontSize',14);
    title(['LS Abgleich Schmallband aus der Messung "' Name_Messung_Plot '" / Mithörschwelle aus dem Ausrollen (nach DIN 45681) - ' num2str(v(kk)) ' km/h'],'FontSize',18,'interpreter','none');
    hold off;
    
    savefig([save_path 'Emergenz_' num2str(v(kk)) '_kmh']);
    set(gcf,'PaperPositionMode','auto');
    print(f,[save_path 'Emergenz_' num2str(v(kk)) '_kmh'],'-dmeta','-r0');
end

f = figure;
cmap = colormap([jet(length(Abgl_Z));[0 0 0]]);
legendInfo = cell(1,length(Abgl_Z)+1);
for iz=1:length(Abgl_Z)+1
    mittelwert_temp = num2str(round(mean(Emergenz_Array(:,iz))*10)/10);
    maxwert_temp = num2str(round(max(Emergenz_Array(:,iz))*10)/10);
    if iz<=length(Abgl_Z)
        legendInfo{iz} = ['Emergenz ' num2str(Abgl_Z(iz)) '. Ordnung (Mittel ' mittelwert_temp ' dB, Max ' maxwert_temp ' dB)'];
    else
        legendInfo{iz} = ['Emergenz LE (Mittel ' mittelwert_temp ' dB, Max ' maxwert_temp ' dB)'];
    end
end
x_tick_labels = cell(1,length(v));
for kk = 1:length(v)
    x_tick_labels{kk} = num2str(v(kk));
end
bar(Emergenz_Array,'grouped','BarWidth',1);
screen_size = get(0,'ScreenSize');
set(gcf, 'Position', [10 31 0.99*screen_size(3) 0.85*screen_size(4)]);
set(gca,'XLim',[0 15],'YLim',[0 20],'XTickLabel',x_tick_labels,'FontSize',14);
h_legend=legend(legendInfo,'Location','Best');
set(h_legend,'FontSize',14);
grid on; xlabel('Geschwindigkeit [km/h]','FontSize',14);ylabel('Emergenz [dB(A)]','FontSize',14);
title(['LS Abgleich Schmallband aus der Messung "' Name_Messung_Plot '" / Mithörschwelle aus dem Ausrollen (nach DIN 45681)'],'FontSize',18,'interpreter','none');

savefig([save_path 'Emergenz_Zusammenfassung']);
set(gcf,'PaperPositionMode','auto');
print(f,[save_path 'Emergenz_Zusammenfassung'],'-dmeta','-r0');

close all

save([save_path 'Emergenz_Auswertung.mat']);

end