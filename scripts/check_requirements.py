#!/usr/bin/env python3
"""
Narzędzie pomocnicze do sprawdzania kompletnosci `requirements.txt` względem importów w projekcie.
- Wyszukuje importy w plikach .py (wyłączając venv i foldery zewnętrzne)
- Porównuje z pakietami z `requirements.txt`
- Raportuje brakujące zależności (najprawdopodobniej nazwy pip)
- Opcjonalnie próbuje zainstalować brakujące pakiety (jeśli uruchomione z --install)

Użycie:
    python scripts/check_requirements.py [--install]

"""
import argparse
import os
import re
import sys
import subprocess
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(__file__))
REQ_FILE = os.path.join(ROOT, 'requirements.txt')

PY_FILE_EXTS = ('.py',)

IMPORT_RE = re.compile(r'^(?:from\s+([\w\.]+)\s+import|import\s+([\w\.]+))')

# Map common top-level import -> pip package name when they differ
COMMON_OVERRIDES = {
    'httpx': 'httpx',
    'fastapi': 'fastapi',
    'uvicorn': 'uvicorn',
    'spacy': 'spacy',
    'bs4': 'beautifulsoup4',
    'bs': 'beautifulsoup4',
    'PIL': 'pillow',
    'Crypto': 'pycryptodome',
    'sklearn': 'scikit-learn',
    'yaml': 'PyYAML',
    'cv2': 'opencv-python',
}


def collect_imports(root):
    imports = set()
    for dirpath, dirnames, filenames in os.walk(root):
        # skip venv and .git and node_modules
        if any(part in ('venv', '.venv', '.git', 'node_modules', '__pycache__', 'frontend') for part in dirpath.split(os.sep)):
            continue
        for fn in filenames:
            if not fn.endswith(PY_FILE_EXTS):
                continue
            path = os.path.join(dirpath, fn)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    for line in f:
                        m = IMPORT_RE.match(line.strip())
                        if m:
                            pkg = m.group(1) or m.group(2)
                            if pkg:
                                top = pkg.split('.')[0]
                                imports.add(top)
            except Exception:
                pass
    return imports


def read_requirements(req_file):
    if not os.path.exists(req_file):
        return []
    res = []
    with open(req_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            # take package name before any [extras],==,>=,<= etc
            pkg = re.split('[>=< \[]', line, 1)[0]
            res.append(pkg)
    return res


def map_import_to_package(name):
    return COMMON_OVERRIDES.get(name, name)


def is_stdlib_module(name):
    # Python 3.10+: sys.stdlib_module_names contains stdlib names
    try:
        import sys
        if hasattr(sys, 'stdlib_module_names'):
            return name in sys.stdlib_module_names
    except Exception:
        pass
    # Fallback to builtin names
    try:
        import sys
        if name in sys.builtin_module_names:
            return True
    except Exception:
        pass
    return False


def is_local_module(name, root):
    # Check if a local file or package exists with that name inside project
    candidate_py = os.path.join(root, name + '.py')
    candidate_pkg = os.path.join(root, name)
    if os.path.exists(candidate_py) or os.path.isdir(candidate_pkg):
        return True
    # also check nested in package folders
    for dirpath, dirnames, filenames in os.walk(root):
        if name + '.py' in filenames:
            return True
        if name in dirnames:
            # ensure it has __init__.py (package)
            if os.path.exists(os.path.join(dirpath, name, '__init__.py')):
                return True
    return False


def is_installed_package(name):
    # Try importlib to see if the package can be resolved outside the project
    try:
        import importlib.util, sys
        spec = importlib.util.find_spec(name)
        if spec is None:
            return False
        origin = getattr(spec, 'origin', None)
        if origin is None:
            # namespace package or builtin - consider installed
            return True
        # if origin path contains site-packages or dist-packages or pip-installed marker
        lower = origin.lower()
        if 'site-packages' in lower or 'dist-packages' in lower or ('python' in lower and 'lib' in lower):
            return True
        # if it's a compiled builtin (.pyd/.so) treat as installed
        if lower.endswith(('.pyd', '.so', '.dll')):
            return True
        # otherwise, if origin is not inside the project, treat as installed
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        if not os.path.abspath(origin).startswith(project_root):
            return True
        return False
    except Exception:
        return False


def check_missing(installed_pkgs, imports):
    mapped = set(map(map_import_to_package, imports))
    missing = sorted([p for p in mapped if p not in installed_pkgs])
    return missing


def get_installed_packages():
    try:
        import pkg_resources
        return {pkg.key for pkg in pkg_resources.working_set}
    except Exception:
        # fallback to pip list
        out = subprocess.check_output([sys.executable, '-m', 'pip', 'list', '--format=freeze'], text=True)
        pkgs = set()
        for line in out.splitlines():
            if '==' in line:
                pkgs.add(line.split('==',1)[0].lower())
        return pkgs


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--install', action='store_true', help='Try to pip install missing packages')
    p.add_argument('--root', default=ROOT, help='Project root')
    args = p.parse_args()
    imports = collect_imports(args.root)
    reqs = read_requirements(os.path.join(args.root, 'requirements.txt'))
    req_names = {r.lower() for r in reqs}

    missing = []
    externals = []
    for imp in sorted(imports):
        if not imp:
            continue
        if is_stdlib_module(imp):
            continue
        if is_local_module(imp, args.root):
            continue
        externals.append(imp)
        mapped = map_import_to_package(imp).lower()
        if mapped not in req_names and not is_installed_package(imp):
            missing.append(mapped)

    print('\nDetected top-level imports (external candidates):')
    print(', '.join(sorted(set(externals))))
    print('\nPackages listed in requirements.txt:')
    print(', '.join(sorted(reqs)))
    print('\nMissing packages (likely not in requirements.txt):')
    if missing:
        for m in sorted(set(missing)):
            print(' -', m)
    else:
        print(' None! requirements.txt looks complete relative to external imports.')

    if args.install and missing:
        print('\nAttempting to pip install missing packages...')
        for pkg in sorted(set(missing)):
            try:
                print('pip install', pkg)
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', pkg])
            except Exception as e:
                print('Failed to install', pkg, e)


if __name__ == '__main__':
    main()
