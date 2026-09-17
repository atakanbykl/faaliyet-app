"""
FieldOps Assistant - Çekirdek Modül Testleri
"""

import json
import unittest
from pathlib import Path

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
    external_file.write_bytes(b"TEST CONTENT")

    registered = sm.register_external_package("loc_test", req, external_file, copy_to_storage=True)
    assert registered.exists()
    assert req.status == "found"

    # Yeniden arandığında bulunmalı
    found_now, path_now = sm.check_requirement("loc_test", req)
    assert found_now
    assert path_now.exists()


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

