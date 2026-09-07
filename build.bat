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

set "USE_UPX=0"

echo [3/5] UPX wylaczony (Windows Smart App Control blokuje spakowane DLL-e Qt)
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
