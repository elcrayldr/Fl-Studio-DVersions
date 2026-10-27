# -*- mode: python ; coding: utf-8 -*-
# Compilar en Windows:  python -m PyInstaller --noconfirm --clean CrayFLPAnalyzer.spec
# Resultado: dist\CrayFLPAnalyzer\CrayFLPAnalyzer.exe  (modo carpeta, base de la versión portable)
import os
ROOT = os.path.abspath(SPECPATH)
a = Analysis(
    [os.path.join(ROOT, "run_app.py")],
    pathex=[os.path.join(ROOT, "src")],
    datas=[(os.path.join(ROOT, "docs"), "docs")],
    hiddenimports=["tkinter", "tkinter.ttk", "tkinter.filedialog", "tkinter.messagebox"],
    excludes=["pytest", "numpy", "PIL"],
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="CrayFLPAnalyzer",
          console=False, disable_windowed_traceback=False,
          icon=os.path.join(ROOT, "assets", "cray.ico") if os.path.isfile(os.path.join(ROOT, "assets", "cray.ico")) else None)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="CrayFLPAnalyzer")
