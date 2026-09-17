@echo off
setlocal
cd /d "%~dp0"
title FieldOps Assistant - Ortam Kurulum Scripti (Windows)

echo ===================================================
echo   FieldOps Assistant - Otomatik Ortam Kurulumu
echo ===================================================

REM 1. Python kontrolu
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [HATA] Sistemde Python bulunamadi!
    echo Lutfen Python 3.9 veya daha guncel bir surumu yukleyip PATH ortam degiskenine ekleyin.
    pause
    exit /b 1
)

echo [1/4] Python tespit edildi:
python --version

REM 2. Sanal Ortam (.venv) Kontrolu / Olusturma
if not exist ".venv" (
    echo [2/4] Sanal ortam olusturuluyor (.venv)...
    python -m venv .venv
    if %ERRORLEVEL% neq 0 (
        echo [HATA] Sanal ortam olusturulamadi!
        pause
        exit /b 1
    )
) else (
    echo [2/4] Mevcut sanal ortam kullaniliyor (.venv).
)

REM 3. Sanal Ortami Aktif Et ve Bagimliliklari Yukle
echo [3/4] Bagimliliklar yukleniyor (requirements.txt)...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo [HATA] Bagimliliklar yuklenirken hata olustu!
    pause
    exit /b 1
)

REM 4. Otomatik Testleri Calistir
echo [4/4] Cekirdek moduller dogrulaniyor (tests/test_core.py)...
python tests/test_core.py
if %ERRORLEVEL% neq 0 (
    echo [UYARI] Testlerde bazi sorunlar tespit edildi!
) else (
    echo [BASARILI] Tum testler basariyla gecti!
)

echo ===================================================
echo   Kurulum Tamamlandi!
echo   Uygulamayi baslatmak icin FieldOps_Windows.bat
echo   dosyasini calistirabilirsiniz.
echo ===================================================
pause

