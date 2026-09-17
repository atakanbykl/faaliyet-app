#!/bin/bash
# FieldOps Assistant - Linux x86_64 Portable Launcher

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "==================================================="
echo "  FieldOps Assistant - Saha Yonetim Asistani (Linux)"
echo "==================================================="

# 1. Eger derlenmis standalone ELF/AppImage binary varsa onu calistir
if [ -f "bin/linux/fieldops.bin" ]; then
    echo "[BILGI] Derlenmis Linux binary calistiriliyor..."
    chmod +x "bin/linux/fieldops.bin"
    exec "./bin/linux/fieldops.bin"
fi

# 2. Sanal ortam (.venv) kontrolü
if [ -f ".venv/bin/python" ]; then
    echo "[BILGI] Sanal ortam (.venv) uzerinden baslatiliyor..."
    exec .venv/bin/python app/main.py
fi

# 3. Sistemde python3 kontrolü
if command -v python3 &>/dev/null; then
    echo "[BILGI] python3 uzerinden baslatiliyor..."
    exec python3 app/main.py
fi

echo "[HATA] Sistemde calistirilabilir Python ortami bulunamadi!"
echo "Lütfen önce ./setup_env.sh calistirarak ortami hazirlayiniz."
exit 1

