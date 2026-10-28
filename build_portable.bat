@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ==========================================
echo   Civ4 PBEM Manager - Portable Build
echo   OFFLINE (wheels\ + portable_python\)
echo ==========================================
echo.

set "PYDIR=%~dp0portable_python"
set "PY=%PYDIR%\python.exe"
set "WHEELS=%~dp0wheels"

if not exist "%PY%" (
    echo [BLAD] Brak portable_python\python.exe
    echo Popros o pelny OFFLINE BuildKit.
    pause
    exit /b 1
)
if not exist "%WHEELS%\." (
    echo [BLAD] Brak folderu wheels\
    echo To nie jest pelny offline kit.
    pause
    exit /b 1
)

echo [0/5] Python:
"%PY%" --version
if errorlevel 1 (
    echo [BLAD] Nie da sie uruchomic portable Python.
    pause
    exit /b 1
)
echo.

echo [1/5] Zaleznosci z wheels\ ^(bez internetu^)...
"%PY%" -m pip --version >nul 2>&1
if errorlevel 1 (
    echo [BLAD] Brak pip w portable_python. Kit uszkodzony.
    pause
    exit /b 1
)

"%PY%" -m pip install --no-index --find-links="%WHEELS%" -r requirements.txt
if errorlevel 1 (
    echo [BLAD] pip install z wheels nie powiodl sie.
    pause
    exit /b 1
)
echo.

echo [2/5] Ikona...
if not exist icon.ico (
    "%PY%" -m pip install --no-index --find-links="%WHEELS%" Pillow >nul 2>&1
    if exist generate_icon.py (
        "%PY%" generate_icon.py
    )
)
echo.

echo [3/5] UPX wylaczony ^(Smart App Control^)
echo.

echo [4/5] PyInstaller...
"%PY%" tools\gen_version_info.py
"%PY%" -m PyInstaller build.spec --noconfirm
if errorlevel 1 (
    echo [BLAD] Budowanie nie powiodlo sie!
    pause
    exit /b 1
)
echo.

echo [5/5] Gotowe
echo ==========================================
"%PY%" -c "from src.config import APP_VERSION, version_label; print('  Wersja:', APP_VERSION, '(' + version_label() + ')')"
echo   Plik: dist\Civ4PBEMManager.exe
for %%A in (dist\Civ4PBEMManager.exe) do echo   Rozmiar: %%~zA bytes
echo ==========================================
echo.
echo Uruchom: dist\Civ4PBEMManager.exe
echo ^(lokalny build - Smart App Control zwykle nie blokuje^)
echo.
pause
