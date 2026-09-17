"""
FieldOps Assistant - Yazılım Varlık ve Paket Yöneticisi
softwares/<app_name>/<version>/ hiyerarşisinde paketlerin taranması,
boş versiyonların uyarı ile tespiti ve saha gereksinimlerinin karşılanması.
"""

from __future__ import annotations
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from app.core.app_paths import AppPaths
from app.core.models import LocationProfile, SoftwareRequirement, StoredSoftwareInfo


class SoftwareAssetManager:
    """softwares/ klasöründeki uygulama ve versiyon paketlerini yönetir."""

    KNOWN_EXTENSIONS = [
        ".tar.gz", ".tar.bz2", ".tar.xz", ".tar", ".tgz",
        ".pigz", ".zip", ".deb", ".rpm", ".bin", ".run", ".iso", ".sh"
    ]

    def __init__(self, packages_dir: Optional[Path] = None):
        self.packages_dir = packages_dir or AppPaths.get_softwares_dir()
        self.packages_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_sample_package()

    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Bayt cinsinden dosya boyutunu okunabilir formata dönüştürür (KB, MB, GB)."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

    @classmethod
    def detect_extension(cls, filename: str) -> str:
        """Dosya adından bilinen arşiv/paket uzantısını tespit eder."""
        name_lower = filename.lower()
        for ext in cls.KNOWN_EXTENSIONS:
            if name_lower.endswith(ext):
                return ext
        return Path(filename).suffix.lower()

    def scan_available_softwares(self) -> List[StoredSoftwareInfo]:
        """
        softwares/ dizinini tarar:
        - 1. seviye klasörler: Uygulama ismi (<app_name>)
        - 2. seviye klasörler: Versiyon ismi (<version_name>)
        Her bir versiyon klasörünü bir yazılım girdisi olarak listeler.
        Eğer klasör boşsa (veya sadece .gitkeep varsa) is_empty=True olarak işaretler.
        """
        items: List[StoredSoftwareInfo] = []
        if not self.packages_dir.exists():
            return items

        # 1. Seviye: Uygulama klasörleri
        for app_dir in sorted(self.packages_dir.iterdir()):
            if not app_dir.is_dir() or app_dir.name.startswith("."):
                continue

            app_name = app_dir.name
            version_subdirs = [d for d in app_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]

            if version_subdirs:
                # 2. Seviye: Versiyon klasörleri
                for v_dir in sorted(version_subdirs, key=lambda d: d.name, reverse=True):
                    version_name = v_dir.name
                    v_items = self._inspect_version_folder(app_name, version_name, v_dir)
                    items.append(v_items)
            else:
                # Versiyon alt klasörü yoksa doğrudan app_dir altındaki dosyaları incele
                v_items = self._inspect_version_folder(app_name, "varsayılan", app_dir)
                items.append(v_items)

        # 3. Kök dizinde doğrudan bırakılmış serbest dosyalar varsa onları da kaçırma
        root_loose_files = [
            f for f in self.packages_dir.iterdir()
            if f.is_file() and not f.name.startswith(".")
        ]
        for f in root_loose_files:
            stat = f.stat()
            size = stat.st_size
            ext = self.detect_extension(f.name)
            # Versiyon bilgisi dosya adından çıkarılabilir mi?
            v_match = re.search(r"v\d+[\.\d+]*", f.name)
            v_name = v_match.group(0) if v_match else "kök_dosya"
            base_app_name = f.name.replace(f"_{v_name}", "").replace(v_name, "").split(".")[0].strip("_-")

            items.append(
                StoredSoftwareInfo(
                    app_name=base_app_name or "kök_paket",
                    version_name=v_name,
                    folder_path=str(self.packages_dir),
                    relative_path=f.name,
                    is_empty=False,
                    files=[f.name],
                    file_count=1,
                    total_size_bytes=size,
                    formatted_size=self.format_file_size(size),
                    modified_time_str=datetime.fromtimestamp(stat.st_mtime).strftime("%d.%m.%Y %H:%M"),
                    primary_package=f.name,
                    extension=ext,
                )
            )

        # Uygulama adına göre sırala, aynı uygulama içinde yeni versiyonlar önce gelsin
        items.sort(key=lambda x: (x.app_name.lower(), not x.is_empty, x.version_name.lower()))
        return items

    def scan_softwares_grouped(self) -> dict[str, List[StoredSoftwareInfo]]:
        """
        softwares/ dizinini tarar ve sonuçları uygulama ismine göre gruplandırılmış sözlük olarak döner:
        {
            "radar_control": [v2.4.0 (Dolu), v2.5.0 (Boş)],
            "yardimci_araclar": [v1.0.0 (Dolu), v1.1.0 (Boş)]
        }
        """
        from collections import OrderedDict
        items = self.scan_available_softwares()
        grouped: OrderedDict[str, List[StoredSoftwareInfo]] = OrderedDict()
        for it in items:
            if it.app_name not in grouped:
                grouped[it.app_name] = []
            grouped[it.app_name].append(it)
        return dict(grouped)

    def _inspect_version_folder(self, app_name: str, version_name: str, folder: Path) -> StoredSoftwareInfo:
        """Belirtilen versiyon klasörünü inceler ve StoredSoftwareInfo nesnesi oluşturur."""
        rel_path = folder.relative_to(self.packages_dir)

        # İçindeki gizli olmayan tüm dosyaları topla (özyinelemeli)
        files: List[Path] = []
        try:
            for p in folder.rglob("*"):
                if p.is_file() and not p.name.startswith(".") and not any(part.startswith(".") for part in p.parts):
                    files.append(p)
        except Exception:
            pass

        if not files:
            # Klasör boş (veya sadece .gitkeep / gizli dosyalar var)
            try:
                mtime = folder.stat().st_mtime
                mtime_str = datetime.fromtimestamp(mtime).strftime("%d.%m.%Y %H:%M")
            except Exception:
                mtime_str = ""

            return StoredSoftwareInfo(
                app_name=app_name,
                version_name=version_name,
                folder_path=str(folder),
                relative_path=str(rel_path).replace("\\", "/"),
                is_empty=True,
                files=[],
                file_count=0,
                total_size_bytes=0,
                formatted_size="0 B",
                modified_time_str=mtime_str,
                primary_package=None,
                extension="",
            )

        # Klasör dolu
        total_size = sum(f.stat().st_size for f in files)
        latest_mtime = max(f.stat().st_mtime for f in files)
        mtime_str = datetime.fromtimestamp(latest_mtime).strftime("%d.%m.%Y %H:%M")

        # Birincil arşiv veya ikili dosyayı seç
        primary_pkg = None
        primary_ext = ""
        for f in files:
            ext = self.detect_extension(f.name)
            if ext in self.KNOWN_EXTENSIONS:
                primary_pkg = f.name
                primary_ext = ext
                break
        if not primary_pkg and files:
            primary_pkg = files[0].name
            primary_ext = self.detect_extension(files[0].name)

        return StoredSoftwareInfo(
            app_name=app_name,
            version_name=version_name,
            folder_path=str(folder),
            relative_path=str(rel_path).replace("\\", "/"),
            is_empty=False,
            files=[f.name for f in files],
            file_count=len(files),
            total_size_bytes=total_size,
            formatted_size=self.format_file_size(total_size),
            modified_time_str=mtime_str,
            primary_package=primary_pkg,
            extension=primary_ext,
        )

    def check_requirement(self, location_id: str, req: SoftwareRequirement) -> Tuple[bool, Optional[Path]]:
        """
        Gereksinim duyulan paketi arar:
        1. [softwares_dir]/<app>/<version>/[package_filename] veya alt klasörlerde özyinelemeli arama
        2. Geriye dönük uyumluluk: data/packages/[location_id]/[package_filename]
        Bulunursa (True, path), bulunamazsa (False, None) döner.
        """
        # 1. softwares klasöründe özyinelemeli arama
        for match in self.packages_dir.rglob(req.package_filename):
            if match.is_file() and not match.name.startswith("."):
                req.resolved_package_path = str(match)
                req.status = "found"
                return True, match

        # 2. Geriye dönük uyumluluk: data/packages
        legacy_data_dir = AppPaths.get_data_dir() / "packages"
        if legacy_data_dir.exists():
            for match in legacy_data_dir.rglob(req.package_filename):
                if match.is_file() and not match.name.startswith("."):
                    req.resolved_package_path = str(match)
                    req.status = "found"
                    return True, match

        req.resolved_package_path = None
        req.status = "missing"
        return False, None

    def register_external_package(
        self,
        location_id: str,
        req: SoftwareRequirement,
        external_file_path: Path,
        copy_to_storage: bool = True
    ) -> Path:
        """
        Kullanıcının harici olarak gösterdiği bir paketi kaydeder.
        İstenirse softwares/<app>/<version>/ dizinine kalıcı olarak kopyalar.
        """
        if not external_file_path.exists():
            raise FileNotFoundError(f"Seçilen dosya mevcut değil: {external_file_path}")

        if copy_to_storage:
            app_name = req.service_name or req.name.lower().replace(" ", "_")
            version_str = f"v{req.expected_version}" if not req.expected_version.startswith("v") else req.expected_version
            target_dir = self.packages_dir / app_name / version_str
            target_dir.mkdir(parents=True, exist_ok=True)
            target_file = target_dir / req.package_filename
            shutil.copy2(external_file_path, target_file)
            req.resolved_package_path = str(target_file)
            req.status = "found"
            return target_file
        else:
            req.resolved_package_path = str(external_file_path)
            req.status = "external_selected"
            return external_file_path

    def _ensure_sample_package(self) -> None:
        """Test ve ilk kullanım amaçlı örnek yazılım ve versiyon hiyerarşisi oluşturur."""
        # 1. Ana yazılım: radar_control v2.4.0 (Dolu) ve v2.5.0 (Boş / Uyarı)
        radar_v24 = self.packages_dir / "radar_control" / "v2.4.0"
        radar_v24.mkdir(parents=True, exist_ok=True)
        radar_pkg = radar_v24 / "radar_control_v2.4.0_x86_64.tar.gz"
        if not radar_pkg.exists():
            # Eski konumlardan kopyalamayı dene
            old_pkg = self.packages_dir / "ankara_golbasi_01" / "radar_control_v2.4.0_x86_64.tar.gz"
            legacy_sample = AppPaths.get_data_dir() / "packages" / "ankara_golbasi_01" / "radar_control_v2.4.0_x86_64.tar.gz"
            if old_pkg.exists():
                shutil.copy2(old_pkg, radar_pkg)
            elif legacy_sample.exists():
                shutil.copy2(legacy_sample, radar_pkg)
            else:
                with open(radar_pkg, "wb") as f:
                    f.write(b"FieldOps Mock Release Package v2.4.0 x86_64\n" * 100)

        # radar_control v2.5.0 (Boş sürüm)
        radar_v25 = self.packages_dir / "radar_control" / "v2.5.0"
        radar_v25.mkdir(parents=True, exist_ok=True)
        v25_keep = radar_v25 / ".gitkeep"
        if not v25_keep.exists():
            v25_keep.write_text("# Empty version directory\n", encoding="utf-8")

        # 2. Yardımcı yazılımlar: yardimci_araclar v1.0.0 (Dolu) ve v1.1.0 (Boş)
        yardimci_v10 = self.packages_dir / "yardimci_araclar" / "v1.0.0"
        yardimci_v10.mkdir(parents=True, exist_ok=True)
        yardimci_pkg = yardimci_v10 / "saha_diagnostik_v1.0.0.tar.gz"
        if not yardimci_pkg.exists():
            with open(yardimci_pkg, "wb") as f:
                f.write(b"FieldOps Diagnostic Tool v1.0.0\n" * 50)

        yardimci_v11 = self.packages_dir / "yardimci_araclar" / "v1.1.0"
        yardimci_v11.mkdir(parents=True, exist_ok=True)
        v11_keep = yardimci_v11 / ".gitkeep"
        if not v11_keep.exists():
            v11_keep.write_text("# Empty version directory\n", encoding="utf-8")
