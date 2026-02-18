% test_indexing.m
% Tests: 1-based loops, array indexing, arithmetic column index (2*kk-1)

N = 4;
A = zeros(N, 1);

% Basic 1-based loop with array indexing
for i = 1:N
    A(i) = i * 2;
end
disp(A);

% Matrix with arithmetic column indexing (key pattern)
M = zeros(3, 2*N);
for kk = 1:N
    % MATLAB: column 2*kk-1 and 2*kk (1-based)
    M(:, 2*kk-1) = kk;
    M(:, 2*kk)   = kk * 10;
end
disp(M);

% Slicing
B = [10 20 30 40 50];
first = B(1);
last  = B(end);
sub   = B(2:4);
fprintf('First: %d, Last: %d\n', first, last);
disp(sub);

% Reverse loop
C = zeros(1, N);
for i = N:-1:1
    C(i) = N - i + 1;
end
disp(C);

% 2D indexing
D = magic(4);
val = D(2, 3);
col = D(:, 2);
row = D(1, :);
fprintf('D(2,3) = %d\n', val);
disp(col);
disp(row);
