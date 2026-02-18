% test_structs.m
% Tests: static struct fields, dynamic struct access s.(fieldname)

% Static struct
data.frequency = 1000;
data.amplitude = 0.5;
data.label     = 'tone';

fprintf('Frequency: %d Hz\n', data.frequency);
fprintf('Amplitude: %.2f\n', data.amplitude);
fprintf('Label: %s\n', data.label);

% Struct array via struct()
s = struct('name', 'foo', 'value', 42);
disp(s.name);
disp(s.value);

% Dynamic field access
fields = {'frequency', 'amplitude', 'label'};
for i = 1:length(fields)
    fname = fields{i};
    val = data.(fname);
    fprintf('%s -> ', fname);
    disp(val);
end

% Dynamic field name from num2str
result = struct();
for kk = 1:3
    fieldname = ['Z' num2str(kk)];
    result.(fieldname) = kk * 100;
end

% Read back dynamically
for kk = 1:3
    fname = ['Z' num2str(kk)];
    fprintf('%s = %d\n', fname, result.(fname));
end

% fieldnames
fn = fieldnames(data);
fprintf('Fields in data: %d\n', length(fn));
