"""
FieldOps Assistant - Profil Yöneticisi
Lokasyon profillerinin YAML/JSON olarak okunması, yazılması ve güncellenmesi.
"""

from __future__ import annotations
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
import yaml

from app.core.app_paths import AppPaths
from app.core.models import EquipmentItem, LocationProfile, SoftwareRequirement, TargetDeviceConfig

logger = logging.getLogger(__name__)


class ProfileManager:
    """Lokasyon profilleri üzerinde CRUD ve senkronizasyon işlemlerini yürütür."""

    def __init__(self, profiles_dir: Optional[Path] = None):
        self.profiles_dir = profiles_dir or AppPaths.get_profiles_dir()
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_default_profiles()

    def list_profiles(self) -> List[LocationProfile]:
        """Tüm kayıtlı lokasyon profillerini yükler."""
        profiles = []
        for file_path in self.profiles_dir.glob("*.yaml"):
            try:
                prof = self.load_profile(file_path.stem)
                if prof:
                    profiles.append(prof)
            except Exception as e:
                logger.error(f"Profil okuma hatası ({file_path}): {e}")
        return profiles

    def load_profile(self, profile_id: str) -> Optional[LocationProfile]:
        """Belirtilen ID'ye sahip profili dosyadan yükler."""
        file_path = self.profiles_dir / f"{profile_id}.yaml"
        if not file_path.exists():
            return None

        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if not data:
                return None
            return LocationProfile.from_dict(data)

    def save_profile(self, profile: LocationProfile) -> Path:
        """Profili YAML olarak kaydeder."""
        file_path = self.profiles_dir / f"{profile.id}.yaml"
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(profile.to_dict(), f, allow_unicode=True, sort_keys=False, default_flow_style=False)
        return file_path

    def delete_profile(self, profile_id: str) -> bool:
        """Belirtilen profili diskten siler."""
        file_path = self.profiles_dir / f"{profile_id}.yaml"
        if file_path.exists():
            try:
                file_path.unlink()
                return True
            except Exception as e:
                logger.error(f"Profil silme hatası ({file_path}): {e}")
                return False
        return False

    def profile_exists(self, profile_id: str) -> bool:
        """Belirtilen profil ID'sinin diskte olup olmadığını kontrol eder."""
        return (self.profiles_dir / f"{profile_id}.yaml").exists()

    def update_baseline_config(self, profile_id: str, new_config_content: str) -> bool:
        """Sahadan dönen ve onaylanan konfigürasyonu ana referans profile aktarır."""
        prof = self.load_profile(profile_id)
        if not prof:
            return False
        prof.baseline_config_content = new_config_content
        self.save_profile(prof)
        return True

    def _ensure_default_profiles(self) -> None:
        """Klasör boşsa test ve örnek amaçlı 2 adet lokasyon profili oluşturur."""
        existing = list(self.profiles_dir.glob("*.yaml"))
        if existing:
            return

        # Örnek Profil 1: Ankara Gölbaşı İstasyonu
        ankara_config = json.dumps({
            "station_id": "ANK-GOLBASI-01",
            "log_level": "INFO",
            "telemetry_interval_sec": 5,
            "sensor_baudrate": 115200,
            "rf_frequency_mhz": 433.92,
            "max_buffer_size_mb": 500,
            "network": {
                "ip": "192.168.10.50",
                "gateway": "192.168.10.1",
                "port": 8080
            },
            "features": {
                "auto_backup": True,
                "high_accuracy_gps": True,
                "encryption_enabled": True
            }
        }, indent=2, ensure_ascii=False)

        ankara_profile = LocationProfile(
            id="ankara_golbasi_01",
            name="Ankara Gölbaşı Radar İstasyonu",
            description="Sabit radar ve telemetri istasyonu - Yüksek hızlı fiber bağlantı.",
            target_device=TargetDeviceConfig(
                host="192.168.10.50",
                port=22,
                username="operator",
                remote_log_dir="/opt/fieldapp/logs",
                remote_config_path="/opt/fieldapp/config/config.json",
            ),
            equipment_checklist=[
                EquipmentItem(id="eq_1", name="Yedek Ethernet CAT6 Kablosu (15m)", is_mandatory=True),
                EquipmentItem(id="eq_2", name="USB-RS232 Seri Port Dönüştürücü", is_mandatory=True),
                EquipmentItem(id="eq_3", name="Saha Multimetresi ve Probları", is_mandatory=False),
                EquipmentItem(id="eq_4", name="24V Saha Güç Adaptörü & Akü", is_mandatory=True),
                EquipmentItem(id="eq_5", name="Yansıtıcı Saha Yeleği & Baret", is_mandatory=True),
            ],
            software_requirements=[
                SoftwareRequirement(
                    name="RadarControlService",
                    expected_version="2.4.0",
                    package_filename="radar_control_v2.4.0_x86_64.tar.gz",
                    target_install_path="/opt/fieldapp",
                    service_name="radar_control",
                    version_command="/opt/fieldapp/bin/radar_control --version",
                )
            ],
            baseline_config_content=ankara_config,
            custom_notes="İstasyon jeneratörü faz-2 hattına bağlıdır. Yağışlı havalarda RF kutusunu açmayınız."
        )

        # Örnek Profil 2: İzmir Çeşme Mobil Saha
        izmir_config = json.dumps({
            "station_id": "IZM-CESME-MOBIL",
            "log_level": "DEBUG",
            "telemetry_interval_sec": 1,
            "sensor_baudrate": 9600,
            "rf_frequency_mhz": 868.0,
            "max_buffer_size_mb": 200,
            "network": {
                "ip": "192.168.1.150",
                "gateway": "192.168.1.1",
                "port": 9000
            },
            "features": {
                "auto_backup": False,
                "high_accuracy_gps": True,
                "encryption_enabled": True
            }
        }, indent=2, ensure_ascii=False)

        izmir_profile = LocationProfile(
            id="izmir_cesme_mobil",
            name="İzmir Çeşme Mobil Saha Aracı",
            description="Mobil araç üstü saha sistemi - 4G/LTE yönlendirici üzerinden haberleşme.",
            target_device=TargetDeviceConfig(
                host="192.168.1.150",
                port=22,
                username="fielduser",
                remote_log_dir="/var/log/fieldapp",
                remote_config_path="/etc/fieldapp/runtime.json",
            ),
            equipment_checklist=[
                EquipmentItem(id="eq_10", name="Manyetik Araç Üstü GPS Anteni", is_mandatory=True),
                EquipmentItem(id="eq_11", name="12V Araç Çakmaklık Güç Kablosu", is_mandatory=True),
                EquipmentItem(id="eq_12", name="4G Yedek SIM Kart", is_mandatory=True),
            ],
            software_requirements=[
                SoftwareRequirement(
                    name="MobileTrackerCore",
                    expected_version="1.8.2",
                    package_filename="mobile_tracker_v1.8.2_x86_64.tar.gz",
                    target_install_path="/opt/fieldapp",
                    service_name="mobile_tracker",
                    version_command="/opt/fieldapp/bin/mobile_tracker --version",
                )
            ],
            baseline_config_content=izmir_config,
            custom_notes="GSM sinyali zayıf bölgelerde yerel SD kart tamponunu aktif ediniz."
        )

        self.save_profile(ankara_profile)
        self.save_profile(izmir_profile)

