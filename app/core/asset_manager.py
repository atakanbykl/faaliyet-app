"""
FieldOps Assistant - Yazılım Varlık ve Paket Yöneticisi
Lokasyona özel yedek yazılım paketlerinin otomatik taranması ve harici seçici entegrasyonu.
"""

from __future__ import annotations
import shutil
from pathlib import Path
from typing import List, Optional, Tuple

from app.core.app_paths import AppPaths
from app.core.models import LocationProfile, SoftwareRequirement


class SoftwareAssetManager:
    """Lokasyona ait yazılım paketlerini/binary'lerini yönetir."""

    def __init__(self, packages_dir: Optional[Path] = None):
        self.packages_dir = packages_dir or AppPaths.get_packages_dir()
        self.packages_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_sample_package()

    def check_requirement(self, location_id: str, req: SoftwareRequirement) -> Tuple[bool, Optional[Path]]:
        """
        Gereksinim duyulan paketi arar:
        1. [packages_dir]/[location_id]/[package_filename]
        2. [packages_dir]/[package_filename]
        Bulunursa (True, path), bulunamazsa (False, None) döner.
        """
        # 1. Lokasyona özel alt klasör
        loc_path = self.packages_dir / location_id / req.package_filename
        if loc_path.exists():
            req.resolved_package_path = str(loc_path)
            req.status = "found"
            return True, loc_path

        # 2. Genel packages klasörü
        gen_path = self.packages_dir / req.package_filename
        if gen_path.exists():
            req.resolved_package_path = str(gen_path)
            req.status = "found"
            return True, gen_path

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
        İstenirse USB/data dizinine kalıcı olarak kopyalar.
        """
        if not external_file_path.exists():
            raise FileNotFoundError(f"Seçilen dosya mevcut değil: {external_file_path}")

        if copy_to_storage:
            target_dir = self.packages_dir / location_id
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
        """Test amaçlı örnek bir sahte tar.gz paketi oluşturur."""
        ankara_pkg = self.packages_dir / "ankara_golbasi_01" / "radar_control_v2.4.0_x86_64.tar.gz"
        if not ankara_pkg.exists():
            ankara_pkg.parent.mkdir(parents=True, exist_ok=True)
            with open(ankara_pkg, "wb") as f:
                f.write(b"FieldOps Mock Release Package v2.4.0 x86_64\n" * 100)

