% test_basic.m
% Tests: variables, arithmetic, fprintf, disp

x = 42;
y = 3.14;
z = x + y;

name = 'World';
fprintf('Hello, %s!\n', name);
disp(z);

% Simple arithmetic
a = 10;
b = 3;
result_add = a + b;
result_sub = a - b;
result_mul = a * b;
result_div = a / b;
result_pow = a ^ 2;

fprintf('Add: %d\n', result_add);
fprintf('Sub: %d\n', result_sub);
fprintf('Mul: %d\n', result_mul);
fprintf('Div: %.4f\n', result_div);
fprintf('Pow: %d\n', result_pow);

% Array creation
v = [1 2 3 4 5];
fprintf('Sum: %d\n', sum(v));
fprintf('Mean: %.2f\n', mean(v));
fprintf('Length: %d\n', length(v));

% String operations
prefix = 'Result';
num = 7;
label = [prefix '_' num2str(num)];
disp(label);
