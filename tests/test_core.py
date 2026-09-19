"""
FieldOps Assistant - Çekirdek Modül Testleri
"""

import json
import sys
import unittest
from pathlib import Path

# Proje kökünü sys.path'e ekle
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.app_paths import AppPaths
from app.core.asset_manager import SoftwareAssetManager
from app.core.diff_engine import ConfigDiffEngine
from app.core.models import LocationProfile, SoftwareRequirement, TargetDeviceConfig
from app.core.profile_manager import ProfileManager
from app.adapters.local_adapter import LocalExecutionAdapter


def test_app_paths(tmp_path):
    root = AppPaths.get_app_root()
    assert root.exists()
    assert (root / "app").exists()

    data_dir = AppPaths.get_data_dir()
    assert data_dir.exists()

    softwares_dir = AppPaths.get_softwares_dir()
    assert softwares_dir.exists()
    assert AppPaths.get_packages_dir() == softwares_dir


def test_profile_manager(tmp_path):
    pm = ProfileManager(profiles_dir=tmp_path)
    profiles = pm.list_profiles()
    # Otomatik en az 2 varsayılan profil üretmeli
    assert len(profiles) >= 2

    test_prof = profiles[0]
    loaded = pm.load_profile(test_prof.id)
    assert loaded is not None
    assert loaded.id == test_prof.id

    # Baseline config güncelleme testi
    new_cfg = json.dumps({"test_key": "updated_val"})
    assert pm.update_baseline_config(test_prof.id, new_cfg)
    reloaded = pm.load_profile(test_prof.id)
    assert "updated_val" in reloaded.baseline_config_content

    # profile_exists ve delete_profile testleri
    assert pm.profile_exists(test_prof.id)
    assert not pm.profile_exists("non_existent_profile_xyz")

    # Yeni profil kaydetme ve silme
    custom_prof = LocationProfile(
        id="custom_test_loc",
        name="Custom Test Lokasyonu"
    )
    pm.save_profile(custom_prof)
    assert pm.profile_exists("custom_test_loc")
    assert pm.delete_profile("custom_test_loc")
    assert not pm.profile_exists("custom_test_loc")


def test_software_asset_manager(tmp_path):
    sm = SoftwareAssetManager(packages_dir=tmp_path)
    req = SoftwareRequirement(
        name="TestApp",
        expected_version="1.0.0",
        package_filename="test_app_v1.0.0.tar.gz"
    )

    # Başlangıçta eksik olmalı
    found, path = sm.check_requirement("loc_test", req)
    assert not found
    assert req.status == "missing"

    # Harici paket simülasyonu
    external_file = tmp_path / "external_test_app.tar.gz"
    external_file.write_bytes(b"TEST CONTENT" * 50)

    registered = sm.register_external_package("loc_test", req, external_file, copy_to_storage=True)
    assert registered.exists()
    assert req.status == "found"

    # Yeniden arandığında bulunmalı
    found_now, path_now = sm.check_requirement("loc_test", req)
    assert found_now
    assert path_now.exists()

    # scan_available_softwares testi
    softwares = sm.scan_available_softwares()
    assert len(softwares) >= 1
    found_item = next((s for s in softwares if s.primary_package == "test_app_v1.0.0.tar.gz"), None)
    assert found_item is not None
    assert found_item.version_name == "v1.0.0"
    assert not found_item.is_empty
    assert "B" in found_item.formatted_size or "KB" in found_item.formatted_size
    assert found_item.extension == ".tar.gz"

    # Boş versiyon klasörü testi (Uyarı bayrağı kontrolü)
    empty_v_dir = tmp_path / "main_app" / "v2.0.0"
    empty_v_dir.mkdir(parents=True, exist_ok=True)
    (empty_v_dir / ".gitkeep").write_text("# gitkeep only\n")

    softwares_after = sm.scan_available_softwares()
    empty_item = next((s for s in softwares_after if s.version_name == "v2.0.0"), None)
    assert empty_item is not None
    assert empty_item.is_empty
    assert empty_item.file_count == 0
    assert empty_item.formatted_size == "0 B"

    # Gruplandırılmış tarama testi (Uygulama bazlı ağaç yapısı)
    grouped = sm.scan_softwares_grouped()
    assert "main_app" in grouped
    assert len(grouped["main_app"]) == 2  # v1.0.0 (dolu) ve v2.0.0 (boş)

    # Boyut biçimlendirme testi
    assert sm.format_file_size(500) == "500 B"
    assert sm.format_file_size(2048) == "2.0 KB"
    assert sm.format_file_size(1024 * 1024 * 5) == "5.0 MB"


def test_config_diff_engine():
    baseline = json.dumps({"baudrate": 9600, "timeout": 5}, indent=2)
    field_same = json.dumps({"baudrate": 9600, "timeout": 5}, indent=2)
    field_diff = json.dumps({"baudrate": 115200, "timeout": 10, "new_param": True}, indent=2)

    # Birebir aynı durum
    lines_same, has_diff_same = ConfigDiffEngine.compare_configs(baseline, field_same)
    assert not has_diff_same

    # Farklı durum
    lines_diff, has_diff = ConfigDiffEngine.compare_configs(baseline, field_diff)
    assert has_diff
    assert any(l.change_type == "replace" for l in lines_diff)
    assert any(l.change_type == "insert" for l in lines_diff)


def test_local_adapter_compression(tmp_path):
    adapter = LocalExecutionAdapter()

    # Sahte log klasörü oluştur
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    (log_dir / "system.log").write_text("Log line 1\nLog line 2\n" * 100)

    archive_dest = tmp_path / "output_archive.tar.gz"

    success, sha = adapter.compress_logs(str(log_dir), str(archive_dest))
    assert success
    assert archive_dest.exists()
    assert len(sha) == 64  # SHA-256 hash uzunluğu


def test_mission_manager_saved_sessions(tmp_path):
    from app.core.mission_context import MissionManager
    mm = MissionManager(missions_dir=tmp_path)

    # 1. Yeni oturum başlat
    session = mm.start_new_session("loc_ankara", "Ahmet Mühendis")
    assert session.current_stage == 1
    assert session.session_id.startswith("gorev_")

    # 2. İkinci aşamaya geç
    mm.set_current_stage(2)
    assert session.stage1_completed
    assert session.current_stage == 2

    # 3. Kayıtlı oturumları tara
    saved = mm.list_saved_sessions()
    assert len(saved) >= 1
    assert saved[0].session_id == session.session_id
    assert saved[0].current_stage == 2

    # 4. Yeniden oturumu diskten yükle
    loaded = mm.load_session(session.session_id)
    assert loaded is not None
    assert loaded.operator_name == "Ahmet Mühendis"
    assert loaded.current_stage == 2
    assert loaded.stage1_completed


def test_equipment_catalog_manager(tmp_path):
    from app.core.equipment_manager import EquipmentCatalogManager
    from app.core.models import EquipmentItem

    catalog_file = tmp_path / "equipment_catalog.json"
    em = EquipmentCatalogManager(catalog_file=catalog_file)

    # 1. Varsayılan ekipmanlar yüklenmiş olmalı
    items = em.get_items()
    assert len(items) >= 5
    assert catalog_file.exists()

    # 2. Arama ve filtreleme
    search_res = em.get_items(search_query="ethernet")
    assert len(search_res) >= 1
    assert "ethernet" in search_res[0].name.lower()

    # 3. Yeni ekipman ekleme
    assert em.add_item("Özel Test Multimetresi", "Kalibre edilmiş cihaz", category="Donanım & Test")
    found = [it for it in em.get_items() if it.name == "Özel Test Multimetresi"]
    assert len(found) == 1
    assert found[0].description == "Kalibre edilmiş cihaz"

    # 4. Ekipman silme
    assert em.remove_item("Özel Test Multimetresi")
    assert not any(it.name == "Özel Test Multimetresi" for it in em.get_items())

    # 5. register_items (elle girilenleri havuza otomatik kaydetme)
    manual_items = [
        EquipmentItem(id="eq_new1", name="Saha Termal Kamerası", description="FLIR E4", is_mandatory=True),
        EquipmentItem(id="eq_new2", name="Fiber Optik Temizleme Çubuğu", description="", is_mandatory=False),
    ]
    em.register_items(manual_items)
    assert any(it.name == "Saha Termal Kamerası" for it in em.get_items())
    assert any(it.name == "Fiber Optik Temizleme Çubuğu" for it in em.get_items())

    # 6. Yeni instance yüklediğinde kalıcı olduğunu teyit etme
    em2 = EquipmentCatalogManager(catalog_file=catalog_file)
    assert any(it.name == "Saha Termal Kamerası" for it in em2.get_items())


if __name__ == "__main__":
    import tempfile
    test_functions = [
        test_app_paths,
        test_profile_manager,
        test_software_asset_manager,
        test_config_diff_engine,
        test_local_adapter_compression,
        test_mission_manager_saved_sessions,
        test_equipment_catalog_manager,
    ]
    for fn in test_functions:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            if "tmp_path" in fn.__code__.co_varnames:
                fn(p)
            else:
                fn()
            print(f"[OK] {fn.__name__} passed")
    print("All core tests passed successfully!")


