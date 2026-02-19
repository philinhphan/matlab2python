v_vector = Fzg__GesFzg_S;
zeit = Fzg__GesFzg_S_X;

% v_vector = v_kmh_S;
% zeit = v_kmh_S_X;
% 
% v_vector = V__Fzg_S;
% zeit = V__Fzg_S_X;

v_vector_kmh = 3.6*v_vector;

figure
plot(zeit,3.6*v_vector,'Color','r');

acc =diff(v_vector)./diff(zeit);
acc_smooth = smooth(acc,0.3,'rloess');

figure
plot(zeit(2:end),acc,'Color','r');
hold on
plot(zeit(2:end),acc_smooth);

figure
plot(v_vector_kmh(2:end),acc,'Color','r');
hold on
plot(v_vector_kmh(2:end),acc_smooth);
set(gca,'YLim',[-2 6]);

a_v(:,1) = v_vector_kmh;
a_v(2:end,2) = acc_smooth;
a_v = sortrows(a_v);

close all
clear all