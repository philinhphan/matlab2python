function [] = G_Emergenz_Zusammenfassung_ANTRIEB_v07(Par)

%% Vorbereitung
Mic_Pos_Name = Par.Mic_Pos_Name;
Mic_Pos_Name_ZF = Par.Mic_Pos_Name_ZF;
Name_Emergenz_save = Par.Name_Emergenz_save;
Name_Emergenz_save_ZF = [Par.Name_Emergenz_save '_' Mic_Pos_Name_ZF];
save_path_ZF = ['Emergenz\',Name_Emergenz_save_ZF,'\'];
mkdir(save_path_ZF);
Name_Messung_Plot_ZF = [Par.Name_Messung_Plot ' ' Mic_Pos_Name_ZF];

ziel_fahrzeug_charakter = Par.ziel_fahrzeug_charakter; % 0 = unhörbar, 1 = leise, 2 = dezent, 3 = präsent, 4 = dominant
plot_max = 1; % 1/0: mit/ohne Darstellung der Peaks der Emergenz
plot_median = 1; % 1/0: mit/ohne Darstellung der Medianwerte der Emergenz

% Fahrzeug-Auswertungen importieren
% Fzg 1
Par_Fzg_1 = load(['Emergenz\' Name_Emergenz_save '_' Mic_Pos_Name{1} '\Emergenz_Spinne.mat'],'Emergenz_Array_Max','id_langsam','id_stadt','id_land','id_bab','Emergenz_Array_Max_Abgl_Max','Emergenz_Array_Max_Abgl_Median');
% Fzg 2
Par_Fzg_2 = load(['Emergenz\' Name_Emergenz_save '_' Mic_Pos_Name{2} '\Emergenz_Spinne.mat'],'Emergenz_Array_Max','id_langsam','id_stadt','id_land','id_bab','Emergenz_Array_Max_Abgl_Max','Emergenz_Array_Max_Abgl_Median');


%% Auswertung Max
Emergenz_Array_Max = max(Par_Fzg_1.Emergenz_Array_Max,Par_Fzg_2.Emergenz_Array_Max);
Emergenz_Array_Max_Abgl_Max = min(Par_Fzg_1.Emergenz_Array_Max_Abgl_Max,Par_Fzg_2.Emergenz_Array_Max_Abgl_Max);
Emergenz_Array_Max_Abgl_Median = min(Par_Fzg_1.Emergenz_Array_Max_Abgl_Median,Par_Fzg_2.Emergenz_Array_Max_Abgl_Median);
v = 10*unique([Par_Fzg_1.id_langsam, Par_Fzg_2.id_langsam, Par_Fzg_1.id_stadt, Par_Fzg_2.id_stadt, Par_Fzg_1.id_land, Par_Fzg_2.id_land,Par_Fzg_1.id_bab,Par_Fzg_2.id_bab]);
id_langsam = unique([Par_Fzg_1.id_langsam, Par_Fzg_2.id_langsam]);
id_stadt = unique([Par_Fzg_1.id_stadt, Par_Fzg_2.id_stadt]);
id_land = unique([Par_Fzg_1.id_land, Par_Fzg_2.id_land]);
id_bab = unique([Par_Fzg_1.id_bab, Par_Fzg_2.id_bab]);


%% Plot der maximalen Tonhaltigkeit im Vergleich mit den Emergenz-Zielkurven


%% Plot Emergenz-Spinne

openfig('Spinne_Vorlage_v6.fig');
hold on

% Grenzen Zielkurven
% Sport
h_max(1) = polar(0:2*pi/100:2*pi,4*ones(1,101),'--');
set(h_max(1),'LineWidth',2.5,'Color',[132 60 12]./255);
% Dynamik
h_max(2) = polar(0:2*pi/100:2*pi,5*ones(1,101),'--');
set(h_max(2),'LineWidth',2.5,'Color',[197 90 17]./255);
% Souverän
h_max(3) = polar(0:2*pi/100:2*pi,6*ones(1,101),'--');
set(h_max(3),'LineWidth',2.5,'Color',[237 125 49]./255);
% Luxus
h_max(4) = polar(0:2*pi/100:2*pi,7*ones(1,101),'--');
set(h_max(4),'LineWidth',2.5,'Color',[244 177 131]./255);
% Mithörschwelle
h_max(5) = polar(0:2*pi/100:2*pi,8*ones(1,101),'--');
set(h_max(5),'LineWidth',2.5,'Color','k');
% Ziel Fahrzeug-Charakter
h_max(6) = polar(0:2*pi/50:2*pi,(8-ziel_fahrzeug_charakter)*ones(1,51),'go');
set(h_max(6),'LineWidth',5);

legend_text_max = {'E-Antrieb "dominant"','E-Antrieb "präsent"','E-Antrieb "dezent"','E-Antrieb "leise"','E-Antrieb "unhörbar"','Fahrzeug Emergenz-Ziel'};

% Max Spinne

ct = 1;
plot_color = 'b';
id_names = {'langsam', 'stadt', 'land', 'bab'};
for i = 1:4
    if ~isempty(eval(sprintf('Par_Fzg_%d.id_%s', 1, id_names{i}))) || ~isempty(eval(sprintf('Par_Fzg_%d.id_%s', 2, id_names{i})))
        if plot_max == 1
            h_max(6+ct) = polar(eval(sprintf('%dpi/2-2pi/20:-2pi/20:%dpi/2+2pi/20', (i-1)*pi/2, (i-1)*pi/2)), eval(sprintf('Emergenz_Array_Max_Abgl_Max(%d,:)', i)), ':o');
            set(h_max(6+ct),'LineWidth',5,'Color',plot_color,'MarkerFaceColor',plot_color);
            legend_text_max{1,6+ct} = sprintf([Name_Messung_Plot_ZF '\n- Maximale Emergenz']);
            ct = ct+1;
        end
        if plot_median == 1
            h_max(6+ct) = polar(eval(sprintf('%dpi/2-2pi/20:-2pi/20:%dpi/2+2pi/20', (i-1)*pi/2, (i-1)*pi/2)), eval(sprintf('Emergenz_Array_Max_Abgl_Median(%d,:)', i)), '-s');
            set(h_max(6+ct),'LineWidth',6,'Color',plot_color,'MarkerFaceColor',plot_color);
            legend_text_max{1,6+ct} = sprintf([Name_Messung_Plot_ZF '\n- Mediane Emergenz']);
            ct = ct+1;
        end
    end
end
ct_max = ct;


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

h_legend_max = legend(h_max(1:6+plot_max+plot_median),legend_text_max);
h_legend_pos = get(h_legend_max,'Position');
set(h_legend_max,'FontSize',14,'Position',[0.75 0.45 h_legend_pos(3:4)]);

savefig(gcf,[save_path_ZF 'Emergenz_Spinne']);
set(gcf,'PaperPositionMode','auto');
print(gcf,[save_path_ZF 'Emergenz_Spinne'],'-dpng','-r0');

close all

save([save_path_ZF 'Emergenz_Zusammenfassung.mat']);

end