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

echo [1/4] Instalowanie zaleznosci...
pip install -r requirements.txt
if errorlevel 1 (
    echo [BLAD] Nie udalo sie zainstalowac zaleznosci!
    pause
    exit /b 1
)
echo.

echo [2/4] Generowanie ikony (jesli brak)...
if not exist icon.ico (
    pip install Pillow --quiet
    python generate_icon.py
)
echo.

echo [3/4] Sprawdzanie UPX (kompresja)...
where upx >nul 2>&1
if errorlevel 1 (
    echo [INFO] UPX nie znaleziony - budowanie bez kompresji.
    echo        Dla mniejszego .exe zainstaluj UPX:
    echo        https://github.com/upx/upx/releases
    echo        i dodaj do PATH.
    echo.
) else (
    echo [OK] UPX znaleziony - kompresja wlaczona.
    echo.
)

echo [4/4] Budowanie .exe...
pyinstaller build.spec --noconfirm
if errorlevel 1 (
    echo [BLAD] Budowanie nie powiodlo sie!
    pause
    exit /b 1
)
echo.

:: Show result size
echo ==========================================
echo   GOTOWE!
echo ==========================================
echo.
for %%A in (dist\Civ4PBEMManager.exe) do echo   Plik: dist\Civ4PBEMManager.exe (%%~zA bytes)
echo.
echo   Wskazowki aby zmniejszyc rozmiar:
echo   1. Zainstaluj UPX i dodaj do PATH (oszczedza ~30%%)
echo   2. Uzyj PyQt5-slim: pip install PyQt5==5.15.9 (bez WebEngine)
echo   3. Wiecej info: README.md
echo.
pause
