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

REM 2. Sanal ortam (.venv) kontrolu
if exist ".venv\Scripts\python.exe" (
    echo [BILGI] Sanal ortam (.venv) uzerinden baslatiliyor...
    ".venv\Scripts\python.exe" app\main.py
    exit /b 0
)

REM 3. Sistemde Python kontrolu
where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [BILGI] Sistem Python uzerinden baslatiliyor...
    python app\main.py
    exit /b 0
)

echo [HATA] Sistemde calistirilabilir Python ortami bulunamadi!
echo Lutfen once "setup_env.bat" dosyasini calistirarak ortami hazirlayiniz.
pause

