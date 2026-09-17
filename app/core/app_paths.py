"""
FieldOps Assistant - Portable Path & Storage Resolver
Bu modül uygulamanın çalıştığı ortamı (USB, yerel disk, Windows, Linux) dinamik
olarak tespit eder ve sabit yol bağımlılıklarını ortadan kaldırır.
"""

from __future__ import annotations
import os
import sys
from pathlib import Path
from typing import List, Optional
import psutil


class AppPaths:
    """Uygulamanın çalıştırıldığı kök dizini ve veri klasörlerini dinamik yönetir."""

    @staticmethod
    def get_app_root() -> Path:
        """
        Uygulamanın kök dizinini bulur:
        - PyInstaller / Nuitka dondurulmuş (frozen) moddaysa binary'nin bulunduğu yer
        - Normal Python ortamında repo kök dizini
        """
        if getattr(sys, "frozen", False):
            # PyInstaller binary
            executable_path = Path(sys.executable).resolve()
            # Eğer /bin/windows/ veya /bin/linux/ altındaysa 2 üst dizine çıkarak USB kökünü bul
            if "bin" in executable_path.parts:
                root = executable_path.parents[2]
            else:
                root = executable_path.parent
            return root
        else:
            # Geliştirme ortamı: app_paths.py -> core -> app -> fieldops_assistant
            return Path(__file__).resolve().parents[2]

    @classmethod
    def get_data_dir(cls) -> Path:
        """Ortak veri klasörü yolu: [ROOT]/data"""
        data_dir = cls.get_app_root() / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir

    @classmethod
    def get_profiles_dir(cls) -> Path:
        """Lokasyon profilleri klasörü: [ROOT]/data/profiles"""
        d = cls.get_data_dir() / "profiles"
        d.mkdir(parents=True, exist_ok=True)
        return d

    @classmethod
    def get_packages_dir(cls) -> Path:
        """Lokasyona özel yedek yazılım paketleri: [ROOT]/data/packages"""
        d = cls.get_data_dir() / "packages"
        d.mkdir(parents=True, exist_ok=True)
        return d

    @classmethod
    def get_missions_dir(cls) -> Path:
        """Saha görev arşivleri ve çekilen loglar: [ROOT]/data/missions"""
        d = cls.get_data_dir() / "missions"
        d.mkdir(parents=True, exist_ok=True)
        return d

    @classmethod
    def get_temp_dir(cls) -> Path:
        """Geçici işlemler için klasör: [ROOT]/data/temp"""
        d = cls.get_data_dir() / "temp"
        d.mkdir(parents=True, exist_ok=True)
        return d

    @classmethod
    def is_running_from_usb(cls) -> bool:
        """Uygulamanın şu anda bir USB / Çıkarılabilir sürücüden çalışıp çalışmadığını belirler."""
        root = cls.get_app_root()
        root_str = str(root)
        try:
            for part in psutil.disk_partitions(all=False):
                if "removable" in part.opts.lower() or "cdrom" in part.opts.lower():
                    if root_str.startswith(part.mountpoint):
                        return True
                # Windows özelinde sürücü harfi kontrolü
                if sys.platform == "win32" and hasattr(part, "device"):
                    if part.device and root_str.upper().startswith(part.device.upper()):
                        if "removable" in part.opts.lower():
                            return True
        except Exception:
            pass
        return False

    @classmethod
    def detect_removable_drives(cls) -> List[Path]:
        """
        Sistemde takılı olan çıkarılabilir USB sürücüleri listeler.
        Uygulama yerel diske kopyalanıp çalıştırıldığında verileri USB'ye aktarmak için kullanılır.
        """
        removable_paths: List[Path] = []
        try:
            for part in psutil.disk_partitions(all=False):
                opts = part.opts.lower()
                mount = part.mountpoint
                if not mount:
                    continue

                # Windows
                if sys.platform == "win32":
                    if "removable" in opts:
                        removable_paths.append(Path(mount))
                    else:
                        # Drive type kontrolü yapılabilir (Drive type 2 = Removable)
                        try:
                            import ctypes
                            drive_type = ctypes.windll.kernel32.GetDriveTypeW(mount)
                            if drive_type == 2:  # DRIVE_REMOVABLE
                                removable_paths.append(Path(mount))
                        except Exception:
                            pass

                # Linux
                else:
                    if "removable" in opts or "/media/" in mount or "/run/media/" in mount or "/mnt/" in mount:
                        removable_paths.append(Path(mount))
        except Exception:
            pass

        # Tekrarları temizle
        unique_paths = []
        for p in removable_paths:
            if p not in unique_paths and p.exists():
                unique_paths.append(p)
        return unique_paths

    @classmethod
    def get_disk_free_gb(cls, path: Path) -> float:
        """Belirtilen yolun bulunduğu diskteki boş alanı GB cinsinden döner."""
        try:
            usage = psutil.disk_usage(str(path))
            return usage.free / (1024 ** 3)
        except Exception:
            return 0.0

