@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ==========================================
echo   Civ4 PBEM Manager - Build Script
echo ==========================================
echo.

:: Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [BLAD] Python nie znaleziony! Zainstaluj Python 3.10+ i dodaj do PATH.
    pause
    exit /b 1
)

:: Check if pip is available
pip --version >nul 2>&1
if errorlevel 1 (
    echo [BLAD] pip nie znaleziony!
    pause
    exit /b 1
)

echo [1/5] Instalowanie zaleznosci...
pip install -r requirements.txt
if errorlevel 1 (
    echo [BLAD] Nie udalo sie zainstalowac zaleznosci!
    pause
    exit /b 1
)
echo.

echo [2/5] Generowanie ikony (jesli brak)...
if not exist icon.ico (
    pip install Pillow --quiet
    python generate_icon.py
)
echo.

set "UPX_EXE=%~dp0tools\upx\upx.exe"
set "USE_UPX=0"

echo [3/5] UPX (kompresja exe, ~30%% mniej)...
if exist "%UPX_EXE%" (
    set "USE_UPX=1"
    set "PATH=%~dp0tools\upx;%PATH%"
    echo [OK] Lokalny UPX: %UPX_EXE%
    "%UPX_EXE%" --version
) else (
    where upx >nul 2>&1
    if not errorlevel 1 (
        set "USE_UPX=1"
        echo [OK] UPX w systemowym PATH:
        upx --version
    ) else (
        echo [INFO] Brak UPX — pobieram do tools\upx\...
        powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\install_upx.ps1"
        if exist "%UPX_EXE%" (
            set "USE_UPX=1"
            set "PATH=%~dp0tools\upx;%PATH%"
            echo [OK] UPX zainstalowany lokalnie.
            "%UPX_EXE%" --version
        ) else (
            echo [UWAGA] Nie udalo sie pobrac UPX — budowanie bez kompresji.
        )
    )
)
echo.

echo [4/5] Budowanie .exe...
if exist "venv\Scripts\pyinstaller.exe" (
    set "PYINSTALLER=venv\Scripts\pyinstaller.exe"
) else (
    set "PYINSTALLER=pyinstaller"
)
"%PYINSTALLER%" build.spec --noconfirm
if errorlevel 1 (
    echo [BLAD] Budowanie nie powiodlo sie!
    pause
    exit /b 1
)
echo.

echo [5/5] Podsumowanie
echo ==========================================
python -c "from src.config import APP_VERSION, version_label; print('  Wersja:', APP_VERSION, '(' + version_label() + ')')"
echo   GOTOWE!
echo ==========================================
echo.
for %%A in (dist\Civ4PBEMManager.exe) do echo   Plik: dist\Civ4PBEMManager.exe (%%~zA bytes)
if "%USE_UPX%"=="1" (
    echo   Kompresja UPX: wlaczona
) else (
    echo   Kompresja UPX: wylaczona
)
echo.
pause
