import sys
import os
import unittest
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, os.path.abspath("."))

from PySide6.QtWidgets import QApplication
from app.core.profile_manager import ProfileManager
from app.core.mission_context import MissionManager
from app.core.models import LocationProfile, TargetDeviceConfig
from app.adapters.local_adapter import LocalExecutionAdapter
from app.adapters.ssh_adapter import SSHExecutionAdapter
from app.gui.wizards.stage3_field_end import Stage3FieldEndWidget


class TestStage3ConnectionCard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            cls.app = QApplication(["--platform", "offscreen"])
        else:
            cls.app = QApplication.instance()

    def setUp(self):
        self.profile_mgr = ProfileManager()
        self.mission_mgr = MissionManager()
        self.widget = Stage3FieldEndWidget(self.profile_mgr, self.mission_mgr)

        self.sample_profile = LocationProfile(
            id="test_loc",
            name="Test Radar İstasyonu",
            target_device=TargetDeviceConfig(
                host="192.168.10.50",
                port=2222,
                username="operator",
                password="secret_password",
                key_path="",
                remote_config_path="/opt/app/config.json",
                remote_log_dir="/opt/app/logs"
            )
        )

    def test_ui_elements_exist(self):
        """Card 1 UI elemanları var olmalı."""
        self.assertTrue(hasattr(self.widget, "lbl_platform_detected"))
        self.assertTrue(hasattr(self.widget, "radio_ssh"))
        self.assertTrue(hasattr(self.widget, "radio_local"))
        self.assertTrue(hasattr(self.widget, "chk_custom_ssh"))
        self.assertTrue(hasattr(self.widget, "ssh_inputs_frame"))
        self.assertTrue(hasattr(self.widget, "txt_ssh_host"))
        self.assertTrue(hasattr(self.widget, "txt_ssh_port"))
        self.assertTrue(hasattr(self.widget, "txt_ssh_user"))
        self.assertTrue(hasattr(self.widget, "txt_ssh_pass"))
        self.assertTrue(hasattr(self.widget, "txt_ssh_key"))
        self.assertTrue(hasattr(self.widget, "btn_test_conn"))
        self.assertTrue(hasattr(self.widget, "lbl_conn_status"))
        self.assertTrue(hasattr(self.widget, "info_lbl"))
        self.assertFalse(self.widget.ssh_inputs_frame.isVisible())

    def test_load_session_with_local_adapter(self):
        """Stage 2'den gelen LocalExecutionAdapter devralınmalı ve doğrulanmış olmalı."""
        adapter = LocalExecutionAdapter()
        self.widget.load_session(self.sample_profile, adapter)

        self.assertTrue(self.widget.radio_local.isChecked())
        self.assertEqual(self.widget.lbl_conn_status.text(), "✓ Başarılı")
        self.assertIs(self.widget.adapter, adapter)
        self.assertIn("Test Radar İstasyonu", self.widget.info_lbl.text())
        self.assertIn("192.168.10.50", self.widget.info_lbl.text())

    def test_load_session_with_ssh_adapter_profile_config(self):
        """Stage 2'den gelen SSHExecutionAdapter (profil ayarlı) devralınmalı."""
        adapter = SSHExecutionAdapter(self.sample_profile.target_device)
        # Mock active transport
        class MockTransport:
            def is_active(self):
                return True
        class MockClient:
            def get_transport(self):
                return MockTransport()
        adapter._client = MockClient()

        self.widget.load_session(self.sample_profile, adapter)
        self.assertTrue(self.widget.radio_ssh.isChecked())
        self.assertFalse(self.widget.chk_custom_ssh.isChecked())
        self.assertEqual(self.widget.lbl_conn_status.text(), "✓ Başarılı")
        self.assertIs(self.widget.adapter, adapter)

    def test_load_session_with_ssh_adapter_custom_config(self):
        """Stage 2'den gelen özel SSH bilgileri otomatik algılanıp formda gösterilmeli."""
        custom_cfg = TargetDeviceConfig(
            host="10.0.0.99",
            port=2200,
            username="special_admin",
            password="custom_password",
            key_path="/path/to/key.pem"
        )
        adapter = SSHExecutionAdapter(custom_cfg)
        class MockTransport:
            def is_active(self):
                return True
        class MockClient:
            def get_transport(self):
                return MockTransport()
        adapter._client = MockClient()

        self.widget.load_session(self.sample_profile, adapter)
        self.assertTrue(self.widget.radio_ssh.isChecked())
        self.assertTrue(self.widget.chk_custom_ssh.isChecked())
        self.assertEqual(self.widget.txt_ssh_host.text(), "10.0.0.99")
        self.assertEqual(self.widget.txt_ssh_port.text(), "2200")
        self.assertEqual(self.widget.txt_ssh_user.text(), "special_admin")
        self.assertEqual(self.widget.txt_ssh_pass.text(), "custom_password")
        self.assertEqual(self.widget.txt_ssh_key.text(), "/path/to/key.pem")
        self.assertEqual(self.widget.lbl_conn_status.text(), "✓ Başarılı")

    def test_load_session_without_adapter(self):
        """Adaptör verilmeden oturum açıldığında platform varsayılanı seçilmeli ve Test Edilmedi olmalı."""
        self.widget.load_session(self.sample_profile, None)
        self.assertEqual(self.widget.lbl_conn_status.text(), "Test Edilmedi")
        self.assertIsNone(self.widget.adapter)

    def test_custom_ssh_fallback_to_plan(self):
        """chk_custom_ssh seçili değilse profile.target_device kullanılmalı, seçiliyse elle girilenler."""
        self.widget.load_session(self.sample_profile, None)
        self.widget.radio_ssh.setChecked(True)

        # 1. Unchecked -> plandaki config
        self.widget.chk_custom_ssh.setChecked(False)
        adapter = self.widget._get_active_adapter()
        self.assertIsInstance(adapter, SSHExecutionAdapter)
        self.assertEqual(adapter.config.host, "192.168.10.50")
        self.assertEqual(adapter.config.port, 2222)
        self.assertEqual(adapter.config.username, "operator")

        # 2. Checked -> elle girilen config
        self.widget.chk_custom_ssh.setChecked(True)
        self.widget.txt_ssh_host.setText("172.16.0.2")
        self.widget.txt_ssh_port.setText("22222")
        self.widget.txt_ssh_user.setText("custom_user")
        adapter_custom = self.widget._get_active_adapter()
        self.assertIsInstance(adapter_custom, SSHExecutionAdapter)
        self.assertEqual(adapter_custom.config.host, "172.16.0.2")
        self.assertEqual(adapter_custom.config.port, 22222)
        self.assertEqual(adapter_custom.config.username, "custom_user")

    def test_switching_mode_clears_verification(self):
        """Mod değiştirildiğinde veya SSH bilgisi değiştirildiğinde bağlantı durumu sıfırlanmalı."""
        local_adapter = LocalExecutionAdapter()
        self.widget.load_session(self.sample_profile, local_adapter)
        self.assertEqual(self.widget.lbl_conn_status.text(), "✓ Başarılı")

        # SSH'a geç
        self.widget.radio_ssh.setChecked(True)
        self.assertEqual(self.widget.lbl_conn_status.text(), "Test Edilmedi")
        self.assertIsNone(self.widget.adapter)

        # Yerel'e geri dön ve doğrula
        self.widget.radio_local.setChecked(True)
        self.assertEqual(self.widget.lbl_conn_status.text(), "Test Edilmedi")
        self.widget._test_connection()
        self.assertEqual(self.widget.lbl_conn_status.text(), "✓ Başarılı")
        self.assertIsInstance(self.widget.adapter, LocalExecutionAdapter)

    def test_readiness_requires_connection(self):
        """Bağlantı doğrulanmadığında readiness 'Cihaz bağlantısı doğrulanmadı' uyarısı vermeli."""
        self.widget.load_session(self.sample_profile, None)
        self.assertIn("Cihaz bağlantısı doğrulanmadı", self.widget.lbl_end_summary.text())
        self.assertFalse(self.widget.btn_finish_mission.isEnabled())

        # Force açıldığında eksiklere rağmen buton aktifleşmeli
        self.widget.chk_force_end.setChecked(True)
        self.assertTrue(self.widget.btn_finish_mission.isEnabled())
        self.assertIn("Force Aktif", self.widget.lbl_end_summary.text())


    def test_collect_logs_and_pull_config_guards(self):
        """Bağlantı doğrulanmadığında log çekme ve config çekme işlemi durdurulmalı."""
        from unittest.mock import patch
        self.widget.load_session(self.sample_profile, None)
        # lbl_conn_status is 'Test Edilmedi'
        with patch("PySide6.QtWidgets.QMessageBox.warning") as mock_warn:
            self.widget._pull_active_config()
            self.assertIn("Bağlantı doğrulanmadan konfigürasyon çekilemez", self.widget.console.text_edit.toPlainText())
            mock_warn.assert_called_once()

        with patch("PySide6.QtWidgets.QMessageBox.warning") as mock_warn:
            self.widget._collect_logs()
            self.assertIn("Bağlantı doğrulanmadan log toplanamaz", self.widget.console.text_edit.toPlainText())
            mock_warn.assert_called_once()

    def test_pull_active_config_with_local_adapter(self):
        """Yerel modda konfigürasyon çekilip diff durumu güncellenmeli."""
        import tempfile
        self.mission_mgr.start_new_session(self.sample_profile.id, "Operator")
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json", encoding="utf-8") as f:
            f.write('{"mode": "operational", "status": "active"}')
            temp_config = f.name

        try:
            self.sample_profile.target_device.remote_config_path = temp_config
            self.sample_profile.baseline_config_content = '{"mode": "operational", "status": "active"}'
            local_adapter = LocalExecutionAdapter()
            self.widget.load_session(self.sample_profile, local_adapter)

            self.widget._pull_active_config()
            self.assertEqual(self.widget.captured_config_text, '{"mode": "operational", "status": "active"}')
            self.assertTrue(self.widget.btn_open_diff.isEnabled())
            self.assertIn("birebir aynı", self.widget.lbl_diff_status.text())
        finally:
            if os.path.exists(temp_config):
                os.unlink(temp_config)


if __name__ == "__main__":
    unittest.main()
