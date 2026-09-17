#!/usr/bin/env bash
# FieldOps Assistant - Linux Otomatik Ortam Kurulum Scripti

set -e
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "==================================================="
echo "  FieldOps Assistant - Linux Ortam Kurulumu"
echo "==================================================="

# 1. python3 kontrolü
if ! command -v python3 &>/dev/null; then
    echo "[HATA] Sistemde python3 bulunamadi!"
    echo "Lütfen önce python3 ve python3-venv paketlerini yükleyin (örn: sudo apt install python3 python3-venv python3-pip)"
    exit 1
fi

echo "[1/4] python3 tespit edildi:"
python3 --version

# 2. Sanal Ortam (.venv)
if [ ! -d ".venv" ]; then
    echo "[2/4] Sanal ortam olusturuluyor (.venv)..."
    python3 -m venv .venv
else
    echo "[2/4] Mevcut sanal ortam kullaniliyor (.venv)."
fi

# 3. Bağımlılıkların Kurulumu
echo "[3/4] Bagimliliklar yukleniyor (requirements.txt)..."
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 4. Doğrulama Testi
echo "[4/4] Cekirdek moduller dogrulaniyor (tests/test_core.py)..."
python tests/test_core.py

echo "==================================================="
echo "  Kurulum Tamamlandi!"
echo "  Uygulamayi baslatmak icin ./FieldOps_Linux.sh"
echo "  calistirabilirsiniz."
echo "==================================================="

