"""
FieldOps Assistant - Windows Tek Tıkla PyInstaller Paketleme Scripti
Çalıştırıldığında bin/windows/ altında kurulumsuz taşınabilir .exe üretir.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT_DIR / "bin" / "windows"


def build():
    print(f"[FieldOps Build] Proje kökü: {ROOT_DIR}")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    main_script = ROOT_DIR / "app" / "main.py"

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name", "fieldops",
        "--distpath", str(OUTPUT_DIR),
        "--workpath", str(ROOT_DIR / "build" / "pyinstaller_work"),
        "--specpath", str(ROOT_DIR / "build"),
        f"--paths={ROOT_DIR}",
        str(main_script)
    ]

    print("[FieldOps Build] PyInstaller çalıştırılıyor...")
    print(" ".join(cmd))
    res = subprocess.run(cmd)

    if res.returncode == 0:
        print(f"\n[FieldOps Build] BAŞARILI! Çıktı klasörü: {OUTPUT_DIR}")
    else:
        print(f"\n[FieldOps Build] HATA! Çıkış kodu: {res.returncode}")


if __name__ == "__main__":
    build()

