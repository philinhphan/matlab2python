"""MATLAB → Python/NumPy/SciPy function mapping.

Each entry maps a MATLAB function name to a dict with:
  - python: the Python equivalent expression or pattern
  - imports: list of import statements needed
  - notes: any caveats or usage notes
"""

MATLAB_TO_PYTHON_MAP: dict[str, dict] = {
    # Array creation
    "zeros": {
        "python": "np.zeros((m, n))",
        "imports": ["import numpy as np"],
        "notes": "zeros(m,n) → np.zeros((m,n)); zeros(1,n) → np.zeros(n)",
    },
    "ones": {
        "python": "np.ones((m, n))",
        "imports": ["import numpy as np"],
        "notes": "ones(m,n) → np.ones((m,n))",
    },
    "nan": {
        "python": "np.nan",
        "imports": ["import numpy as np"],
        "notes": "NaN scalar; for arrays: np.full((m,n), np.nan)",
    },
    "NaN": {
        "python": "np.nan",
        "imports": ["import numpy as np"],
        "notes": "NaN scalar; for arrays: np.full((m,n), np.nan)",
    },
    "linspace": {
        "python": "np.linspace(a, b, n)",
        "imports": ["import numpy as np"],
        "notes": "Same signature as MATLAB",
    },
    "logspace": {
        "python": "np.logspace(a, b, n)",
        "imports": ["import numpy as np"],
        "notes": "Same signature; exponents base 10 by default",
    },
    "eye": {
        "python": "np.eye(n)",
        "imports": ["import numpy as np"],
        "notes": "Identity matrix",
    },
    "rand": {
        "python": "np.random.rand(m, n)",
        "imports": ["import numpy as np"],
        "notes": "Uniform random; randn → np.random.randn",
    },
    "randn": {
        "python": "np.random.randn(m, n)",
        "imports": ["import numpy as np"],
        "notes": "Normal random",
    },

    # Array info
    "size": {
        "python": "A.shape",
        "imports": ["import numpy as np"],
        "notes": "size(A) → A.shape; size(A,1) → A.shape[0]; size(A,2) → A.shape[1]",
    },
    "length": {
        "python": "max(A.shape)",
        "imports": ["import numpy as np"],
        "notes": "length(A) → max(A.shape) or len(A) for 1D",
    },
    "numel": {
        "python": "A.size",
        "imports": ["import numpy as np"],
        "notes": "Total number of elements",
    },
    "ndims": {
        "python": "A.ndim",
        "imports": ["import numpy as np"],
        "notes": "Number of dimensions",
    },
    "isempty": {
        "python": "A.size == 0",
        "imports": ["import numpy as np"],
        "notes": "isempty(A) → A.size == 0 or (isinstance(A, list) and len(A) == 0)",
    },

    # Array operations
    "find": {
        "python": "np.where(condition)[0]",
        "imports": ["import numpy as np"],
        "notes": "find(cond) → np.where(cond)[0]; returns 0-based indices",
    },
    "sort": {
        "python": "np.sort(A)",
        "imports": ["import numpy as np"],
        "notes": "sort(A) ascending; sort(A,'descend') → np.sort(A)[::-1]",
    },
    "sum": {
        "python": "np.sum(A)",
        "imports": ["import numpy as np"],
        "notes": "sum(A) → np.sum(A); sum(A,1) → np.sum(A,axis=0); sum(A,2) → np.sum(A,axis=1)",
    },
    "cumsum": {
        "python": "np.cumsum(A)",
        "imports": ["import numpy as np"],
        "notes": "cumsum(A) → np.cumsum(A)",
    },
    "prod": {
        "python": "np.prod(A)",
        "imports": ["import numpy as np"],
        "notes": "prod(A) → np.prod(A)",
    },
    "max": {
        "python": "np.max(A)",
        "imports": ["import numpy as np"],
        "notes": "max(A) → np.max(A); [v,i]=max(A) → i=np.argmax(A); v=A[i]",
    },
    "min": {
        "python": "np.min(A)",
        "imports": ["import numpy as np"],
        "notes": "min(A) → np.min(A); [v,i]=min(A) → i=np.argmin(A); v=A[i]",
    },
    "mean": {
        "python": "np.mean(A)",
        "imports": ["import numpy as np"],
        "notes": "mean(A) → np.mean(A); mean(A,2) → np.mean(A,axis=1)",
    },
    "std": {
        "python": "np.std(A, ddof=1)",
        "imports": ["import numpy as np"],
        "notes": "MATLAB uses ddof=1 (N-1) by default; numpy default is ddof=0",
    },
    "abs": {
        "python": "np.abs(A)",
        "imports": ["import numpy as np"],
        "notes": "abs(A) → np.abs(A)",
    },
    "floor": {
        "python": "np.floor(A)",
        "imports": ["import numpy as np"],
        "notes": "floor(A) → np.floor(A)",
    },
    "ceil": {
        "python": "np.ceil(A)",
        "imports": ["import numpy as np"],
        "notes": "ceil(A) → np.ceil(A)",
    },
    "round": {
        "python": "np.round(A)",
        "imports": ["import numpy as np"],
        "notes": "round(A) → np.round(A)",
    },
    "mod": {
        "python": "A % B",
        "imports": [],
        "notes": "mod(a,b) → a % b",
    },
    "rem": {
        "python": "A % B",
        "imports": [],
        "notes": "rem(a,b) → a % b (same for positive numbers)",
    },
    "fix": {
        "python": "int(A)",
        "imports": ["import numpy as np"],
        "notes": "fix(A) → np.fix(A) or int(A) for scalars; truncates toward zero",
    },
    "sign": {
        "python": "np.sign(A)",
        "imports": ["import numpy as np"],
        "notes": "sign(A) → np.sign(A)",
    },
    "cross": {
        "python": "np.cross(A, B)",
        "imports": ["import numpy as np"],
        "notes": "cross(A,B) → np.cross(A,B)",
    },
    "dot": {
        "python": "np.dot(A, B)",
        "imports": ["import numpy as np"],
        "notes": "dot(A,B) → np.dot(A,B)",
    },
    "norm": {
        "python": "np.linalg.norm(A)",
        "imports": ["import numpy as np"],
        "notes": "norm(A) → np.linalg.norm(A); norm(A,1) → np.linalg.norm(A,1)",
    },
    "inv": {
        "python": "np.linalg.inv(A)",
        "imports": ["import numpy as np"],
        "notes": "inv(A) → np.linalg.inv(A)",
    },
    "det": {
        "python": "np.linalg.det(A)",
        "imports": ["import numpy as np"],
        "notes": "det(A) → np.linalg.det(A)",
    },
    "eig": {
        "python": "np.linalg.eig(A)",
        "imports": ["import numpy as np"],
        "notes": "[V,D]=eig(A) → eigenvalues,eigenvectors=np.linalg.eig(A)",
    },
    "reshape": {
        "python": "A.reshape(m, n)",
        "imports": ["import numpy as np"],
        "notes": "reshape(A,m,n) → A.reshape(m,n); use -1 for auto dimension",
    },
    "repmat": {
        "python": "np.tile(A, (m, n))",
        "imports": ["import numpy as np"],
        "notes": "repmat(A,m,n) → np.tile(A,(m,n))",
    },
    "transpose": {
        "python": "A.T",
        "imports": [],
        "notes": "A' or transpose(A) → A.T",
    },
    "fliplr": {
        "python": "np.fliplr(A)",
        "imports": ["import numpy as np"],
        "notes": "fliplr(A) → np.fliplr(A)",
    },
    "flipud": {
        "python": "np.flipud(A)",
        "imports": ["import numpy as np"],
        "notes": "flipud(A) → np.flipud(A)",
    },
    "horzcat": {
        "python": "np.hstack([A, B])",
        "imports": ["import numpy as np"],
        "notes": "[A B] → np.hstack([A,B])",
    },
    "vertcat": {
        "python": "np.vstack([A, B])",
        "imports": ["import numpy as np"],
        "notes": "[A; B] → np.vstack([A,B])",
    },
    "cat": {
        "python": "np.concatenate([A, B], axis=dim-1)",
        "imports": ["import numpy as np"],
        "notes": "cat(dim,A,B) → np.concatenate([A,B],axis=dim-1)",
    },
    "diag": {
        "python": "np.diag(A)",
        "imports": ["import numpy as np"],
        "notes": "diag(A) → np.diag(A)",
    },
    "triu": {
        "python": "np.triu(A)",
        "imports": ["import numpy as np"],
        "notes": "triu(A) → np.triu(A)",
    },
    "tril": {
        "python": "np.tril(A)",
        "imports": ["import numpy as np"],
        "notes": "tril(A) → np.tril(A)",
    },
    "kron": {
        "python": "np.kron(A, B)",
        "imports": ["import numpy as np"],
        "notes": "kron(A,B) → np.kron(A,B)",
    },

    # Math functions
    "sqrt": {
        "python": "np.sqrt(A)",
        "imports": ["import numpy as np"],
        "notes": "sqrt(A) → np.sqrt(A)",
    },
    "exp": {
        "python": "np.exp(A)",
        "imports": ["import numpy as np"],
        "notes": "exp(A) → np.exp(A)",
    },
    "log": {
        "python": "np.log(A)",
        "imports": ["import numpy as np"],
        "notes": "log(A) → np.log(A) (natural log!); log10 → np.log10; log2 → np.log2",
    },
    "log10": {
        "python": "np.log10(A)",
        "imports": ["import numpy as np"],
        "notes": "log10(A) → np.log10(A)",
    },
    "log2": {
        "python": "np.log2(A)",
        "imports": ["import numpy as np"],
        "notes": "log2(A) → np.log2(A)",
    },
    "sin": {
        "python": "np.sin(A)",
        "imports": ["import numpy as np"],
        "notes": "sin(A) → np.sin(A); argument in radians",
    },
    "cos": {
        "python": "np.cos(A)",
        "imports": ["import numpy as np"],
        "notes": "cos(A) → np.cos(A)",
    },
    "tan": {
        "python": "np.tan(A)",
        "imports": ["import numpy as np"],
        "notes": "tan(A) → np.tan(A)",
    },
    "atan2": {
        "python": "np.arctan2(y, x)",
        "imports": ["import numpy as np"],
        "notes": "atan2(y,x) → np.arctan2(y,x)",
    },
    "pi": {
        "python": "np.pi",
        "imports": ["import numpy as np"],
        "notes": "pi → np.pi",
    },

    # String operations
    "sprintf": {
        "python": "f'...'",
        "imports": [],
        "notes": "sprintf('%d items', n) → f'{n} items'; use f-strings",
    },
    "num2str": {
        "python": "str(x)",
        "imports": [],
        "notes": "num2str(x) → str(x); num2str(x,'%.2f') → f'{x:.2f}'",
    },
    "str2num": {
        "python": "float(s)",
        "imports": [],
        "notes": "str2num(s) → float(s) or int(s)",
    },
    "str2double": {
        "python": "float(s)",
        "imports": [],
        "notes": "str2double(s) → float(s)",
    },
    "strcmp": {
        "python": "a == b",
        "imports": [],
        "notes": "strcmp(a,b) → a == b",
    },
    "strcmpi": {
        "python": "a.lower() == b.lower()",
        "imports": [],
        "notes": "strcmpi(a,b) → a.lower() == b.lower()",
    },
    "strcat": {
        "python": "a + b",
        "imports": [],
        "notes": "strcat(a,b) → a + b or f'{a}{b}'",
    },
    "strtrim": {
        "python": "s.strip()",
        "imports": [],
        "notes": "strtrim(s) → s.strip()",
    },
    "lower": {
        "python": "s.lower()",
        "imports": [],
        "notes": "lower(s) → s.lower()",
    },
    "upper": {
        "python": "s.upper()",
        "imports": [],
        "notes": "upper(s) → s.upper()",
    },
    "strsplit": {
        "python": "s.split(delim)",
        "imports": [],
        "notes": "strsplit(s,delim) → s.split(delim)",
    },
    "strrep": {
        "python": "s.replace(old, new)",
        "imports": [],
        "notes": "strrep(s,old,new) → s.replace(old,new)",
    },
    "regexp": {
        "python": "re.search(pattern, s)",
        "imports": ["import re"],
        "notes": "regexp(s,pattern) → re.search(pattern,s)",
    },
    "regexprep": {
        "python": "re.sub(pattern, replacement, s)",
        "imports": ["import re"],
        "notes": "regexprep(s,pattern,rep) → re.sub(pattern,rep,s)",
    },
    "int2str": {
        "python": "str(int(x))",
        "imports": [],
        "notes": "int2str(x) → str(int(x))",
    },

    # File I/O
    "load": {
        "python": "mat_to_dict(scipy.io.loadmat(filename))",
        "imports": ["import scipy.io", "# from utils.mat_io import mat_to_dict"],
        "notes": "load(file) → mat_to_dict(scipy.io.loadmat(file)); must include mat_to_dict helper",
    },
    "save": {
        "python": "scipy.io.savemat(filename, {'var': var})",
        "imports": ["import scipy.io"],
        "notes": "save(file,'var1','var2') → scipy.io.savemat(file, {'var1':var1,'var2':var2})",
    },
    "fopen": {
        "python": "open(filename, mode)",
        "imports": [],
        "notes": "fopen(f,'r') → open(f,'r'); fopen(f,'w') → open(f,'w')",
    },
    "fclose": {
        "python": "f.close()",
        "imports": [],
        "notes": "fclose(fid) → use context manager 'with open() as f:'",
    },
    "fprintf": {
        "python": "print(f'...')",
        "imports": [],
        "notes": "fprintf(format,args) → print(f-string); fprintf(fid,fmt,args) → f.write(f-string)",
    },
    "disp": {
        "python": "print(x)",
        "imports": [],
        "notes": "disp(x) → print(x)",
    },

    # Interpolation
    "interp1": {
        "python": "scipy.interpolate.interp1d(x, y, kind='linear')(xq)",
        "imports": ["import scipy.interpolate"],
        "notes": "interp1(x,y,xq) → f=interp1d(x,y); f(xq); kind='linear'/'cubic'/'nearest'",
    },
    "interp2": {
        "python": "scipy.interpolate.RegularGridInterpolator((x,y), Z)(pts)",
        "imports": ["import scipy.interpolate"],
        "notes": "interp2(X,Y,Z,Xq,Yq) → use RegularGridInterpolator",
    },
    "griddata": {
        "python": "scipy.interpolate.griddata(points, values, xi)",
        "imports": ["import scipy.interpolate"],
        "notes": "griddata(x,y,v,xq,yq) → griddata((x.ravel(),y.ravel()),v.ravel(),(xq,yq))",
    },

    # Signal processing
    "fft": {
        "python": "np.fft.fft(x)",
        "imports": ["import numpy as np"],
        "notes": "fft(x) → np.fft.fft(x)",
    },
    "ifft": {
        "python": "np.fft.ifft(x)",
        "imports": ["import numpy as np"],
        "notes": "ifft(x) → np.fft.ifft(x)",
    },
    "fftshift": {
        "python": "np.fft.fftshift(x)",
        "imports": ["import numpy as np"],
        "notes": "fftshift(x) → np.fft.fftshift(x)",
    },
    "conv": {
        "python": "np.convolve(a, b)",
        "imports": ["import numpy as np"],
        "notes": "conv(a,b) → np.convolve(a,b)",
    },
    "filter": {
        "python": "scipy.signal.lfilter(b, a, x)",
        "imports": ["import scipy.signal"],
        "notes": "filter(b,a,x) → scipy.signal.lfilter(b,a,x)",
    },

    # GUI / control flow stubs
    "uigetfile": {
        "python": "input('Enter file path: ')",
        "imports": ["import os"],
        "notes": "uigetfile → input() stub; os.path.split() for path/name separation",
    },
    "waitbar": {
        "python": "tqdm(total=N)",
        "imports": ["from tqdm import tqdm"],
        "notes": "waitbar(0,'msg') → pbar=tqdm(total=N); waitbar(x,h) → pbar.update(1)",
    },
    "assignin": {
        "python": "# CONVERSION NOTE: assignin removed",
        "imports": [],
        "notes": "assignin is workspace manipulation; remove and restructure code",
    },
    "evalin": {
        "python": "# CONVERSION NOTE: evalin removed",
        "imports": [],
        "notes": "evalin is workspace manipulation; remove and restructure code",
    },
    "eval": {
        "python": "# CONVERSION NOTE: eval replaced with dict dispatch",
        "imports": [],
        "notes": "eval(sprintf('var%d',n)) → use dict dispatch or getattr()",
    },
    "inputname": {
        "python": "# CONVERSION NOTE: inputname not available in Python",
        "imports": [],
        "notes": "No direct equivalent; restructure if needed",
    },
    "nargin": {
        "python": "len(args)",
        "imports": [],
        "notes": "nargin → use *args or default parameter values",
    },
    "nargout": {
        "python": "# CONVERSION NOTE: nargout not needed",
        "imports": [],
        "notes": "Python returns tuples; caller decides what to unpack",
    },
    "error": {
        "python": "raise ValueError(msg)",
        "imports": [],
        "notes": "error('msg',args) → raise ValueError(f'msg')",
    },
    "warning": {
        "python": "import warnings; warnings.warn(msg)",
        "imports": ["import warnings"],
        "notes": "warning('msg') → warnings.warn('msg')",
    },
    "tic": {
        "python": "import time; t0 = time.time()",
        "imports": ["import time"],
        "notes": "tic → t0=time.time(); toc → print(time.time()-t0)",
    },
    "toc": {
        "python": "print(f'Elapsed: {time.time()-t0:.3f}s')",
        "imports": ["import time"],
        "notes": "toc → time.time()-t0",
    },
    "pause": {
        "python": "import time; time.sleep(n)",
        "imports": ["import time"],
        "notes": "pause(n) → time.sleep(n)",
    },
    "clc": {
        "python": "# clc removed (clear console not needed in scripts)",
        "imports": [],
        "notes": "clc → remove",
    },
    "clear": {
        "python": "# clear removed",
        "imports": [],
        "notes": "clear → remove (variables go out of scope naturally)",
    },
    "close": {
        "python": "plt.close('all')",
        "imports": ["import matplotlib.pyplot as plt"],
        "notes": "close all → plt.close('all')",
    },

    # Plotting
    "figure": {
        "python": "fig, ax = plt.subplots()",
        "imports": ["import matplotlib.pyplot as plt"],
        "notes": "figure() → fig, ax = plt.subplots(); figure(n) → fig = plt.figure(n)",
    },
    "subplot": {
        "python": "ax = fig.add_subplot(m, n, p)",
        "imports": ["import matplotlib.pyplot as plt"],
        "notes": "subplot(m,n,p) → ax=fig.add_subplot(m,n,p) or use plt.subplots(m,n)",
    },
    "plot": {
        "python": "ax.plot(x, y)",
        "imports": ["import matplotlib.pyplot as plt"],
        "notes": "plot(x,y,'r-') → ax.plot(x,y,'r-'); hold on → multiple ax.plot() calls",
    },
    "semilogx": {
        "python": "ax.semilogx(x, y)",
        "imports": ["import matplotlib.pyplot as plt"],
        "notes": "semilogx(x,y) → ax.semilogx(x,y)",
    },
    "semilogy": {
        "python": "ax.semilogy(x, y)",
        "imports": ["import matplotlib.pyplot as plt"],
        "notes": "semilogy(x,y) → ax.semilogy(x,y)",
    },
    "loglog": {
        "python": "ax.loglog(x, y)",
        "imports": ["import matplotlib.pyplot as plt"],
        "notes": "loglog(x,y) → ax.loglog(x,y)",
    },
    "bar": {
        "python": "ax.bar(x, y)",
        "imports": ["import matplotlib.pyplot as plt"],
        "notes": "bar(x,y) → ax.bar(x,y); grouped: offset x positions with width",
    },
    "barh": {
        "python": "ax.barh(y, x)",
        "imports": ["import matplotlib.pyplot as plt"],
        "notes": "barh(x,y) → ax.barh(y,x)",
    },
    "polar": {
        "python": "fig, ax = plt.subplots(subplot_kw={'projection': 'polar'}); ax.plot(theta, r)",
        "imports": ["import matplotlib.pyplot as plt"],
        "notes": "polar(theta,r) → use polar projection subplot",
    },
    "fill": {
        "python": "ax.fill(x, y, color='b')",
        "imports": ["import matplotlib.pyplot as plt"],
        "notes": "fill(x,y,'b') → ax.fill(x,y,color='b')",
    },
    "patch": {
        "python": "ax.fill(x, y, facecolor=c, edgecolor=e)",
        "imports": ["import matplotlib.pyplot as plt"],
        "notes": "patch → ax.fill() or mpl.patches.Polygon",
    },
    "scatter": {
        "python": "ax.scatter(x, y)",
        "imports": ["import matplotlib.pyplot as plt"],
        "notes": "scatter(x,y) → ax.scatter(x,y)",
    },
    "errorbar": {
        "python": "ax.errorbar(x, y, yerr=e)",
        "imports": ["import matplotlib.pyplot as plt"],
        "notes": "errorbar(x,y,e) → ax.errorbar(x,y,yerr=e)",
    },
    "contour": {
        "python": "ax.contour(X, Y, Z)",
        "imports": ["import matplotlib.pyplot as plt"],
        "notes": "contour(X,Y,Z) → ax.contour(X,Y,Z)",
    },
    "contourf": {
        "python": "ax.contourf(X, Y, Z)",
        "imports": ["import matplotlib.pyplot as plt"],
        "notes": "contourf(X,Y,Z) → ax.contourf(X,Y,Z)",
    },
    "mesh": {
        "python": "ax.plot_wireframe(X, Y, Z)",
        "imports": ["import matplotlib.pyplot as plt", "from mpl_toolkits.mplot3d import Axes3D"],
        "notes": "mesh(X,Y,Z) → ax = fig.add_subplot(projection='3d'); ax.plot_wireframe(X,Y,Z)",
    },
    "surf": {
        "python": "ax.plot_surface(X, Y, Z)",
        "imports": ["import matplotlib.pyplot as plt", "from mpl_toolkits.mplot3d import Axes3D"],
        "notes": "surf(X,Y,Z) → ax.plot_surface(X,Y,Z)",
    },
    "xlabel": {
        "python": "ax.set_xlabel(label)",
        "imports": [],
        "notes": "xlabel('str') → ax.set_xlabel('str')",
    },
    "ylabel": {
        "python": "ax.set_ylabel(label)",
        "imports": [],
        "notes": "ylabel('str') → ax.set_ylabel('str')",
    },
    "zlabel": {
        "python": "ax.set_zlabel(label)",
        "imports": [],
        "notes": "zlabel('str') → ax.set_zlabel('str')",
    },
    "title": {
        "python": "ax.set_title(title)",
        "imports": [],
        "notes": "title('str') → ax.set_title('str')",
    },
    "legend": {
        "python": "ax.legend(labels)",
        "imports": [],
        "notes": "legend('a','b') → ax.legend(['a','b'])",
    },
    "grid": {
        "python": "ax.grid(True)",
        "imports": [],
        "notes": "grid on → ax.grid(True); grid off → ax.grid(False)",
    },
    "hold": {
        "python": "# hold on/off not needed; just call ax.plot() multiple times",
        "imports": [],
        "notes": "hold on → multiple plot calls on same ax; hold off → start new figure",
    },
    "xlim": {
        "python": "ax.set_xlim([a, b])",
        "imports": [],
        "notes": "xlim([a b]) → ax.set_xlim([a,b])",
    },
    "ylim": {
        "python": "ax.set_ylim([a, b])",
        "imports": [],
        "notes": "ylim([a b]) → ax.set_ylim([a,b])",
    },
    "zlim": {
        "python": "ax.set_zlim([a, b])",
        "imports": [],
        "notes": "zlim([a b]) → ax.set_zlim([a,b])",
    },
    "axis": {
        "python": "ax.axis([xmin, xmax, ymin, ymax])",
        "imports": [],
        "notes": "axis([a b c d]) → ax.axis([a,b,c,d]); axis equal → ax.set_aspect('equal')",
    },
    "set": {
        "python": "ax.set(property=value)",
        "imports": [],
        "notes": "set(h,'Property',val) → use object methods e.g. ax.set_linewidth(2)",
    },
    "get": {
        "python": "ax.get_xlim()",
        "imports": [],
        "notes": "get(h,'Property') → use object attribute/method",
    },
    "colorbar": {
        "python": "fig.colorbar(im, ax=ax)",
        "imports": [],
        "notes": "colorbar → fig.colorbar(mappable, ax=ax)",
    },
    "colormap": {
        "python": "ax.set_cmap('jet')",
        "imports": ["import matplotlib.pyplot as plt"],
        "notes": "colormap(jet) → ax.set_cmap('jet') or plt.colormaps['jet']",
    },
    "caxis": {
        "python": "im.set_clim(vmin, vmax)",
        "imports": [],
        "notes": "caxis([a b]) → im.set_clim(a,b)",
    },
    "clabel": {
        "python": "ax.clabel(cs, inline=True)",
        "imports": [],
        "notes": "clabel(cs) → ax.clabel(cs,inline=True)",
    },
    "text": {
        "python": "ax.text(x, y, 'string')",
        "imports": [],
        "notes": "text(x,y,'str') → ax.text(x,y,'str')",
    },
    "annotation": {
        "python": "ax.annotate('str', xy=(x,y))",
        "imports": [],
        "notes": "annotation('arrow',...) → ax.annotate()",
    },
    "savefig": {
        "python": "fig.savefig(filename, dpi=300, bbox_inches='tight')",
        "imports": [],
        "notes": "savefig(file) → fig.savefig(file, dpi=300, bbox_inches='tight')",
    },
    "print": {
        "python": "fig.savefig(filename, format='pdf')",
        "imports": [],
        "notes": "print('-dpdf',file) → fig.savefig(file,format='pdf')",
    },
    "openfig": {
        "python": "# CONVERSION NOTE: openfig cannot load .fig files; recreate plot programmatically",
        "imports": [],
        "notes": ".fig files are MATLAB binary; must recreate plot in Python",
    },
    "gca": {
        "python": "plt.gca()",
        "imports": ["import matplotlib.pyplot as plt"],
        "notes": "gca() → plt.gca() or pass ax explicitly",
    },
    "gcf": {
        "python": "plt.gcf()",
        "imports": ["import matplotlib.pyplot as plt"],
        "notes": "gcf() → plt.gcf()",
    },
    "shading": {
        "python": "# shading flat → use shading='flat' in pcolormesh",
        "imports": [],
        "notes": "shading interp → use shading='gouraud' in pcolormesh",
    },

    # Misc
    "iscell": {
        "python": "isinstance(x, list)",
        "imports": [],
        "notes": "iscell(x) → isinstance(x, list)",
    },
    "isstruct": {
        "python": "isinstance(x, dict)",
        "imports": [],
        "notes": "isstruct(x) → isinstance(x, dict)",
    },
    "isnumeric": {
        "python": "isinstance(x, (int, float, np.ndarray))",
        "imports": ["import numpy as np"],
        "notes": "isnumeric(x) → isinstance(x,(int,float,np.ndarray))",
    },
    "ischar": {
        "python": "isinstance(x, str)",
        "imports": [],
        "notes": "ischar(x) → isinstance(x,str)",
    },
    "islogical": {
        "python": "isinstance(x, (bool, np.ndarray)) and x.dtype == bool",
        "imports": ["import numpy as np"],
        "notes": "islogical(x) → x.dtype == bool for arrays",
    },
    "isnan": {
        "python": "np.isnan(x)",
        "imports": ["import numpy as np"],
        "notes": "isnan(x) → np.isnan(x)",
    },
    "isinf": {
        "python": "np.isinf(x)",
        "imports": ["import numpy as np"],
        "notes": "isinf(x) → np.isinf(x)",
    },
    "isfinite": {
        "python": "np.isfinite(x)",
        "imports": ["import numpy as np"],
        "notes": "isfinite(x) → np.isfinite(x)",
    },
    "any": {
        "python": "np.any(x)",
        "imports": ["import numpy as np"],
        "notes": "any(x) → np.any(x)",
    },
    "all": {
        "python": "np.all(x)",
        "imports": ["import numpy as np"],
        "notes": "all(x) → np.all(x)",
    },
    "unique": {
        "python": "np.unique(x)",
        "imports": ["import numpy as np"],
        "notes": "unique(x) → np.unique(x); [u,i,j]=unique(x) → u,i,j=np.unique(x,return_index=True,return_inverse=True)",
    },
    "intersect": {
        "python": "np.intersect1d(a, b)",
        "imports": ["import numpy as np"],
        "notes": "intersect(a,b) → np.intersect1d(a,b)",
    },
    "union": {
        "python": "np.union1d(a, b)",
        "imports": ["import numpy as np"],
        "notes": "union(a,b) → np.union1d(a,b)",
    },
    "setdiff": {
        "python": "np.setdiff1d(a, b)",
        "imports": ["import numpy as np"],
        "notes": "setdiff(a,b) → np.setdiff1d(a,b)",
    },
    "ismember": {
        "python": "np.isin(a, b)",
        "imports": ["import numpy as np"],
        "notes": "ismember(a,b) → np.isin(a,b)",
    },
    "fieldnames": {
        "python": "list(s.keys())",
        "imports": [],
        "notes": "fieldnames(s) → list(s.keys()) where s is a dict",
    },
    "struct": {
        "python": "{}",
        "imports": [],
        "notes": "struct() → {}; struct('f1',v1,'f2',v2) → {'f1':v1,'f2':v2}",
    },
    "cell": {
        "python": "[None] * n",
        "imports": [],
        "notes": "cell(1,n) → [None]*n; cell(m,n) → [[None]*n for _ in range(m)]",
    },
    "cellfun": {
        "python": "[f(x) for x in lst]",
        "imports": [],
        "notes": "cellfun(@f,c) → [f(x) for x in c] or list(map(f,c))",
    },
    "arrayfun": {
        "python": "np.vectorize(f)(A)",
        "imports": ["import numpy as np"],
        "notes": "arrayfun(@f,A) → np.vectorize(f)(A)",
    },
    "structfun": {
        "python": "{k: f(v) for k,v in s.items()}",
        "imports": [],
        "notes": "structfun(@f,s) → {k:f(v) for k,v in s.items()}",
    },
    "containers.Map": {
        "python": "{}",
        "imports": [],
        "notes": "containers.Map(keys,vals) → dict(zip(keys,vals))",
    },
    "who": {
        "python": "# who removed",
        "imports": [],
        "notes": "who/whos → remove",
    },
    "whos": {
        "python": "# whos removed",
        "imports": [],
        "notes": "whos → remove",
    },
    "addpath": {
        "python": "import sys; sys.path.insert(0, path)",
        "imports": ["import sys"],
        "notes": "addpath(p) → sys.path.insert(0,p)",
    },
    "cd": {
        "python": "os.chdir(path)",
        "imports": ["import os"],
        "notes": "cd(path) → os.chdir(path)",
    },
    "pwd": {
        "python": "os.getcwd()",
        "imports": ["import os"],
        "notes": "pwd → os.getcwd()",
    },
    "dir": {
        "python": "os.listdir(path)",
        "imports": ["import os"],
        "notes": "dir(path) → os.listdir(path) or glob.glob(pattern)",
    },
    "exist": {
        "python": "os.path.exists(path)",
        "imports": ["import os"],
        "notes": "exist(file,'file') → os.path.exists(file)",
    },
    "mkdir": {
        "python": "Path(path).mkdir(parents=True, exist_ok=True)",
        "imports": ["from pathlib import Path"],
        "notes": "mkdir(a,b) → Path(a/b).mkdir(parents=True,exist_ok=True)",
    },
    "fullfile": {
        "python": "os.path.join(parts)",
        "imports": ["import os"],
        "notes": "fullfile(a,b,c) → os.path.join(a,b,c) or Path(a)/b/c",
    },
    "fileparts": {
        "python": "os.path.split(path)",
        "imports": ["import os"],
        "notes": "[p,n,e]=fileparts(f) → p,n=os.path.split(f); e from os.path.splitext",
    },
    "pyenv": {
        "python": "# CONVERSION NOTE: pyenv removed — Python script runs natively",
        "imports": [],
        "notes": "pyenv is MATLAB-specific; remove entirely",
    },
    "pyrunfile": {
        "python": "# CONVERSION NOTE: pyrunfile removed — convert as separate Python module",
        "imports": [],
        "notes": "pyrunfile runs .py from MATLAB; remove and convert target script instead",
    },
    "typecast": {
        "python": "np.frombuffer(x.tobytes(), dtype=np.uint8)",
        "imports": ["import numpy as np"],
        "notes": "typecast(x,type) → np.frombuffer(x.tobytes(),dtype=type)",
    },
    "bitand": {
        "python": "a & b",
        "imports": [],
        "notes": "bitand(a,b) → a & b",
    },
    "bitor": {
        "python": "a | b",
        "imports": [],
        "notes": "bitor(a,b) → a | b",
    },
    "bitxor": {
        "python": "a ^ b",
        "imports": [],
        "notes": "bitxor(a,b) → a ^ b",
    },
    "input": {
        "python": "input(prompt)",
        "imports": [],
        "notes": "input('msg') → input('msg') in Python too; use float(input()) for numbers",
    },
}
