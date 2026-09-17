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

# 2. Sistemde python3 kontrolu
if command -v python3 &>/dev/null; then
    echo "[BILGI] python3 uzerinden baslatiliyor..."
    exec python3 app/main.py
fi

echo "[HATA] Sistemde ne derlenmis binary (bin/linux/fieldops.bin) ne de python3 bulundu!"
exit 1

