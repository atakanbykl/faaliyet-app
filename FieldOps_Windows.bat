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

REM 2. Sistemde Python kontrolu
where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [BILGI] Python uzerinden baslatiliyor...
    python app\main.py
    exit /b 0
)

echo [HATA] Sistemde ne derlenmis binary (bin\windows\fieldops.exe) ne de Python bulundu!
echo Lutfen USB bellek icerisindeki bin klasorunu kontrol ediniz.
pause

