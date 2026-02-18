% test_plotting.m
% Tests: figure, plot, xlabel, ylabel, title, grid, semilogx

x = linspace(0, 2*pi, 100);
y = sin(x);

% Basic line plot
figure;
plot(x, y);
xlabel('x (radians)');
ylabel('sin(x)');
title('Sine Wave');
grid on;

% Multiple lines with hold
figure;
hold on;
plot(x, sin(x), 'b-');
plot(x, cos(x), 'r--');
hold off;
xlabel('x');
ylabel('Amplitude');
title('Sin and Cos');
legend('sin(x)', 'cos(x)');
grid on;

% Semilog plot
f = logspace(1, 4, 50);   % 10 Hz to 10 kHz
H = 1 ./ (1 + (f/1000).^2);

figure;
semilogx(f, 20*log10(H));
xlabel('Frequency (Hz)');
ylabel('Level (dB)');
title('Low-pass Filter');
grid on;
xlim([10 10000]);

% Save figure
savefig('test_plot.fig');
