"""Knowledge tools: tool_plain functions that return conversion rules and mappings.

These do not need RunContext since they only look up static data.
"""

from __future__ import annotations

from converter.stdlib_map import MATLAB_TO_PYTHON_MAP

# Detailed conversion recipes for named patterns
CONVERSION_RULES: dict[str, str] = {
    "dynamic_struct_access": """
MATLAB dynamic struct field access:
  s.(varname)              → s[varname]
  s.([prefix num2str(n)]) → s[f"{prefix}{n}"]
  s.(['field' num2str(i)]) → s[f"field{i}"]

When a struct becomes a dict in Python, use dict[key] syntax.
Example:
  MATLAB: Ergebnis.(FeldName) = wert
  Python: Ergebnis[FeldName] = wert

  MATLAB: data.(['Z' num2str(kk)])
  Python: data[f'Z{kk}']
""",

    "mat_file_load": """
Loading .mat files:
  MATLAB: data = load('file.mat')
  Python:
    import scipy.io
    raw = scipy.io.loadmat('file.mat')
    data = mat_to_dict(raw)

  MATLAB: load('file.mat', 'var1', 'var2')
  Python:
    raw = scipy.io.loadmat('file.mat', variable_names=['var1', 'var2'])
    data = mat_to_dict(raw)

Always include mat_to_dict() helper at top of file:
  def mat_to_dict(mat):
      return {k: v.squeeze().item() if v.squeeze().ndim==0 else v.squeeze()
              for k, v in mat.items() if not k.startswith('__')}

After loading: MATLAB data.fieldname → Python data['fieldname']
""",

    "mat_file_save": """
Saving .mat files:
  MATLAB: save('file.mat', 'var1', 'var2')
  Python: scipy.io.savemat('file.mat', {'var1': var1, 'var2': var2})

  MATLAB: save('file.mat')  (saves workspace)
  Python: scipy.io.savemat('file.mat', {
      'var1': var1, 'var2': var2,  # list all in-scope variables explicitly
  })

  CRITICAL: When MATLAB uses save('file.mat') with NO variable list,
  it saves ALL workspace variables. You must trace what downstream
  functions load from this file and include ALL those variables.
  When in doubt, save every locally-computed variable.

For nested structs:
  MATLAB: save with nested struct field
  Python: scipy.io.savemat('file.mat', {'struct_name': {'field': value}})
""",

    "1based_indexing": """
MATLAB uses 1-based indexing, Python uses 0-based. Subtract 1 from EVERY index.

Simple cases:
  MATLAB: A(1)    → Python: A[0]
  MATLAB: A(i)    → Python: A[i-1]
  MATLAB: A(end)  → Python: A[-1]
  MATLAB: A(end-1) → Python: A[-2]

Range slicing:
  MATLAB: A(1:5)   → Python: A[0:5]   (same as A[:5])
  MATLAB: A(2:end) → Python: A[1:]
  MATLAB: A(i:j)   → Python: A[i-1:j]  (j is inclusive in MATLAB, exclusive in Python — but slice end is already exclusive so A[i-1:j] is correct)
  MATLAB: A(i:end) → Python: A[i-1:]

Loop variables:
  MATLAB: for i=1:N → Python: for i in range(1, N+1)
  Inside loop: A(i) → A[i-1]

2D arrays:
  MATLAB: M(i,j)     → Python: M[i-1, j-1]
  MATLAB: M(:,j)     → Python: M[:, j-1]
  MATLAB: M(i,:)     → Python: M[i-1, :]
  MATLAB: M(1:m,1:n) → Python: M[0:m, 0:n]  (same as M[:m,:n])
""",

    "arithmetic_column_index": """
CRITICAL: Arithmetic column index pattern — most error-prone conversion.

When a loop variable is used in arithmetic to compute an index:
  MATLAB: for kk=1:N; A(:, 2*kk)     → Python: for kk in range(1, N+1): A[:, 2*kk-1]
  MATLAB: for kk=1:N; A(:, 2*kk-1)   → Python: for kk in range(1, N+1): A[:, 2*kk-2]
  MATLAB: for kk=1:N; A(:, 2*kk-1:2*kk) → Python: A[:, 2*kk-2:2*kk]  (slice end not adjusted!)
  MATLAB: for kk=1:N; A(3*kk-2:3*kk,:) → Python: A[3*kk-3:3*kk, :]

The rule: subtract 1 from the FINAL computed start index.
For slices A(start:end), Python needs A[start-1:end] — only start is adjusted!

Examples with ZArrayV pattern from acoustic analysis:
  MATLAB: ZArrayV(:, 2*kk)    (kk=1→col2, kk=2→col4)
  Python:  ZArrayV[:, 2*kk-1] (kk=1→col1=idx1, kk=2→col3=idx3 ✓)

  MATLAB: ZArrayV(:, 2*kk-1)  (kk=1→col1, kk=2→col3)
  Python:  ZArrayV[:, 2*kk-2] (kk=1→col0=idx0, kk=2→col2=idx2 ✓)

  MATLAB: ZArrayV(:, 2*kk-1:2*kk) (kk=1→cols1:2)
  Python:  ZArrayV[:, 2*kk-2:2*kk] (kk=1→0:2 which is [idx0,idx1] ✓)
""",

    "waitbar": """
MATLAB waitbar → Python tqdm:
  MATLAB:
    h = waitbar(0, 'Processing...');
    for i=1:N
        waitbar(i/N, h);
        % work
    end
    close(h);

  Python:
    from tqdm import tqdm
    pbar = tqdm(total=N, desc='Processing...')
    for i in range(N):
        # work
        pbar.update(1)
    pbar.close()

Or use tqdm as context manager:
    with tqdm(total=N, desc='Processing...') as pbar:
        for i in range(N):
            # work
            pbar.update(1)
""",

    "uigetfile": """
MATLAB uigetfile → Python glob-based auto-selection:
  MATLAB:
    [filename, pathname] = uigetfile('*.mat', 'Select file');
    full_path = fullfile(pathname, filename);

  Python:
    import glob
    import os
    # CONVERSION NOTE: uigetfile replaced with glob-based auto-selection.
    # For interactive GUI, use: tkinter.filedialog.askopenfilename()
    mat_files = sorted(glob.glob('*.mat'))
    if not mat_files:
        raise FileNotFoundError('No .mat files found in current directory')
    full_path = mat_files[0]  # auto-select first match
    pathname, filename = os.path.split(full_path)

  When the MATLAB code filters by a specific pattern (e.g. '*MHS*.mat'),
  use that pattern in the glob call. When context provides a search
  directory (e.g. from a variable), use os.path.join(search_dir, pattern).

  When uigetfile browses a directory (data in subdirectories),
  use recursive glob:
    mat_files = sorted(glob.glob(os.path.join(dir, '**', '*.mat'), recursive=True))
    # Filter by context (e.g., mic position name) if available

  NEVER use input() — it causes EOFError in non-interactive execution.
""",

    "assignin": """
MATLAB assignin → remove with comment:
  MATLAB:
    assignin('base', 'varname', value)
    assignin('caller', 'result', computed)

  Python:
    # CONVERSION NOTE: assignin('base'/'caller', 'varname', value) removed.
    # Restructure: return value from function or use a shared dict/object.
    # varname = value  (if in same scope)

The pattern often appears when trying to set variables in the calling workspace.
Restructure to use return values or pass mutable containers.
""",

    "openfig": """
MATLAB openfig → recreate figure programmatically:
  MATLAB:
    hFig = openfig('template.fig');
    ax = gca;
    % modify plot...

  Python:
    import matplotlib.pyplot as plt
    # CONVERSION NOTE: openfig('template.fig') cannot load MATLAB .fig files.
    # Recreate the figure programmatically from the MATLAB code context.
    fig, ax = plt.subplots(subplot_kw={'projection': 'polar'})  # if polar/spider
    # or: fig, ax = plt.subplots()  # for regular axes

  For spider/radar diagrams (common with openfig):
    fig, ax = plt.subplots(subplot_kw={'projection': 'polar'})
    ax.set_theta_zero_location('N')    # 0° at top
    ax.set_theta_direction(-1)          # clockwise
    angles = np.linspace(0, 2*np.pi, n_categories, endpoint=False)
    ax.plot(angles, values)
    ax.set_thetagrids(np.degrees(angles), category_labels)

  MUST recreate the figure — do NOT just add a comment and skip it.
""",

    "addpath": """
MATLAB addpath → remove with comment, use explicit imports:
  MATLAB:
    addpath('subfolder')
    addpath(genpath('libs'))

  Python:
    # CONVERSION NOTE: addpath('subfolder') removed.
    # Python uses explicit imports: from module import function
    # All output files are flat in the output directory and on PYTHONPATH.

  Since all converted .py files land in the same flat output directory,
  cross-file function calls should use:
    from other_module import function_name

  Do NOT add sys.path manipulation — the execution environment already
  sets PYTHONPATH to include the output directory.
""",

    "eval_sprintf": """
MATLAB eval(sprintf()) → Python dict dispatch or getattr():
  MATLAB:
    eval(sprintf('ZArray%d = data;', kk))
    eval(['result = ' varname '+ 1;'])

  Python option 1 (dict dispatch — preferred):
    arrays = {}
    arrays[f'ZArray{kk}'] = data

  Python option 2 (getattr for object attributes):
    setattr(obj, f'field{kk}', value)
    getattr(obj, f'field{kk}')

  NEVER use Python eval() — it's a security risk and fragile.
  NEVER use exec() either.

  For reading dynamically named variables:
    MATLAB: val = eval(sprintf('array_%d', i))
    Python:  val = arrays[f'array_{i}']
""",

    "polar_plot": """
MATLAB polar() → matplotlib polar projection:
  MATLAB:
    polar(theta, r)
    polar(theta, r, 'r-')

  Python:
    fig, ax = plt.subplots(subplot_kw={'projection': 'polar'})
    ax.plot(theta, r)        # theta in radians
    ax.plot(theta, r, 'r-')

  For rose/compass plots:
    ax = fig.add_subplot(projection='polar')

  Note: MATLAB polar() uses degrees for some variants; ensure theta is in radians.
  Convert: theta_rad = np.deg2rad(theta_deg)

  Setting axis limits:
    MATLAB: axis([0 2*pi 0 rmax])
    Python:  ax.set_rlim(0, rmax)

  Tick labels:
    ax.set_thetagrids(np.degrees(theta_ticks))
""",

    "subtightplot": """
MATLAB subtightplot → matplotlib GridSpec:
  MATLAB:
    subtightplot(n_rows, n_cols, idx, gap, marg_h, marg_w)
    where gap=[hspace wspace], marg_h=[top bot], marg_w=[left right]

  Python (include this helper function in the converted file):
    def subtightplot(n_rows, n_cols, idx, gap=(0.1,0.05), marg_h=(0.1,0.06), marg_w=(0.05,0.05)):
        import matplotlib.gridspec as gridspec
        gs = gridspec.GridSpec(n_rows, n_cols,
                               hspace=gap[0], wspace=gap[1],
                               top=1-marg_h[0], bottom=marg_h[1],
                               left=marg_w[0], right=1-marg_w[1])
        return plt.subplot(gs[idx-1])  # MATLAB idx is 1-based

  Usage:
    ax = subtightplot(2, 3, 1, [0.1, 0.05], [0.1, 0.06], [0.05, 0.05])
""",

    "cell_array": """
MATLAB cell arrays → Python lists:
  MATLAB: c = cell(1, n)   → Python: c = [None] * n
  MATLAB: c = cell(m, n)   → Python: c = [[None]*n for _ in range(m)]
  MATLAB: c{i}             → Python: c[i-1]    (0-based!)
  MATLAB: c{i,j}           → Python: c[i-1][j-1]
  MATLAB: c{end}           → Python: c[-1]
  MATLAB: [c{:}]           → Python: c  (already a list)

  Cell of strings:
  MATLAB: labels = {'apples', 'bananas', 'cherries'}
  Python:  labels = ['apples', 'bananas', 'cherries']

  Appending:
  MATLAB: c{end+1} = val   → Python: c.append(val)

  For-loop over cells:
  MATLAB: for i=1:length(c); do_something(c{i}); end
  Python:  for item in c: do_something(item)
""",

    "string_concat": """
MATLAB string concatenation → Python f-strings:
  MATLAB: ['hello ' name]       → Python: f'hello {name}'
  MATLAB: [str1 str2 str3]      → Python: f'{str1}{str2}{str3}'
  MATLAB: [prefix num2str(n)]   → Python: f'{prefix}{n}'
  MATLAB: sprintf('%s_%d', s, n) → Python: f'{s}_{n}'
  MATLAB: [path '\' filename]   → Python: os.path.join(path, filename)
                                          or f'{path}/{filename}'

  For building paths use pathlib:
    from pathlib import Path
    full_path = Path(path) / subdir / filename
""",

    "pyenv_pyrunfile": """
MATLAB pyenv/pyrunfile → remove with note:
  MATLAB:
    pyenv('Version', '/path/to/python')
    pyrunfile('script.py', var=value)
    result = py.module.function(args)

  Python:
    # CONVERSION NOTE: pyenv removed — Python script runs natively.
    # CONVERSION NOTE: pyrunfile('script.py') removed.
    # Convert 'script.py' as a separate Python module and import it:
    #   import script  (or from script import function)

  Python objects called via py.module.fn:
    # CONVERSION NOTE: py.numpy.array([1,2,3]) → np.array([1,2,3])
    # Import the Python module directly.
""",

    "windows_path": """
Windows path handling → pathlib:
  MATLAB: path = 'C:\\Users\\data\\file.mat'
  Python:  path = r'C:\\Users\\data\\file.mat'  # raw string
        or path = 'C:/Users/data/file.mat'       # forward slashes
        or path = Path('C:/Users/data/file.mat') # pathlib

  Building paths:
  MATLAB: fullfile(root, 'subdir', 'file.mat')
  Python:  Path(root) / 'subdir' / 'file.mat'
        or os.path.join(root, 'subdir', 'file.mat')

  Directory separator:
  MATLAB: [root '\\' subdir '\\' file]
  Python:  os.path.join(root, subdir, file)
        or f'{root}/{subdir}/{file}'

  Always use forward slashes or pathlib.Path — never hardcode backslashes.
""",

    "grouped_bar": """
MATLAB grouped bar chart → matplotlib:
  MATLAB:
    bar(x, Y)  % Y is matrix, each column is a group

  Python:
    import numpy as np
    import matplotlib.pyplot as plt

    n_groups, n_bars = Y.shape  # or len(x), Y.shape[1]
    x_pos = np.arange(n_groups)
    width = 0.8 / n_bars
    fig, ax = plt.subplots()
    for i in range(n_bars):
        ax.bar(x_pos + i * width - (n_bars-1)*width/2,
               Y[:, i], width=width, label=labels[i])
    ax.set_xticks(x_pos)
    ax.set_xticklabels(x_labels)
    ax.legend()
""",

    "logical_indexing": """
MATLAB logical indexing → NumPy boolean indexing:
  MATLAB: A(A > 0)         → Python: A[A > 0]
  MATLAB: A(mask)           → Python: A[mask]
  MATLAB: A(logical(B))     → Python: A[B.astype(bool)]
  MATLAB: A(B == 'string')  → Python: A[B == 'string']

  Assignment with logical index:
  MATLAB: A(A < 0) = 0     → Python: A[A < 0] = 0
  MATLAB: A(idx) = val      → Python: A[idx] = val  (idx is 0-based!)

  find() with logical:
  MATLAB: find(A > threshold) → Python: np.where(A > threshold)[0]
  Returns 0-based indices in Python!
""",

    "colon_operator": """
MATLAB colon operator → NumPy arange:
  MATLAB: a:b        → Python: np.arange(a, b+1)   (integer, inclusive end)
  MATLAB: a:s:b      → Python: np.arange(a, b+s, s) (with step)
  MATLAB: 1:N        → Python: range(1, N+1) in for-loops
                              or np.arange(1, N+1) for arrays

  For loop:
  MATLAB: for i=1:10       → Python: for i in range(1, 11):
  MATLAB: for i=0:0.1:1   → Python: for i in np.arange(0, 1.1, 0.1):
  MATLAB: for i=N:-1:1    → Python: for i in range(N, 0, -1):

  As array:
  MATLAB: x = (0:0.01:1)'  → Python: x = np.arange(0, 1.01, 0.01).reshape(-1,1)
  MATLAB: x = 1:10         → Python: x = np.arange(1, 11)
""",
}

# Plotting recipes keyed by MATLAB command
PLOTTING_RECIPES: dict[str, str] = {
    "polar": """
ax = fig.add_subplot(projection='polar')
# or: fig, ax = plt.subplots(subplot_kw={'projection': 'polar'})
ax.plot(theta_rad, r)
ax.set_rlim(0, rmax)
ax.set_thetagrids(np.arange(0, 360, 45))
""",
    "semilogx": "ax.semilogx(x, y, **kwargs)",
    "semilogy": "ax.semilogy(x, y, **kwargs)",
    "loglog": "ax.loglog(x, y, **kwargs)",
    "bar_grouped": """
# Grouped bar chart
import numpy as np
n_groups = len(categories)
n_series = Y.shape[1]
x = np.arange(n_groups)
width = 0.8 / n_series
for i, (col, label) in enumerate(zip(Y.T, series_labels)):
    offset = (i - n_series/2 + 0.5) * width
    ax.bar(x + offset, col, width=width, label=label)
ax.set_xticks(x)
ax.set_xticklabels(categories)
ax.legend()
""",
    "subplot": """
fig, axes = plt.subplots(nrows, ncols, figsize=(width, height))
ax = axes[row, col]  # 0-based
# or with subtightplot for precise control
""",
    "colormap_jet": """
cmap = plt.colormaps['jet']
im = ax.pcolormesh(X, Y, Z, cmap='jet')
fig.colorbar(im, ax=ax)
""",
    "errorbar": "ax.errorbar(x, y, yerr=errors, fmt='o-', capsize=5)",
    "contourf": """
cs = ax.contourf(X, Y, Z, levels=20, cmap='jet')
ax.clabel(cs, inline=True, fontsize=8)
fig.colorbar(cs, ax=ax)
""",
    "stem": "ax.stem(x, y)",
    "stairs": "ax.stairs(values, edges)",
    "fill_between": "ax.fill_between(x, y1, y2, alpha=0.3)",
    "quiver": "ax.quiver(X, Y, U, V)",
    "pcolor": "ax.pcolormesh(X, Y, Z, cmap='jet')",
    "imagesc": """
im = ax.imshow(Z, origin='lower', aspect='auto',
               extent=[x.min(), x.max(), y.min(), y.max()])
fig.colorbar(im, ax=ax)
""",
    "spy": "ax.spy(A)",
    "histogram": "ax.hist(data, bins=30, edgecolor='black')",
    "set_line_properties": """
line, = ax.plot(x, y)
line.set_linewidth(2)
line.set_color('red')
line.set_linestyle('--')
line.set_marker('o')
line.set_markersize(5)
""",
    "twin_axis": """
ax2 = ax.twinx()
ax2.set_ylabel('second axis')
ax2.plot(x, y2, color='red')
""",
    "tight_layout": "fig.tight_layout(pad=1.5)",
    "savefig": "fig.savefig('output.pdf', dpi=300, bbox_inches='tight')",
}


def get_matlab_stdlib_mapping(function_name: str) -> str:
    """Look up a MATLAB function in the conversion map.

    Returns a formatted string with the Python equivalent, required imports,
    and usage notes. Returns a not-found message if the function is unknown.
    """
    entry = MATLAB_TO_PYTHON_MAP.get(function_name)
    if entry is None:
        return (
            f"Function '{function_name}' not found in stdlib map. "
            "Check numpy, scipy, or matplotlib docs for equivalent. "
            "Common pattern: many MATLAB functions map to numpy with same name."
        )
    lines = [
        f"MATLAB: {function_name}()",
        f"Python: {entry['python']}",
        f"Imports: {', '.join(entry['imports']) if entry['imports'] else 'none'}",
        f"Notes: {entry['notes']}",
    ]
    return "\n".join(lines)


def get_conversion_rule(pattern_name: str) -> str:
    """Return a detailed conversion recipe for a named MATLAB pattern.

    Available patterns: dynamic_struct_access, mat_file_load, mat_file_save,
    1based_indexing, arithmetic_column_index, waitbar, uigetfile, openfig,
    addpath, assignin, eval_sprintf, polar_plot, subtightplot, cell_array,
    string_concat, pyenv_pyrunfile, windows_path, grouped_bar,
    logical_indexing, colon_operator.
    """
    rule = CONVERSION_RULES.get(pattern_name)
    if rule is None:
        available = ", ".join(sorted(CONVERSION_RULES.keys()))
        return (
            f"Pattern '{pattern_name}' not found. "
            f"Available patterns: {available}"
        )
    return rule.strip()


def get_plotting_recipe(matlab_command: str) -> str:
    """Return the matplotlib equivalent for a MATLAB plotting command.

    Available: polar, semilogx, semilogy, loglog, bar_grouped, subplot,
    colormap_jet, errorbar, contourf, stem, stairs, fill_between, quiver,
    pcolor, imagesc, spy, histogram, set_line_properties, twin_axis,
    tight_layout, savefig.
    """
    recipe = PLOTTING_RECIPES.get(matlab_command)
    if recipe is None:
        # Fall back to stdlib map for basic plot commands
        mapping_result = get_matlab_stdlib_mapping(matlab_command)
        if "not found" not in mapping_result:
            return mapping_result
        available = ", ".join(sorted(PLOTTING_RECIPES.keys()))
        return (
            f"No recipe for '{matlab_command}'. "
            f"Available recipes: {available}. "
            "Check matplotlib docs: https://matplotlib.org/stable/gallery/"
        )
    return recipe.strip()
