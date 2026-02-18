function [] = G_Emergenz_Spinne_ANTRIEB_BEV_v07(Par)

%% Berechnete Daten laden
Mic_Pos_Name = Par.Mic_Pos_Name;
Name_Messung_Plot = [Par.Name_Messung_Plot ' ' Mic_Pos_Name];
Name_Emergenz_save = [Par.Name_Emergenz_save '_' Mic_Pos_Name];
save_path = ['Emergenz\',Name_Emergenz_save,'\'];
load([save_path 'Emergenz_Verteilung.mat']);

load('Emergenz_Zielkurven_v2.mat');

%% Fahrzeug-Auswertung
plot_max = 1; % 1/0: mit/ohne Darstellung der Peaks der Emergenz
plot_median = 1; % 1/0: mit/ohne Darstellung der Medianwerte der Emergenz
ziel_fahrzeug_charakter = Par.ziel_fahrzeug_charakter; % 0 = unhörbar, 1 = leise, 2 = dezent, 3 = präsent, 4 = dominant

Emergenz_Array_Max_Abgl = Emergenz_Array_Max; % Abgleich gemessene Emergenz / Grenzwerte
Emergenz_Array_Max_Abgl_Max = nan(4,4); % Minimale Position (~ max Emergenz) pro Geschwindigkeitsbereich (Langsam, Stadt, Land, BAB)
Emergenz_Array_Max_Abgl_Median = nan(4,4); % Mediane Position (~ mediane Emergenz) pro Geschwindigkeitsbereich (Langsam, Stadt, Land, BAB)
id_langsam = find(v<=30);
id_stadt = find(v>30 & v<=80);
id_land = find(v>80 & v<=120);
id_bab = find(v>=130);

for fb=1:Anzahl_FBereiche
    
    if fb == 1
        toleranz_ziel = 1;
        zielkurven = Zielkurven_0_1250Hz_Heulen;
    elseif fb == 2
        toleranz_ziel = 1;
        zielkurven = Zielkurven_1250_4000Hz_Pfeifen;
    elseif fb == 3
        toleranz_ziel = 0.5;
        zielkurven = Zielkurven_4000Hz_Piepsen;    
    end
    
    for i=1:length(Emergenz_Array_Max) % Schleife über die Geschwindigkeitsschritte
        emergenz_messwert = Emergenz_Array_Max(i,fb);
        pos_messwert = 8;
		
		%%% Use for loop?
		
        j=1;
        while j<6
            if (emergenz_messwert > zielkurven(i,j)+toleranz_ziel)
                pos_messwert = pos_messwert-0.5;
                if (j<5) && (emergenz_messwert > zielkurven(i,j+1)-toleranz_ziel)
                    pos_messwert = pos_messwert-0.5;
                end
                if (j==5) && (emergenz_messwert > zielkurven(i,j)+2*toleranz_ziel)
                    pos_messwert = pos_messwert-0.5;
                end
            end
            j=j+1;
        end
        Emergenz_Array_Max_Abgl(i,fb) = pos_messwert;
    end
    if ~isempty(id_langsam)
        Emergenz_Array_Max_Abgl_Max(1,fb) = min(Emergenz_Array_Max_Abgl(id_langsam,fb));
        Emergenz_Array_Max_Abgl_Median(1,fb) = median(Emergenz_Array_Max_Abgl(id_langsam,fb));
    end
    if ~isempty(id_stadt)
        Emergenz_Array_Max_Abgl_Max(2,fb) = min(Emergenz_Array_Max_Abgl(id_stadt,fb));
        Emergenz_Array_Max_Abgl_Median(2,fb) = median(Emergenz_Array_Max_Abgl(id_stadt,fb));
    end
    if ~isempty(id_land)
        Emergenz_Array_Max_Abgl_Max(3,fb) = min(Emergenz_Array_Max_Abgl(id_land,fb));
        Emergenz_Array_Max_Abgl_Median(3,fb) = median(Emergenz_Array_Max_Abgl(id_land,fb));
    end
    if ~isempty(id_bab)
        Emergenz_Array_Max_Abgl_Max(4,fb) = min(Emergenz_Array_Max_Abgl(id_bab,fb));
        Emergenz_Array_Max_Abgl_Median(4,fb) = median(Emergenz_Array_Max_Abgl(id_bab,fb));
    end
end


%% Plot

openfig('Spinne_Vorlage_v6.fig');
hold on

% Grenzen Zielkurven
% Dominant
h(1) = polar(0:2*pi/100:2*pi,4*ones(1,101),'--');
set(h(1),'LineWidth',2.5,'Color',[132 60 12]./255);
% Präsent
h(2) = polar(0:2*pi/100:2*pi,5*ones(1,101),'--');
set(h(2),'LineWidth',2.5,'Color',[197 90 17]./255);
% Dezent
h(3) = polar(0:2*pi/100:2*pi,6*ones(1,101),'--');
set(h(3),'LineWidth',2.5,'Color',[237 125 49]./255);
% Leise
h(4) = polar(0:2*pi/100:2*pi,7*ones(1,101),'--');
set(h(4),'LineWidth',2.5,'Color',[244 177 131]./255);
% Mithörschwelle
h(5) = polar(0:2*pi/100:2*pi,8*ones(1,101),'--');
set(h(5),'LineWidth',2.5,'Color','k');
% Ziel Fahrzeug-Charakter
h(6) = polar(0:2*pi/50:2*pi,(8-ziel_fahrzeug_charakter)*ones(1,51),'go');
set(h(6),'LineWidth',5);

legend_text = {'E-Antrieb "dominant"','E-Antrieb "präsent"','E-Antrieb "dezent"','E-Antrieb "leise"','E-Antrieb "unhörbar"','Fahrzeug Emergenz-Ziel'};



%%% A lot of repeated code

% Fahrzeug-Auswertung
plot_color = 'b';
ct = 1;
if ~isempty(id_langsam)
    if plot_max == 1
        h(6+ct) = polar(pi-2*pi/20:-2*pi/20:pi/2+2*pi/20,Emergenz_Array_Max_Abgl_Max(1,:),':o');
        set(h(6+ct),'LineWidth',5,'Color',plot_color,'MarkerFaceColor',plot_color);
        legend_text{1,6+ct} = sprintf([Name_Messung_Plot '\n- Maximale Emergenz']);
        ct = ct+1;
    end
    if plot_median == 1
        h(6+ct) = polar(pi-2*pi/20:-2*pi/20:pi/2+2*pi/20,Emergenz_Array_Max_Abgl_Median(1,:),'-s');
        set(h(6+ct),'LineWidth',6,'Color',plot_color,'MarkerFaceColor',plot_color);
        legend_text{1,6+ct} = sprintf([Name_Messung_Plot '\n- Mediane Emergenz']);
        ct = ct+1;
    end
end
if ~isempty(id_stadt)
    if plot_max == 1
        h(6+ct) = polar(pi/2-2*pi/20:-2*pi/20:2*pi/20,Emergenz_Array_Max_Abgl_Max(2,:),':o');
        set(h(6+ct),'LineWidth',5,'Color',plot_color,'MarkerFaceColor',plot_color);
        ct = ct+1;
    end
    if plot_median == 1
        h(6+ct) = polar(pi/2-2*pi/20:-2*pi/20:2*pi/20,Emergenz_Array_Max_Abgl_Median(2,:),'-s');
        set(h(6+ct),'LineWidth',6,'Color',plot_color,'MarkerFaceColor',plot_color);
        ct = ct+1;
    end
end
if ~isempty(id_land)
    if plot_max == 1
        h(6+ct) = polar(-2*pi/20:-2*pi/20:-pi/2+2*pi/20,Emergenz_Array_Max_Abgl_Max(3,:),':o');
        set(h(6+ct),'LineWidth',5,'Color',plot_color,'MarkerFaceColor',plot_color);
        ct = ct+1;
    end
    if plot_median == 1
        h(6+ct) = polar(-2*pi/20:-2*pi/20:-pi/2+2*pi/20,Emergenz_Array_Max_Abgl_Median(3,:),'-s');
        set(h(6+ct),'LineWidth',6,'Color',plot_color,'MarkerFaceColor',plot_color);
        ct = ct+1;
    end
end
if ~isempty(id_bab)
    if plot_max == 1
        h(6+ct) = polar(-2*pi/20-pi/2:-2*pi/20:-pi+2*pi/20,Emergenz_Array_Max_Abgl_Max(4,:),':o');
        set(h(6+ct),'LineWidth',5,'Color',plot_color,'MarkerFaceColor',plot_color);
        ct = ct+1;
    end
    if plot_median == 1
        h(6+ct) = polar(-2*pi/20-pi/2:-2*pi/20:-pi+2*pi/20,Emergenz_Array_Max_Abgl_Median(4,:),'-s');
        set(h(6+ct),'LineWidth',6,'Color',plot_color,'MarkerFaceColor',plot_color);
        ct = ct+1;
    end
end

% Grenzen v-Bereiche
h20 = polar(pi/2*ones(1,9),0:1:8,'k');
set(h20,'LineWidth',5);
h21 = polar(0*ones(1,9),0:1:8,'k');
set(h21,'LineWidth',5);
h22 = polar(pi*ones(1,9),0:1:8,'k');
set(h22,'LineWidth',5);
h23 = polar(-pi/2*ones(1,9),0:1:8,'k');
set(h23,'LineWidth',5);

h24 = polar(-2*2*pi/20*ones(1,9),0:1:8,':k');
set(h24,'LineWidth',1);
h25 = polar(-3*2*pi/20*ones(1,9),0:1:8,':k');
set(h25,'LineWidth',1);
h26 = polar(7*2*pi/20*ones(1,9),0:1:8,':k');
set(h26,'LineWidth',1);
h27 = polar(8*2*pi/20*ones(1,9),0:1:8,':k');
set(h27,'LineWidth',1);

h_legend = legend(h(1:6+plot_max+plot_median),legend_text,'interpreter','none');
h_legend_pos = get(h_legend,'Position');
set(h_legend,'FontSize',14,'Position',[0.75 0.45 0.23 h_legend_pos(4)]);

savefig(gcf,[save_path 'Emergenz_Spinne']);
set(gcf,'PaperPositionMode','auto');
print(gcf,[save_path 'Emergenz_Spinne'],'-dpng','-r0');

close all

save([save_path 'Emergenz_Spinne.mat']);

end