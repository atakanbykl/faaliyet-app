@echo off
setlocal
cd /d "%~dp0"
title FieldOps Assistant - Saha Operasyon Yoneticisi

echo ===================================================
echo   FieldOps Assistant - Saha Yonetim Asistani
echo ===================================================

REM 1. Eger derlenmis standalone binary varsa onu calistir
if exist "bin\windows\fieldops.exe" (
    echo [BILGI] Derlenmis Windows binary calistiriliyor...
    start "" "bin\windows\fieldops.exe"
    exit /b 0
)

REM 2. Sanal ortam kontrolu [.venv veya venv]
if exist ".venv\Scripts\python.exe" (
    echo [BILGI] Sanal ortam [.venv] uzerinden baslatiliyor...
    ".venv\Scripts\python.exe" app\main.py
    exit /b 0
)

if exist "venv\Scripts\python.exe" (
    echo [BILGI] Sanal ortam [venv] uzerinden baslatiliyor...
    "venv\Scripts\python.exe" app\main.py
    exit /b 0
)

REM 3. Sistem Python kontrolu
where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [BILGI] Sistem Python uzerinden baslatiliyor...
    python app\main.py
    exit /b 0
)

where py >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [BILGI] Python Launcher uzerinden baslatiliyor...
    py app\main.py
    exit /b 0
)

echo.
echo [HATA] Sistemde calistirilabilir Python ortami bulunamadi!
echo Lutfen sisteminize Python yukleyip gereksinimleri kurunuz:
echo   pip install -r requirements.txt
echo.
pause
