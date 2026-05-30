@echo off
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

echo [1/3] Instalowanie zaleznosci...
pip install -r requirements.txt
if errorlevel 1 (
    echo [BLAD] Nie udalo sie zainstalowac zaleznosci!
    pause
    exit /b 1
)
echo.

echo [2/3] Budowanie .exe...
pyinstaller build.spec --noconfirm
if errorlevel 1 (
    echo [BLAD] Budowanie nie powiodlo sie!
    pause
    exit /b 1
)
echo.

echo [3/3] Gotowe!
echo.
echo ==========================================
echo   Plik wynikowy: dist\Civ4PBEMManager.exe
echo ==========================================
echo.
echo Mozesz skopiowac dist\Civ4PBEMManager.exe gdzie chcesz.
echo.
pause
