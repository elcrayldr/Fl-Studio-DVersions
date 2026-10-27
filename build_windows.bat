@echo off
rem ===== Cray FLP Analyzer - compilación en Windows (rutas relativas) =====
setlocal
cd /d "%~dp0"
set VERSION=0.2.0

echo [1/6] Entorno virtual...
if not exist .venv ( py -3 -m venv .venv || goto :error )
call .venv\Scripts\activate.bat || goto :error
python -m pip install --upgrade pip || goto :error
pip install -r requirements-dev.txt || goto :error

echo [2/6] Pruebas...
set PYTHONPATH=%CD%\src
python -m unittest discover -s tests || goto :error

echo [3/6] PyInstaller...
python -m PyInstaller --noconfirm --clean CrayFLPAnalyzer.spec || goto :error

echo [4/6] Prueba de humo del ejecutable (CLI)...
dist\CrayFLPAnalyzer\CrayFLPAnalyzer.exe analyze "samples\synthetic\synthetic_valido.flp" > nul || goto :error

echo [5/6] Version portable...
if not exist release mkdir release
if exist release\CrayFLPAnalyzer-Portable.zip del release\CrayFLPAnalyzer-Portable.zip
powershell -NoProfile -Command "Compress-Archive -Path 'dist\CrayFLPAnalyzer\*' -DestinationPath 'release\CrayFLPAnalyzer-Portable.zip'" || goto :error

echo [6/6] Instalador (requiere Inno Setup 6)...
set ISCC="%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist %ISCC% set ISCC="%ProgramFiles%\Inno Setup 6\ISCC.exe"
if exist %ISCC% (
  %ISCC% /DAppVersion=%VERSION% installer\CrayFLPAnalyzer.iss || goto :error
) else (
  echo AVISO: Inno Setup no encontrado. Instalalo y ejecuta ISCC sobre installer\CrayFLPAnalyzer.iss
)
echo Listo. Salida en la carpeta release\
exit /b 0
:error
echo ERROR en la compilacion. Revisa los mensajes anteriores.
exit /b 1
