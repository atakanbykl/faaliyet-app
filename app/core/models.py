"""
FieldOps Assistant - Veri Modelleri
Lokasyon profilleri, kontrol listeleri, yazılım paketleri ve görev oturumu modelleri.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any


@dataclass
class EquipmentItem:
    """Saha görevine götürülmesi gereken fiziksel ekipman."""
    id: str
    name: str
    description: str = ""
    is_mandatory: bool = True
    is_checked: bool = False


@dataclass
class SoftwareRequirement:
    """Hedef cihaza kurulacak/kontrol edilecek yazılım paketi."""
    name: str
    expected_version: str
    package_filename: str                     # Örn: main_app_v2.1_x86_64.tar.gz
    target_install_path: str = "/opt/app"    # Hedef Linux dizini
    service_name: Optional[str] = "main_app"  # systemd servis adı
    version_command: str = "/opt/app/bin/app --version"
    resolved_package_path: Optional[str] = None # Diskte bulunan veya kullanıcının seçtiği tam yol
    status: str = "pending"                  # "found", "missing", "external_selected"


@dataclass
class StoredSoftwareInfo:
    """softwares/<app_name>/<version>/ hiyerarşisinde tespit edilen yazılım sürümü metaverisi."""
    app_name: str                                  # Uygulama adı (örn: radar_control, yardimci_araclar)
    version_name: str                              # Versiyon adı (örn: v2.4.0, v2.5.0)
    folder_path: str                               # Versiyon klasörünün mutlak yolu
    relative_path: str                             # Örn: radar_control/v2.4.0
    is_empty: bool                                 # Klasör boşsa veya sadece .gitkeep varsa True
    files: List[str] = field(default_factory=list) # İçindeki paket/dosya isimleri
    file_count: int = 0                            # Dosya sayısı
    total_size_bytes: int = 0                      # Toplam boyut
    formatted_size: str = "0 B"                    # Okunabilir boyut
    modified_time_str: str = ""                    # Son değiştirilme zamanı
    primary_package: Optional[str] = None          # İlk/ana arşiv dosyası (örn: radar_control_v2.4.0_x86_64.tar.gz)
    extension: str = ""                            # Ana paket uzantısı (.tar.gz vb.)
    location_id: Optional[str] = None              # Varsa eşleşen lokasyon kimliği


@dataclass
class TargetDeviceConfig:
    """Hedef saha cihazı bağlantı parametreleri."""
    host: str = "192.168.1.100"
    port: int = 22
    username: str = "root"
    password: Optional[str] = None
    key_path: Optional[str] = None
    use_local_mode: bool = False             # True ise Linux üzerinde doğrudan yerel komutlar çalışır
    remote_log_dir: str = "/opt/app/logs"
    remote_config_path: str = "/opt/app/config/app_config.json"


@dataclass
class LocationProfile:
    """Saha lokasyonuna özel tüm konfigürasyon ve gereksinimleri barındıran profil."""
    id: str
    name: str
    description: str = ""
    target_device: TargetDeviceConfig = field(default_factory=TargetDeviceConfig)
    equipment_checklist: List[EquipmentItem] = field(default_factory=list)
    software_requirements: List[SoftwareRequirement] = field(default_factory=list)
    # Lokasyona ait referans konfigürasyon içeriği (JSON/YAML metni veya dict)
    baseline_config_content: str = "{}"
    custom_notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Profili serileştirilebilir sözlüğe dönüştürür."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "target_device": {
                "host": self.target_device.host,
                "port": self.target_device.port,
                "username": self.target_device.username,
                "password": self.target_device.password,
                "key_path": self.target_device.key_path,
                "use_local_mode": self.target_device.use_local_mode,
                "remote_log_dir": self.target_device.remote_log_dir,
                "remote_config_path": self.target_device.remote_config_path,
            },
            "equipment_checklist": [
                {
                    "id": item.id,
                    "name": item.name,
                    "description": item.description,
                    "is_mandatory": item.is_mandatory,
                }
                for item in self.equipment_checklist
            ],
            "software_requirements": [
                {
                    "name": sw.name,
                    "expected_version": sw.expected_version,
                    "package_filename": sw.package_filename,
                    "target_install_path": sw.target_install_path,
                    "service_name": sw.service_name,
                    "version_command": sw.version_command,
                }
                for sw in self.software_requirements
            ],
            "baseline_config_content": self.baseline_config_content,
            "custom_notes": self.custom_notes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> LocationProfile:
        """Sözlükten profil nesnesi oluşturur."""
        td_data = data.get("target_device", {})
        target_device = TargetDeviceConfig(
            host=td_data.get("host", "192.168.1.100"),
            port=td_data.get("port", 22),
            username=td_data.get("username", "root"),
            password=td_data.get("password"),
            key_path=td_data.get("key_path"),
            use_local_mode=td_data.get("use_local_mode", False),
            remote_log_dir=td_data.get("remote_log_dir", "/opt/app/logs"),
            remote_config_path=td_data.get("remote_config_path", "/opt/app/config/app_config.json"),
        )

        equipments = [
            EquipmentItem(
                id=item.get("id", ""),
                name=item.get("name", ""),
                description=item.get("description", ""),
                is_mandatory=item.get("is_mandatory", True),
            )
            for item in data.get("equipment_checklist", [])
        ]

        software_reqs = [
            SoftwareRequirement(
                name=sw.get("name", ""),
                expected_version=sw.get("expected_version", "1.0.0"),
                package_filename=sw.get("package_filename", ""),
                target_install_path=sw.get("target_install_path", "/opt/app"),
                service_name=sw.get("service_name", "main_app"),
                version_command=sw.get("version_command", "/opt/app/bin/app --version"),
            )
            for sw in data.get("software_requirements", [])
        ]

        return cls(
            id=data.get("id", "default_loc"),
            name=data.get("name", "Varsayılan Lokasyon"),
            description=data.get("description", ""),
            target_device=target_device,
            equipment_checklist=equipments,
            software_requirements=software_reqs,
            baseline_config_content=data.get("baseline_config_content", "{}"),
            custom_notes=data.get("custom_notes", ""),
        )


@dataclass
class MissionSession:
    """Tek bir saha operasyonunun canlı durumu ve kayıtları."""
    session_id: str
    location_id: str
    operator_name: str
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    current_stage: int = 1                  # 1: Ön Kontrol, 2: Faaliyet Başlangıcı, 3: Faaliyet Sonu
    stage1_completed: bool = False
    stage2_completed: bool = False
    stage3_completed: bool = False
    downloaded_logs_path: Optional[str] = None
    captured_config_path: Optional[str] = None
    logs_checksum_sha256: Optional[str] = None
    has_config_drift: bool = False
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "location_id": self.location_id,
            "operator_name": self.operator_name,
            "created_at": self.created_at,
            "current_stage": self.current_stage,
            "stage1_completed": self.stage1_completed,
            "stage2_completed": self.stage2_completed,
            "stage3_completed": self.stage3_completed,
            "downloaded_logs_path": self.downloaded_logs_path,
            "captured_config_path": self.captured_config_path,
            "logs_checksum_sha256": self.logs_checksum_sha256,
            "has_config_drift": self.has_config_drift,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MissionSession:
        return cls(
            session_id=data.get("session_id", ""),
            location_id=data.get("location_id", ""),
            operator_name=data.get("operator_name", "Saha_Operatoru"),
            created_at=data.get("created_at", ""),
            current_stage=data.get("current_stage", 1),
            stage1_completed=data.get("stage1_completed", False),
            stage2_completed=data.get("stage2_completed", False),
            stage3_completed=data.get("stage3_completed", False),
            downloaded_logs_path=data.get("downloaded_logs_path"),
            captured_config_path=data.get("captured_config_path"),
            logs_checksum_sha256=data.get("logs_checksum_sha256"),
            has_config_drift=data.get("has_config_drift", False),
            notes=data.get("notes", []),
        )


