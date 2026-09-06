@echo off
REM ============================================
REM  Civ4 PBEM Manager - Dev Runner
REM  Uruchamia aplikacje bez budowania .exe
REM ============================================

REM Sprawdz czy Python jest dostepny
python --version >nul 2>&1
if errorlevel 1 (
    echo [BLAD] Python nie znaleziony w PATH!
    echo Zainstaluj Python 3.10+ z https://python.org
    pause
    exit /b 1
)

REM Sprawdz czy venv istnieje, jesli nie - stworz
if not exist "venv\" (
    echo [INFO] Tworzenie srodowiska wirtualnego...
    python -m venv venv
    echo [INFO] Instalacja zaleznosci...
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

REM Uruchom aplikacje
echo.
echo ========================================
echo   Civ4 PBEM Manager - DEV MODE
echo ========================================
echo.
python main.py %*
