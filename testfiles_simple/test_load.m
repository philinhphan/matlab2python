% test_load.m
% Tests: load() -> mat_to_dict + scipy.io.loadmat, struct field access after load

% Simulate what load() does: load a .mat file
% (In real usage this would be: data = load('measurements.mat'))
% For testing we create a struct manually to mirror the pattern
data.frequency  = [100 200 500 1000 2000];
data.level_dB   = [60 65 70 72 68];
data.label      = 'test_measurement';

% Field access pattern identical to after load()
fprintf('Label: %s\n', data.label);
fprintf('Num frequencies: %d\n', length(data.frequency));

% Dynamic field access after load (common pattern)
fields = {'frequency', 'level_dB'};
for i = 1:length(fields)
    fname = fields{i};
    val = data.(fname);
    fprintf('%s: ', fname);
    disp(val);
end

% save/load round-trip pattern
save('temp_test.mat', 'data');
loaded = load('temp_test.mat');
fprintf('Loaded label: %s\n', loaded.data.label);

% Access nested field
freq = loaded.data.frequency;
level = loaded.data.level_dB;
fprintf('Peak level: %.1f dB at %d Hz\n', max(level), freq(find(level == max(level))));
