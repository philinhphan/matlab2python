function [] = G_Emergenz_Verteilung_ANTRIEB_BEV_v07(Par)

save("pre_convert_state.mat")

Mic_Pos_Name = Par.Mic_Pos_Name;
Name_Messung_Plot = [Par.Name_Messung_Plot ' ' Mic_Pos_Name];
Name_Emergenz_save = [Par.Name_Emergenz_save '_' Mic_Pos_Name];
save_path = ['Emergenz\',Name_Emergenz_save,'\'];

FBereiche = [[0 1413] [1413 4467] [4467 30000]]; % Grenzen der Frequenzbereiche in Hz
Anzahl_FBereiche = floor(length(FBereiche)/2);

meas = load([save_path 'Emergenz_Auswertung.mat']);
Emergenz_Array = meas.('Emergenz_Array');
v = meas.('v');
Abgl_Z = meas.('Abgl_Z');
iGes = meas.('iGes');
Udyn = meas.('Udyn');

Emergenz_Array_Gruppen = Emergenz_Array; % < v x Abgl_Z > mit Nummer des entsprechenden Frequenzbereiches
Emergenz_Array_Mittelfrequenz = Emergenz_Array; % < v x Abgl_Z > mit Frequenz bei der mittlerer Gschwindigkeit des Schnittes

for kk = 1:length(v)
    for iz=1:length(Abgl_Z)
        freq_temp = (Abgl_Z(iz)*iGes*v(kk))/(60*0.06*Udyn);
        Emergenz_Array_Mittelfrequenz(kk,iz) = freq_temp;
        fb = 1; % Nummer des Frequenzbereiches
        while freq_temp > FBereiche(2*fb)
            fb = fb+1;
        end
        Emergenz_Array_Gruppen(kk,iz) = fb;
    end
    Emergenz_Array_Gruppen(kk,iz+1) = Anzahl_FBereiche; % LE-Auswertung in der höheren Gruppe
end

Emergenz_Array_Summiert = zeros(length(v),Anzahl_FBereiche);   % Energetische Summe der Tonalität der Ordnungen, die im gleichen v-Schnitt im gleichen Frequenzbereich liegen
Emergenz_Array_Max = zeros(length(v),Anzahl_FBereiche);   % Maximale Tonalität der Ordnungen, die im gleichen v-Schnitt im gleichen Frequenzbereich liegen
Emergenz_Array_Verteilung_N_Z = zeros(length(v),Anzahl_FBereiche); % Anzahl an Ordnungen im jeweiligen Bereich
Emergenz_Array_Verteilung_N_Z_Ton = zeros(length(v),Anzahl_FBereiche); % Anzahl an Ordnungen mit Tonalität > 0 dB im jeweiligen Bereich
for kk = 1:length(v)
    for fb=1:Anzahl_FBereiche
        sum = 0; 
        max_temp = 0;
        idf = find(Emergenz_Array_Gruppen(kk,:)==fb);        
        if ~isempty(idf)
            Emergenz_Array_Verteilung_N_Z(kk,fb) = length(idf);
            for iz=1:length(idf)
                if Emergenz_Array(kk,idf(iz)) > 0
                    sum = sum+10^(Emergenz_Array(kk,idf(iz))/10); % energetische Summe der Tonalitäten > 0 dB
                    Emergenz_Array_Verteilung_N_Z_Ton(kk,fb) = Emergenz_Array_Verteilung_N_Z_Ton(kk,fb)+1;
                end
                if Emergenz_Array(kk,idf(iz)) > max_temp
                    max_temp = Emergenz_Array(kk,idf(iz));
                end
            end
            if sum > 0
                emergenz_temp = 10*log10(sum); % summierte Tonalität im Frequenzbereich
                Emergenz_Array_Summiert(kk,fb) = emergenz_temp;
            end
            Emergenz_Array_Max(kk,fb) = max_temp;
        end
    end
end


pyenv('Version', 'L:\proj\gendes\AUSTAUSCH\GENDES-INTERN\Ihor\python interpreter\python.exe')
pyrunfile('converter_test.py');

load('python_export_vars.mat');

% Plot der Ordnungsverteilung
f = figure;
screen_size = get(0,'ScreenSize');
set(gcf, 'Position', [10 31 0.99*screen_size(3) 0.85*screen_size(4)]);
cmap = colormap(jet(Anzahl_FBereiche));
for fb=1:Anzahl_FBereiche 
    lengendInfo = cell(1,2);
    subtightplot(2,2,fb,[0.1 0.05],[0.1 0.06],[0.05 0.05]);
    hold on
    plot(v,Emergenz_Array_Verteilung_N_Z_Ton(:,fb),'Color',cmap(fb,:),'LineWidth',5);
    plot(v,Emergenz_Array_Verteilung_N_Z(:,fb),'Color',cmap(fb,:),'LineWidth',5,'LineStyle','--');
    set(gca,'XLim',[0 150],'XTick',0:10:150,'YLim',[0 10],'YTick',0:1:10,'FontSize',14); 
    grid on; xlabel('Geschwindigkeit [km/h]','FontSize',14);ylabel('Anzahl Ordnungen [-]','FontSize',14);
    lengendInfo{1} = ['Anzahl der hörbaren Ordnungen im Bereich ' num2str(FBereiche(2*fb-1)/1000) '-' num2str(FBereiche(2*fb)/1000) ' kHz'];
    lengendInfo{2} = ['Anzahl der vorhandenen Ordnungen im Bereich ' num2str(FBereiche(2*fb-1)/1000) '-' num2str(FBereiche(2*fb)/1000) ' kHz'];
    h_legend=legend(lengendInfo,'Location','NorthEast');
    if fb==1 
        t=title(['Luftschall Tonhaltigkeit "' Name_Messung_Plot '"'],'FontSize',18,'HorizontalAlignment','left','interpreter','none');
    end
end

savefig([save_path 'Emergenz_Verteilung']);
set(gcf,'PaperPositionMode','auto');
print(f,[save_path 'Emergenz_Verteilung'],'-dmeta','-r0');

% Plot der summierten Tonhaltigkeit
f = figure;
screen_size = get(0,'ScreenSize');
set(gcf, 'Position', [10 31 0.99*screen_size(3) 0.85*screen_size(4)]);
cmap = colormap(jet(Anzahl_FBereiche));
x_tick_labels = cell(1,length(v));
for kk = 1:length(v)
    x_tick_labels{kk} = num2str(v(kk));
end
for fb=1:Anzahl_FBereiche 
    lengendInfo = cell(1);
    subtightplot(2,2,fb,[0.1 0.05],[0.1 0.06],[0.05 0.05]);     
    bar(Emergenz_Array_Summiert(:,fb),'FaceColor',cmap(fb,:));
    set(gca,'XLim',[0 15],'YLim',[0 20],'XTickLabel',x_tick_labels,'FontSize',14);
    grid on; xlabel('Geschwindigkeit [km/h]','FontSize',14);ylabel('Emergenz [dB(A)]','FontSize',14);
    lengendInfo{1} = ['Summierte Tonhaltigkeit im Bereich ' num2str(FBereiche(2*fb-1)/1000) '-' num2str(FBereiche(2*fb)/1000) ' kHz'];
    h_legend=legend(lengendInfo,'Location','NorthEast');
    if fb==1 
        t=title(['Luftschall Tonhaltigkeit "' Name_Messung_Plot '"'],'FontSize',18,'HorizontalAlignment','left','interpreter','none');
    end    
end

savefig([save_path 'Emergenz_Summiert']);
set(gcf,'PaperPositionMode','auto');
print(f,[save_path 'Emergenz_Summiert'],'-dmeta','-r0');

% Plot der summierten Tonhaltigkeit mit maximaler Tonalität
f = figure;
screen_size = get(0,'ScreenSize');
set(gcf, 'Position', [10 31 0.99*screen_size(3) 0.85*screen_size(4)]);
cmap = colormap(jet(Anzahl_FBereiche));
x_tick_labels = cell(1,length(v));
for kk = 1:length(v)
    x_tick_labels{kk} = num2str(v(kk));
end
for fb=1:Anzahl_FBereiche 
    lengendInfo = cell(1,2);
    subtightplot(2,2,fb,[0.1 0.05],[0.1 0.06],[0.05 0.05]); 
    h = bar([Emergenz_Array_Summiert(:,fb) Emergenz_Array_Max(:,fb)],'BarWidth',1.5); 
    temp = get(gca,'Children');
    set(temp(2),'FaceColor',cmap(fb,:));  % summierte Tonalität: dunkle Farben
    set(temp(1),'FaceColor',Light(cmap(fb,:),20));  % maximale Tonalität: helle Farben
    set(gca,'XLim',[0 15],'YLim',[0 20],'XTickLabel',x_tick_labels,'FontSize',14);
    grid on; xlabel('Geschwindigkeit [km/h]','FontSize',14);ylabel('Emergenz [dB(A)]','FontSize',14);
    lengendInfo{1} = ['Summierte Tonhaltigkeit im Bereich ' num2str(FBereiche(2*fb-1)/1000) '-' num2str(FBereiche(2*fb)/1000) ' kHz'];
    lengendInfo{2} = ['Maximale Tonalität im Bereich ' num2str(FBereiche(2*fb-1)/1000) '-' num2str(FBereiche(2*fb)/1000) ' kHz'];
    h_legend=legend(lengendInfo,'Location','NorthEast');
    if fb==1 
        t=title(['Luftschall Tonhaltigkeit "' Name_Messung_Plot '"'],'FontSize',18,'HorizontalAlignment','left','interpreter','none');
    end  
end

savefig([save_path 'Emergenz_Summiert_Max']);
set(gcf,'PaperPositionMode','auto');
print(f,[save_path 'Emergenz_Summiert_Max'],'-dmeta','-r0');

% Plot der maximalen Tonhaltigkeit im Vergleich mit den Emergenz-Zielkurven
zk = load('Emergenz_Zielkurven_v2.mat');        

Zielkurven = zeros(15,5,3);
Zielkurven(:,:,1) = zk.('Zielkurven_0_1250Hz_Heulen');
Zielkurven(:,:,2) = zk.('Zielkurven_1250_4000Hz_Pfeifen');
Zielkurven(:,:,3) = zk.('Zielkurven_4000Hz_Piepsen');

f = figure;
screen_size = get(0,'ScreenSize');
set(gcf, 'Position', [10 31 0.99*screen_size(3) 0.85*screen_size(4)]);
cmap = colormap(jet(Anzahl_FBereiche));
cmap_zielkurven = [[0 0 0]; [244 177 131]./255; [237 125 49]./255; [197 90 17]./255; [132 60 12]./255;];
x_tick_labels = cell(1,length(v));
for kk = 1:length(v)
    x_tick_labels{kk} = num2str(v(kk));
end
for fb=1:Anzahl_FBereiche 
    lengendInfo = cell(1,1);
    subtightplot(2,2,fb,[0.1 0.05],[0.1 0.06],[0.05 0.05]); 
    h = bar(Emergenz_Array_Max(:,fb),'FaceColor',cmap(fb,:));            
    set(gca,'XLim',[0 15],'YLim',[0 20],'XTickLabel',x_tick_labels,'FontSize',14);
    grid on; xlabel('Geschwindigkeit [km/h]','FontSize',14);ylabel('Emergenz [dB(A)]','FontSize',14);
    lengendInfo{1} = ['Maximale Tonalität im Bereich ' num2str(FBereiche(2*fb-1)/1000) '-' num2str(FBereiche(2*fb)/1000) ' kHz'];    
    hold on;
    for z=(1:5) plot (1:1:15, Zielkurven(:,z,fb), 'color', cmap_zielkurven(z,:), 'linewidth',3) ;        
    end
    if fb ==1 % Legende für die Zielkurven nur im linken oberen Bild
        lengendInfo{2} = 'Obergrenze für "unhörbar"';
        lengendInfo{3} = 'Obergrenze für "leise"';
        lengendInfo{4} = 'Obergrenze für "dezent"';
        lengendInfo{5} = 'Obergrenze für "präsent"';
        lengendInfo{6} = 'Obergrenze für "dominant"';
    end    
    h_legend=legend(lengendInfo,'Location','NorthEast');
    if fb==1 
        t=title(['Luftschall Tonhaltigkeit "' Name_Messung_Plot '"'],'FontSize',18,'HorizontalAlignment','left','interpreter','none');
    end  
end

savefig([save_path 'Emergenz_Max']);
set(gcf,'PaperPositionMode','auto');
print(f,[save_path 'Emergenz_Max'],'-dmeta','-r0');


close all

save([save_path 'Emergenz_Verteilung.mat']);        
        
end        