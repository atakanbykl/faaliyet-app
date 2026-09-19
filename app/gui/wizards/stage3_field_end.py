"""
FieldOps Assistant - 3. Aşama: Faaliyet Sonu & Log Toplama (Stage 3: Field Wrap-up)
Modern kart mimarisi, 20-30GB log sıkıştırma ve çekme, görsel diff kıyaslama ve USB aktarımı.
"""

from __future__ import annotations
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QMessageBox, QScrollArea, QProgressBar, QCheckBox,
    QRadioButton, QButtonGroup, QLineEdit, QFileDialog
)

from app.adapters.base_adapter import BaseExecutionAdapter
from app.adapters.local_adapter import LocalExecutionAdapter
from app.adapters.ssh_adapter import SSHExecutionAdapter
from app.core.app_paths import AppPaths
from app.core.diff_engine import ConfigDiffEngine
from app.core.mission_context import MissionManager
from app.core.models import EquipmentItem, LocationProfile, TargetDeviceConfig
from app.core.profile_manager import ProfileManager
from app.gui.widgets.checklist_widget import ChecklistWidget
from app.gui.widgets.diff_dialog import ConfigDiffDialog
from app.gui.widgets.live_console import LiveConsoleWidget
from app.gui.widgets.touch_button import TouchButton


class Stage3FieldEndWidget(QWidget):
    """3. Aşama Ekranı: Faaliyet sonu, büyük log toplama ve konfigürasyon inceleme."""
    mission_finished = Signal()

    def __init__(
        self,
        profile_manager: ProfileManager,
        mission_manager: MissionManager,
        parent=None
    ):
        super().__init__(parent)
        self.profile_manager = profile_manager
        self.mission_manager = mission_manager
        self.profile: Optional[LocationProfile] = None
        self.adapter: Optional[BaseExecutionAdapter] = None
        self.captured_config_text: Optional[str] = None
        self._usb_synced: bool = False

        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(16)

        # Üst Başlık Kartı
        header = QFrame()
        header.setProperty("class", "ModernCard")
        h_layout = QVBoxLayout(header)
        h_layout.setSpacing(4)

        title = QLabel("3. AŞAMA: Faaliyet Sonu & Log Arşivleme")
        title.setProperty("class", "SectionTitle")
        h_layout.addWidget(title)

        desc = QLabel("Faaliyet tamamlandığında büyük loglar toplanır, konfigürasyon farkları incelenir ve veriler USB'ye aktarılır.")
        desc.setProperty("class", "SectionSubtitle")
        h_layout.addWidget(desc)

        self.info_lbl = QLabel()
        self.info_lbl.setStyleSheet("color: #60a5fa; font-weight: 600; font-size: 13px; margin-top: 4px;")
        h_layout.addWidget(self.info_lbl)
        main_layout.addWidget(header)

        # İki Kolonlu İçerik
        content_layout = QHBoxLayout()
        content_layout.setSpacing(18)

        # Sol Kolon (Adımlar)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        left_container = QWidget()
        l_layout = QVBoxLayout(left_container)
        l_layout.setContentsMargins(0, 0, 4, 0)
        l_layout.setSpacing(16)

        # 1. KART: Cihaz Bağlantı Modu & Doğrulama
        conn_card = QFrame()
        conn_card.setProperty("class", "ModernCard")
        c_box = QVBoxLayout(conn_card)
        c_box.setSpacing(12)

        mode_header = QHBoxLayout()
        lbl_s1 = QLabel("🔌 1. Cihaz Bağlantı Modu")
        lbl_s1.setStyleSheet("font-size: 15px; font-weight: 700; color: #f8fafc;")
        mode_header.addWidget(lbl_s1)
        mode_header.addStretch()

        self.lbl_platform_detected = QLabel()
        self.lbl_platform_detected.setProperty("class", "PillBadge")
        mode_header.addWidget(self.lbl_platform_detected)
        c_box.addLayout(mode_header)

        mode_row = QHBoxLayout()
        self.mode_group = QButtonGroup(self)
        self.radio_ssh = QRadioButton("🌐 Uzak SSH (Windows Destek Bilgisayarı)")
        self.radio_local = QRadioButton("⚡ Doğrudan Yerel (Linux Saha Cihazı)")
        self.mode_group.addButton(self.radio_ssh)
        self.mode_group.addButton(self.radio_local)

        self.radio_ssh.toggled.connect(self._on_connection_mode_changed)
        self.radio_local.toggled.connect(self._on_connection_mode_changed)

        mode_row.addWidget(self.radio_ssh)
        mode_row.addWidget(self.radio_local)
        c_box.addLayout(mode_row)

        self.lbl_mode_hint = QLabel()
        self.lbl_mode_hint.setStyleSheet("color: #94a3b8; font-size: 12px; line-height: 1.3;")
        self.lbl_mode_hint.setWordWrap(True)
        c_box.addWidget(self.lbl_mode_hint)

        # SSH Manuel Bilgi Girişi Paneli
        self.ssh_custom_container = QWidget()
        ssh_custom_layout = QVBoxLayout(self.ssh_custom_container)
        ssh_custom_layout.setContentsMargins(0, 2, 0, 2)
        ssh_custom_layout.setSpacing(8)

        self.chk_custom_ssh = QCheckBox("SSH Bilgilerini Elle Gir (Özel IP / Kullanıcı / Şifre)")
        self.chk_custom_ssh.setStyleSheet("color: #cbd5e1; font-size: 13px; font-weight: 500;")
        self.chk_custom_ssh.toggled.connect(self._on_custom_ssh_toggled)
        ssh_custom_layout.addWidget(self.chk_custom_ssh)

        self.ssh_inputs_frame = QFrame()
        self.ssh_inputs_frame.setStyleSheet("""
            QFrame {
                background-color: #0b1120;
                border: 1px solid #1e293b;
                border-radius: 10px;
            }
        """)
        ssh_form_layout = QVBoxLayout(self.ssh_inputs_frame)
        ssh_form_layout.setContentsMargins(14, 12, 14, 12)
        ssh_form_layout.setSpacing(10)

        # 1. Satır: Host, Port, Kullanıcı
        row1 = QHBoxLayout()
        row1.setSpacing(10)

        host_col = QVBoxLayout()
        host_col.setSpacing(4)
        lbl_h = QLabel("Hedef IP / Host:")
        lbl_h.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 600;")
        self.txt_ssh_host = QLineEdit()
        self.txt_ssh_host.setPlaceholderText("192.168.1.100")
        self.txt_ssh_host.setFixedHeight(34)
        self.txt_ssh_host.textChanged.connect(self._on_ssh_credentials_changed)
        host_col.addWidget(lbl_h)
        host_col.addWidget(self.txt_ssh_host)
        row1.addLayout(host_col, 5)

        port_col = QVBoxLayout()
        port_col.setSpacing(4)
        lbl_p = QLabel("Port:")
        lbl_p.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 600;")
        self.txt_ssh_port = QLineEdit("22")
        self.txt_ssh_port.setPlaceholderText("22")
        self.txt_ssh_port.setFixedHeight(34)
        self.txt_ssh_port.textChanged.connect(self._on_ssh_credentials_changed)
        port_col.addWidget(lbl_p)
        port_col.addWidget(self.txt_ssh_port)
        row1.addLayout(port_col, 2)

        user_col = QVBoxLayout()
        user_col.setSpacing(4)
        lbl_u = QLabel("Kullanıcı Adı:")
        lbl_u.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 600;")
        self.txt_ssh_user = QLineEdit("root")
        self.txt_ssh_user.setPlaceholderText("root")
        self.txt_ssh_user.setFixedHeight(34)
        self.txt_ssh_user.textChanged.connect(self._on_ssh_credentials_changed)
        user_col.addWidget(lbl_u)
        user_col.addWidget(self.txt_ssh_user)
        row1.addLayout(user_col, 4)
        ssh_form_layout.addLayout(row1)

        # 2. Satır: Parola, SSH Key
        row2 = QHBoxLayout()
        row2.setSpacing(10)

        pass_col = QVBoxLayout()
        pass_col.setSpacing(4)
        lbl_pwd = QLabel("Parola (Opsiyonel):")
        lbl_pwd.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 600;")
        self.txt_ssh_pass = QLineEdit()
        self.txt_ssh_pass.setEchoMode(QLineEdit.Password)
        self.txt_ssh_pass.setPlaceholderText("SSH parolası...")
        self.txt_ssh_pass.setFixedHeight(34)
        self.txt_ssh_pass.textChanged.connect(self._on_ssh_credentials_changed)
        pass_col.addWidget(lbl_pwd)
        pass_col.addWidget(self.txt_ssh_pass)
        row2.addLayout(pass_col, 4)

        key_col = QVBoxLayout()
        key_col.setSpacing(4)
        lbl_k = QLabel("SSH Anahtar Dosyası (Opsiyonel):")
        lbl_k.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 600;")
        key_row = QHBoxLayout()
        key_row.setSpacing(6)
        self.txt_ssh_key = QLineEdit()
        self.txt_ssh_key.setPlaceholderText("id_rsa, key.pem yolu...")
        self.txt_ssh_key.setFixedHeight(34)
        self.txt_ssh_key.textChanged.connect(self._on_ssh_credentials_changed)
        btn_browse_key = TouchButton("Seç...", variant="ghost")
        btn_browse_key.setFixedHeight(34)
        btn_browse_key.setStyleSheet("font-size: 12px; padding: 2px 12px; min-height: 32px;")
        btn_browse_key.clicked.connect(self._browse_ssh_key)
        key_row.addWidget(self.txt_ssh_key)
        key_row.addWidget(btn_browse_key)
        key_col.addWidget(lbl_k)
        key_col.addLayout(key_row)
        row2.addLayout(key_col, 6)
        ssh_form_layout.addLayout(row2)

        lbl_custom_hint = QLabel("💡 Bu kutucuk işaretlenmediğinde plandaki tanımlı cihaz ayarlarıyla otomatik bağlanılır.")
        lbl_custom_hint.setStyleSheet("color: #64748b; font-size: 11px;")
        lbl_custom_hint.setWordWrap(True)
        ssh_form_layout.addWidget(lbl_custom_hint)

        self.ssh_inputs_frame.setVisible(False)
        ssh_custom_layout.addWidget(self.ssh_inputs_frame)
        c_box.addWidget(self.ssh_custom_container)

        test_row = QHBoxLayout()
        self.btn_test_conn = TouchButton("Bağlantıyı Doğrula", variant="primary")
        self.btn_test_conn.setFixedHeight(38)
        self.btn_test_conn.clicked.connect(self._test_connection)
        test_row.addWidget(self.btn_test_conn)

        self.lbl_conn_status = QLabel("Test Edilmedi")
        self.lbl_conn_status.setProperty("class", "PillBadge PillWarning")
        test_row.addWidget(self.lbl_conn_status)
        test_row.addStretch()
        c_box.addLayout(test_row)

        self._apply_platform_default_mode()
        l_layout.addWidget(conn_card)

        # 2. KART: Kapanış Kontrolleri
        wrap_card = QFrame()
        wrap_card.setProperty("class", "ModernCard")
        w_layout = QVBoxLayout(wrap_card)
        w_layout.setSpacing(12)

        lbl_s2 = QLabel("🎒 2. Kapanış ve Toplanma Kontrolleri")
        lbl_s2.setStyleSheet("font-size: 15px; font-weight: 700; color: #f8fafc;")
        w_layout.addWidget(lbl_s2)

        self.wrap_items = [
            EquipmentItem(id="w1", name="Sensör ve RF bağlantıları güvenle söküldü", is_mandatory=True),
            EquipmentItem(id="w2", name="Cihaz güç kaynağı ve aküsü kapatıldı", is_mandatory=True),
            EquipmentItem(id="w3", name="Kablolar ve antenler toplanıp çantaya yerleştirildi", is_mandatory=True),
        ]
        self.wrap_checklist = ChecklistWidget(self.wrap_items)
        self.wrap_checklist.checklist_updated.connect(self._update_readiness)
        w_layout.addWidget(self.wrap_checklist)
        l_layout.addWidget(wrap_card)

        # 3. KART: 20-30 GB Log Toplama
        log_card = QFrame()
        log_card.setProperty("class", "ModernCard")
        log_layout = QVBoxLayout(log_card)
        log_layout.setSpacing(12)

        lbl_s3 = QLabel("📦 3. Faaliyet Loglarının Paketlenmesi (20-30 GB)")
        lbl_s3.setStyleSheet("font-size: 15px; font-weight: 700; color: #f8fafc;")
        log_layout.addWidget(lbl_s3)

        self.lbl_log_info = QLabel("Cihazdaki loglar çok çekirdekli tar ile sıkıştırılıp güvenle indirilecektir.")
        self.lbl_log_info.setStyleSheet("color: #94a3b8; font-size: 12px;")
        log_layout.addWidget(self.lbl_log_info)

        log_action_row = QHBoxLayout()
        self.btn_collect_logs = TouchButton("Logları Çek ve Arşivle (Onaylı)", variant="primary")
        self.btn_collect_logs.setFixedHeight(38)
        self.btn_collect_logs.clicked.connect(self._collect_logs)
        log_action_row.addWidget(self.btn_collect_logs)

        self.lbl_log_status = QLabel("Beklemede")
        self.lbl_log_status.setProperty("class", "PillBadge PillWarning")
        log_action_row.addWidget(self.lbl_log_status)
        log_action_row.addStretch()
        log_layout.addLayout(log_action_row)

        self.log_progress = QProgressBar()
        self.log_progress.setValue(0)
        self.log_progress.setVisible(False)
        log_layout.addWidget(self.log_progress)
        l_layout.addWidget(log_card)

        # 4. KART: Konfigürasyon Snapshot'ı & Diff
        cfg_card = QFrame()
        cfg_card.setProperty("class", "ModernCard")
        cfg_layout = QVBoxLayout(cfg_card)
        cfg_layout.setSpacing(12)

        lbl_s4 = QLabel("🔍 4. Aktif Konfigürasyon Snapshot'ı & Kıyaslama")
        lbl_s4.setStyleSheet("font-size: 15px; font-weight: 700; color: #f8fafc;")
        cfg_layout.addWidget(lbl_s4)

        snap_row = QHBoxLayout()
        self.btn_pull_config = TouchButton("Sahadaki Konfigürasyonu Çek", variant="ghost")
        self.btn_pull_config.setFixedHeight(38)
        self.btn_pull_config.clicked.connect(self._pull_active_config)
        snap_row.addWidget(self.btn_pull_config)

        self.btn_open_diff = TouchButton("Farkları Kıyasla (Diff)", variant="warning")
        self.btn_open_diff.setFixedHeight(38)
        self.btn_open_diff.setEnabled(False)
        self.btn_open_diff.clicked.connect(self._open_diff_dialog)
        snap_row.addWidget(self.btn_open_diff)
        snap_row.addStretch()
        cfg_layout.addLayout(snap_row)

        self.lbl_diff_status = QLabel("Henüz konfigürasyon çekilmedi.")
        self.lbl_diff_status.setStyleSheet("color: #94a3b8; font-size: 12px;")
        cfg_layout.addWidget(self.lbl_diff_status)
        l_layout.addWidget(cfg_card)

        # 5. KART: USB Senkronizasyon Kartı
        usb_card = QFrame()
        usb_card.setProperty("class", "ModernCard")
        usb_layout = QVBoxLayout(usb_card)
        usb_layout.setSpacing(12)

        lbl_s5 = QLabel("💾 5. USB Bellek Senkronizasyonu")
        lbl_s5.setStyleSheet("font-size: 15px; font-weight: 700; color: #f8fafc;")
        usb_layout.addWidget(lbl_s5)

        self.lbl_usb_detect = QLabel()
        self.lbl_usb_detect.setStyleSheet("color: #60a5fa; font-weight: 600; font-size: 13px;")
        usb_layout.addWidget(self.lbl_usb_detect)

        self.btn_sync_usb = TouchButton("Tüm Görev Verilerini USB'ye Kopyala", variant="success")
        self.btn_sync_usb.setFixedHeight(38)
        self.btn_sync_usb.clicked.connect(self._sync_to_usb)
        usb_layout.addWidget(self.btn_sync_usb)
        l_layout.addWidget(usb_card)

        l_layout.addStretch()
        scroll.setWidget(left_container)
        content_layout.addWidget(scroll, 5)

        # Sağ Kolon: Terminal
        self.console = LiveConsoleWidget("Faaliyet Sonu Terminal & Loglar")
        content_layout.addWidget(self.console, 4)

        main_layout.addLayout(content_layout)

        # Alt Kapanış Butonu & Durum Çubuğu
        bottom_bar = QHBoxLayout()
        bottom_bar.setContentsMargins(0, 10, 0, 0)

        self.lbl_end_summary = QLabel("")
        self.lbl_end_summary.setStyleSheet("font-size: 13px; font-weight: 500;")
        bottom_bar.addWidget(self.lbl_end_summary)
        bottom_bar.addStretch()

        self.chk_force_end = QCheckBox("Eksik adımlara rağmen faaliyeti tamamlamaya izin ver (Force)")
        self.chk_force_end.setStyleSheet("color: #94a3b8; font-size: 13px;")
        self.chk_force_end.stateChanged.connect(self._update_readiness)
        bottom_bar.addWidget(self.chk_force_end)

        self.btn_finish_mission = TouchButton("Görevi ve Faaliyeti Resmen Tamamla  ✓", variant="primary")
        self.btn_finish_mission.setMinimumWidth(340)
        self.btn_finish_mission.setFixedHeight(42)
        self.btn_finish_mission.setEnabled(False)
        self.btn_finish_mission.clicked.connect(self._finish_mission)
        bottom_bar.addWidget(self.btn_finish_mission)

        main_layout.addLayout(bottom_bar)
        self._update_readiness()

    def _apply_platform_default_mode(self):
        """Çalışılan işletim sistemine göre bağlantı modunu önden seçer (kullanıcı elle değiştirebilir)."""
        is_linux = sys.platform.startswith("linux")
        is_win = sys.platform.startswith("win")

        if is_linux:
            self.radio_local.setChecked(True)
            self.lbl_platform_detected.setText("🐧 Linux Ortamı Algılandı")
            self.lbl_platform_detected.setProperty("class", "PillBadge PillSuccess")
            self.lbl_mode_hint.setText(
                "💡 <b>Linux ortamı algılandı:</b> Uygulama doğrudan saha cihazında çalıştığı için "
                "<b>'Doğrudan Yerel'</b> modu önden seçildi (dilediğinizde yukarıdan Uzak SSH'a geçebilirsiniz)."
            )
        elif is_win:
            self.radio_ssh.setChecked(True)
            self.lbl_platform_detected.setText("🪟 Windows Ortamı Algılandı")
            self.lbl_platform_detected.setProperty("class", "PillBadge PillInfo")
            self.lbl_mode_hint.setText(
                "💡 <b>Windows ortamı algılandı:</b> Destek bilgisayarından sahaya bağlanıldığı için "
                "<b>'Uzak SSH'</b> modu önden seçildi (dilediğinizde yukarıdan Yerel moda geçebilirsiniz)."
            )
        else:
            self.radio_ssh.setChecked(True)
            self.lbl_platform_detected.setText(f"💻 {sys.platform} Algılandı")
            self.lbl_platform_detected.setProperty("class", "PillBadge PillMuted")
            self.lbl_mode_hint.setText(
                "💡 Uzak SSH modu önden seçildi (dilediğinizde elle değiştirebilirsiniz)."
            )

        self.lbl_platform_detected.style().unpolish(self.lbl_platform_detected)
        self.lbl_platform_detected.style().polish(self.lbl_platform_detected)

    def _on_connection_mode_changed(self, checked: bool):
        if not checked or getattr(self, "_loading_session", False):
            return
        is_local = self.radio_local.isChecked()
        mode_str = "Doğrudan Yerel Linux" if is_local else "Uzak SSH Bağlantısı"
        if hasattr(self, "ssh_custom_container"):
            self.ssh_custom_container.setVisible(not is_local)
        self.lbl_conn_status.setText("Test Edilmedi")
        self.lbl_conn_status.setProperty("class", "PillBadge PillWarning")
        self.lbl_conn_status.style().unpolish(self.lbl_conn_status)
        self.lbl_conn_status.style().polish(self.lbl_conn_status)
        self.adapter = None
        if hasattr(self, "console"):
            self.console.append_log(f"Bağlantı modu değiştirildi: {mode_str}", "system")
        self._update_readiness()

    def _sync_ssh_inputs_from_profile(self):
        if not self.profile or not hasattr(self, "txt_ssh_host"):
            return
        dev = self.profile.target_device
        self.txt_ssh_host.setText(dev.host or "")
        self.txt_ssh_port.setText(str(dev.port) if dev.port else "22")
        self.txt_ssh_user.setText(dev.username or "root")
        self.txt_ssh_pass.setText(dev.password or "")
        self.txt_ssh_key.setText(dev.key_path or "")

    def _on_custom_ssh_toggled(self, checked: bool):
        if hasattr(self, "ssh_inputs_frame"):
            self.ssh_inputs_frame.setVisible(checked)
        if getattr(self, "_loading_session", False):
            return
        if checked and self.profile:
            if hasattr(self, "txt_ssh_host") and not self.txt_ssh_host.text().strip():
                self._sync_ssh_inputs_from_profile()
        self._on_ssh_credentials_changed()
        mode_desc = "Elle girilen özel SSH bilgileri" if checked else "Plandaki varsayılan cihaz ayarları"
        if hasattr(self, "console"):
            self.console.append_log(f"SSH Bağlantı Kaynağı: {mode_desc}", "system")

    def _on_ssh_credentials_changed(self):
        if getattr(self, "_loading_session", False):
            return
        if hasattr(self, "lbl_conn_status"):
            self.lbl_conn_status.setText("Test Edilmedi")
            self.lbl_conn_status.setProperty("class", "PillBadge PillWarning")
            self.lbl_conn_status.style().unpolish(self.lbl_conn_status)
            self.lbl_conn_status.style().polish(self.lbl_conn_status)
        self.adapter = None
        self._update_readiness()

    def _browse_ssh_key(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "SSH Özel Anahtar Dosyasını Seçin",
            "",
            "Tüm Dosyalar (*.*);;Anahtar Dosyaları (*.pem *.key id_rsa*)"
        )
        if file_path:
            self.txt_ssh_key.setText(file_path)

    def _get_active_adapter(self) -> BaseExecutionAdapter:
        if self.radio_local.isChecked():
            return LocalExecutionAdapter()
        else:
            if hasattr(self, "chk_custom_ssh") and self.chk_custom_ssh.isChecked() and self.profile:
                host = self.txt_ssh_host.text().strip() or self.profile.target_device.host
                try:
                    port = int(self.txt_ssh_port.text().strip())
                except ValueError:
                    port = self.profile.target_device.port
                username = self.txt_ssh_user.text().strip() or self.profile.target_device.username
                password = self.txt_ssh_pass.text() if self.txt_ssh_pass.text() else self.profile.target_device.password
                key_path = self.txt_ssh_key.text().strip() if self.txt_ssh_key.text().strip() else self.profile.target_device.key_path

                custom_config = TargetDeviceConfig(
                    host=host,
                    port=port,
                    username=username,
                    password=password,
                    key_path=key_path,
                    remote_config_path=self.profile.target_device.remote_config_path,
                    remote_log_dir=self.profile.target_device.remote_log_dir
                )
                return SSHExecutionAdapter(custom_config)
            else:
                return SSHExecutionAdapter(self.profile.target_device)

    def _test_connection(self):
        if not self.profile:
            return

        self.adapter = self._get_active_adapter()
        if isinstance(self.adapter, SSHExecutionAdapter):
            cfg = self.adapter.config
            source_lbl = "Elle Girilen" if (hasattr(self, "chk_custom_ssh") and self.chk_custom_ssh.isChecked()) else "Plandaki"
            self.console.append_log(f"SSH Bağlantısı doğrulanıyor ({source_lbl}): {cfg.username}@{cfg.host}:{cfg.port}...", "info")
        else:
            self.console.append_log("Doğrudan Yerel bağlantı doğrulanıyor...", "info")

        success, msg = self.adapter.test_connection()
        if success:
            self.lbl_conn_status.setText("✓ Başarılı")
            self.lbl_conn_status.setProperty("class", "PillBadge PillSuccess")
            self.console.append_log(f"BAĞLANTI TAMAMLANDI: {msg}", "info")
        else:
            self.lbl_conn_status.setText("Hata")
            self.lbl_conn_status.setProperty("class", "PillBadge PillDanger")
            self.console.append_log(f"HATA: {msg}", "error")

        self.lbl_conn_status.style().unpolish(self.lbl_conn_status)
        self.lbl_conn_status.style().polish(self.lbl_conn_status)
        self._update_readiness()

    def load_session(self, profile: LocationProfile, adapter: Optional[BaseExecutionAdapter] = None):
        self._loading_session = True
        self.profile = profile
        self.captured_config_text = None
        self._usb_synced = False
        if hasattr(self, "chk_force_end"):
            self.chk_force_end.setChecked(False)

        if hasattr(self, "info_lbl"):
            self.info_lbl.setText(f"Aktif Lokasyon: <b>{profile.name}</b>  •  Hedef: {profile.target_device.host}")

        # Eğer Stage 2'den adaptör aktarıldıysa
        if adapter is not None:
            self.adapter = adapter
            if isinstance(adapter, LocalExecutionAdapter):
                self.radio_local.setChecked(True)
                if hasattr(self, "ssh_custom_container"):
                    self.ssh_custom_container.setVisible(False)
                if hasattr(self, "chk_custom_ssh"):
                    self.chk_custom_ssh.setChecked(False)
                self.lbl_conn_status.setText("✓ Başarılı")
                self.lbl_conn_status.setProperty("class", "PillBadge PillSuccess")
            elif isinstance(adapter, SSHExecutionAdapter):
                self.radio_ssh.setChecked(True)
                if hasattr(self, "ssh_custom_container"):
                    self.ssh_custom_container.setVisible(True)
                cfg = adapter.config
                is_custom = (
                    cfg.host != profile.target_device.host or
                    cfg.port != profile.target_device.port or
                    cfg.username != profile.target_device.username or
                    cfg.password != profile.target_device.password or
                    cfg.key_path != profile.target_device.key_path
                )
                if hasattr(self, "chk_custom_ssh"):
                    self.chk_custom_ssh.setChecked(is_custom)
                if hasattr(self, "ssh_inputs_frame"):
                    self.ssh_inputs_frame.setVisible(is_custom)
                self.txt_ssh_host.setText(cfg.host or "")
                self.txt_ssh_port.setText(str(cfg.port) if cfg.port else "22")
                self.txt_ssh_user.setText(cfg.username or "root")
                self.txt_ssh_pass.setText(cfg.password or "")
                self.txt_ssh_key.setText(cfg.key_path or "")

                is_connected = bool(adapter._client and adapter._client.get_transport() and adapter._client.get_transport().is_active())
                if is_connected:
                    self.lbl_conn_status.setText("✓ Başarılı")
                    self.lbl_conn_status.setProperty("class", "PillBadge PillSuccess")
                else:
                    self.lbl_conn_status.setText("Test Edilmedi")
                    self.lbl_conn_status.setProperty("class", "PillBadge PillWarning")
                    self.adapter = None
        else:
            self.adapter = None
            if hasattr(self, "chk_custom_ssh"):
                self.chk_custom_ssh.setChecked(False)
            if hasattr(self, "ssh_inputs_frame"):
                self.ssh_inputs_frame.setVisible(False)
            self._sync_ssh_inputs_from_profile()
            self._apply_platform_default_mode()
            self.lbl_conn_status.setText("Test Edilmedi")
            self.lbl_conn_status.setProperty("class", "PillBadge PillWarning")

        self.lbl_conn_status.style().unpolish(self.lbl_conn_status)
        self.lbl_conn_status.style().polish(self.lbl_conn_status)

        self.lbl_log_status.setText("Beklemede")
        self.lbl_log_status.setProperty("class", "PillBadge PillWarning")
        self.lbl_log_status.style().unpolish(self.lbl_log_status)
        self.lbl_log_status.style().polish(self.lbl_log_status)

        self.lbl_diff_status.setText("Henüz konfigürasyon çekilmedi.")
        self.btn_open_diff.setEnabled(False)

        self.console.append_log(f"3. Aşama Başlatıldı. Lokasyon: {profile.name}", "system")
        self._check_usb_status()
        self._loading_session = False
        self._update_readiness()

    def _check_usb_status(self):
        is_usb = AppPaths.is_running_from_usb()
        if is_usb:
            self.lbl_usb_detect.setText("✓ Uygulama doğrudan USB'den çalışıyor. Veriler USB'de.")
            self.btn_sync_usb.setText("Veriler Zaten USB'de")
            self.btn_sync_usb.setEnabled(False)
        else:
            drives = AppPaths.detect_removable_drives()
            if drives:
                d_str = ", ".join(str(d) for d in drives)
                self.lbl_usb_detect.setText(f"✓ Takılı USB Bellek Bulundu: {d_str}")
                self.btn_sync_usb.setEnabled(True)
            else:
                self.lbl_usb_detect.setText("Çıkarılabilir USB bellek takılı değil. Veriler yerel diskte saklanıyor.")
                self.btn_sync_usb.setEnabled(True)
        self._update_readiness()

    def _collect_logs(self):
        if not self.profile:
            return

        if not self.adapter or "Başarılı" not in self.lbl_conn_status.text():
            QMessageBox.warning(self, "Bağlantı Gerekli", "Lütfen önce cihaz bağlantısını doğrulayınız.")
            self.console.append_log("Bağlantı doğrulanmadan log toplanamaz. Önce 'Bağlantıyı Doğrula' butonuna basınız.", "warn")
            return

        is_local = isinstance(self.adapter, LocalExecutionAdapter)
        mode_label = "Doğrudan Yerel" if is_local else "Uzak SSH"

        reply = QMessageBox.question(
            self,
            "Büyük Log Toplama Onayı",
            f"Bağlantı Modu: {mode_label}\n"
            f"'{self.profile.target_device.remote_log_dir}' klasöründeki tüm loglar "
            f"sıkıştırılacak (tar.gz) ve görev arşivine aktarılacaktır.\n\n"
            "İşlem başlatılsın mı?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply != QMessageBox.Yes:
            return

        session_dir = self.mission_manager.current_session_dir or AppPaths.get_missions_dir()
        archive_name = f"logs_{self.profile.id}.tar.gz"
        local_archive_path = session_dir / archive_name

        if is_local:
            remote_archive_path = str(Path(tempfile.gettempdir()) / archive_name)
            self.console.append_log("Doğrudan yerel log toplama işlemi başlatıldı...", "system")
        else:
            remote_archive_path = f"/tmp/{archive_name}"
            cfg = self.adapter.config if isinstance(self.adapter, SSHExecutionAdapter) else None
            host_info = f" ({cfg.username}@{cfg.host})" if cfg else ""
            self.console.append_log(f"Uzak SSH üzerinden log toplama başlatıldı{host_info}...", "system")

        self.log_progress.setVisible(True)
        self.log_progress.setValue(25)

        self.console.append_log("Hedef sistemde çok çekirdekli tar sıkıştırma tetikleniyor...", "info")
        success, sha = self.adapter.compress_logs(
            log_source_dir=self.profile.target_device.remote_log_dir,
            output_archive_path=remote_archive_path,
            log_callback=lambda msg: self.console.append_log(msg, "dim")
        )

        if not success:
            self.console.append_log(f"SIKIŞTIRMA HATASI: {sha}", "error")
            QMessageBox.critical(self, "Hata", f"Loglar sıkıştırılamadı:\n{sha}")
            self.log_progress.setVisible(False)
            self.lbl_log_status.setText("Hata")
            self.lbl_log_status.setProperty("class", "PillBadge PillDanger")
            self.lbl_log_status.style().unpolish(self.lbl_log_status)
            self.lbl_log_status.style().polish(self.lbl_log_status)
            self._update_readiness()
            return

        self.log_progress.setValue(60)
        self.console.append_log(f"Sıkıştırma başarılı. SHA-256: {sha}", "info")

        if is_local:
            self.console.append_log(f"Yerel arşiv kopyalanıyor: {remote_archive_path} -> {local_archive_path}", "info")
        else:
            self.console.append_log(f"SFTP ile arşiv indiriliyor: {remote_archive_path} -> {local_archive_path}", "info")

        fetch_success, fetch_msg = self.adapter.fetch_archive(
            source_archive_path=remote_archive_path,
            local_destination_path=str(local_archive_path),
            progress_callback=lambda cur, tot: self._on_download_progress(cur, tot)
        )

        if fetch_success:
            self.log_progress.setValue(100)
            self.lbl_log_status.setText("✓ Alındı (SHA-256)")
            self.lbl_log_status.setProperty("class", "PillBadge PillSuccess")
            self.console.append_log(f"LOG ÇEKME TAMAMLANDI: {local_archive_path}", "info")

            if self.mission_manager.current_session:
                self.mission_manager.current_session.downloaded_logs_path = str(local_archive_path)
                self.mission_manager.current_session.logs_checksum_sha256 = sha
                self.mission_manager.save_current_session()

            QMessageBox.information(
                self,
                "Loglar Başarıyla Alındı",
                f"Tüm loglar sıkıştırılarak arşivlendi.\n\nSHA-256: {sha}\nKonum: {local_archive_path}"
            )
        else:
            self.lbl_log_status.setText("Hata")
            self.lbl_log_status.setProperty("class", "PillBadge PillDanger")
            self.console.append_log(f"İNDİRME / AKTARMA HATASI: {fetch_msg}", "error")

        self.lbl_log_status.style().unpolish(self.lbl_log_status)
        self.lbl_log_status.style().polish(self.lbl_log_status)
        self._update_readiness()

    def _on_download_progress(self, current_bytes: int, total_bytes: int):
        if total_bytes > 0:
            pct = int((current_bytes / total_bytes) * 100)
            self.log_progress.setValue(pct)

    def _pull_active_config(self):
        if not self.profile:
            return

        if not self.adapter or "Başarılı" not in self.lbl_conn_status.text():
            QMessageBox.warning(self, "Bağlantı Gerekli", "Lütfen önce cihaz bağlantısını doğrulayınız.")
            self.console.append_log("Bağlantı doğrulanmadan konfigürasyon çekilemez. Önce 'Bağlantıyı Doğrula' butonuna basınız.", "warn")
            return

        is_local = isinstance(self.adapter, LocalExecutionAdapter)
        target_path = self.profile.target_device.remote_config_path
        if is_local:
            self.console.append_log(f"Yerel konfigürasyon okunuyor: {target_path}", "info")
        else:
            cfg = self.adapter.config if isinstance(self.adapter, SSHExecutionAdapter) else None
            host_info = f" ({cfg.username}@{cfg.host})" if cfg else ""
            self.console.append_log(f"Uzak konfigürasyon çekiliyor{host_info}: {target_path}...", "info")

        success, content = self.adapter.pull_active_configuration(target_path)

        if success:
            self.captured_config_text = content
            self.mission_manager.store_captured_config(content)
            self.console.append_log("Aktif konfigürasyon başarıyla çekildi ve arşivlendi.", "info")

            _, has_diff = ConfigDiffEngine.compare_configs(
                self.profile.baseline_config_content,
                self.captured_config_text
            )

            if has_diff:
                self.lbl_diff_status.setText("<span style='color:#fbbf24;'>⚠ Sahadaki konfigürasyonda değişiklikler tespit edildi.</span>")
                self.console.append_log("BİLGİ: Sahadaki konfigürasyon referans profilden farklı.", "warn")
                if self.mission_manager.current_session:
                    self.mission_manager.current_session.has_config_drift = True
                    self.mission_manager.save_current_session()
            else:
                self.lbl_diff_status.setText("<span style='color:#34d399;'>✓ Sahadaki konfigürasyon referans ile birebir aynı.</span>")

            self.btn_open_diff.setEnabled(True)
        else:
            self.captured_config_text = None
            self.console.append_log(f"KONFİGÜRASYON ÇEKİLEMEDİ: {content}", "error")
            QMessageBox.warning(self, "Hata", f"Konfigürasyon dosyası okunamadı:\n{content}")

        self._update_readiness()

    def _open_diff_dialog(self):
        if not self.captured_config_text or not self.profile:
            return

        dialog = ConfigDiffDialog(
            profile_name=self.profile.name,
            baseline_text=self.profile.baseline_config_content,
            field_text=self.captured_config_text,
            parent=self
        )
        dialog.merged_to_baseline.connect(self._on_baseline_merged)
        dialog.exec()

    def _on_baseline_merged(self, new_baseline_content: str):
        if self.profile:
            self.profile_manager.update_baseline_config(self.profile.id, new_baseline_content)
            self.profile.baseline_config_content = new_baseline_content
            self.console.append_log(f"'{self.profile.name}' ana profil konfigürasyonu güncellendi!", "system")
            self.lbl_diff_status.setText("<span style='color:#34d399;'>✓ Ana profil başarıyla güncellendi.</span>")
            self._update_readiness()

    def _sync_to_usb(self):
        drives = AppPaths.detect_removable_drives()
        if not drives:
            QMessageBox.warning(self, "USB Bulunamadı", "Lütfen bilgisayara bir USB bellek takıp tekrar deneyiniz.")
            return

        target_usb = drives[0]
        reply = QMessageBox.question(
            self,
            "USB Senkronizasyonu",
            f"Tüm görev verileri şu USB sürücüsüne aktarılacak:\n\n"
            f"Hedef: {target_usb}\n\n"
            "Devam etmek istiyor musunuz?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply != QMessageBox.Yes:
            return

        try:
            self.console.append_log(f"USB senkronizasyonu başlatılıyor: {target_usb}...", "info")
            usb_missions_dir = target_usb / "data" / "missions"
            usb_missions_dir.mkdir(parents=True, exist_ok=True)

            current_dir = self.mission_manager.current_session_dir
            if current_dir and current_dir.exists():
                dest_dir = usb_missions_dir / current_dir.name
                shutil.copytree(current_dir, dest_dir, dirs_exist_ok=True)
                self._usb_synced = True
                self.console.append_log(f"Senkronizasyon tamamlandı: {dest_dir}", "info")
                self.btn_sync_usb.setText("✓ USB'ye Kopyalandı (Yeniden Eşitle)")
                QMessageBox.information(
                    self,
                    "Senkronizasyon Başarılı",
                    f"Tüm görev ve log dosyaları başarıyla aktarıldı:\n{dest_dir}"
                )
                self._update_readiness()
        except Exception as e:
            self.console.append_log(f"USB Kopyalama Hatası: {e}", "error")
            QMessageBox.critical(self, "Hata", f"USB'ye kopyalama sırasında hata oluştu:\n{e}")
            self._update_readiness()

    def _update_readiness(self):
        if not hasattr(self, "lbl_end_summary") or not hasattr(self, "btn_finish_mission"):
            return

        if not self.profile:
            self.lbl_end_summary.setText("<span style='color: #94a3b8;'>Lokasyon profili yüklenmedi</span>")
            self.btn_finish_mission.setText("Görevi ve Faaliyeti Resmen Tamamla  ✓")
            self.btn_finish_mission.setEnabled(False)
            self.btn_finish_mission.set_variant("primary")
            return

        reasons = []

        # 1. Cihaz Bağlantısı Doğrulaması
        conn_ok = (self.adapter is not None and hasattr(self, "lbl_conn_status") and "Başarılı" in self.lbl_conn_status.text())
        if not conn_ok:
            reasons.append("Cihaz bağlantısı doğrulanmadı")

        # 2. Kapanış ve Toplanma Kontrolleri
        checklist_ok = self.wrap_checklist.are_all_mandatory_checked() if hasattr(self, "wrap_checklist") else False
        if not checklist_ok:
            missing = self.wrap_checklist.get_missing_mandatory_items() if hasattr(self, "wrap_checklist") else []
            reasons.append(f"Toplanma kontrolleri tamamlanmadı ({len(missing)} eksik)")

        # 3. Log Toplama Denetimi
        log_ok = hasattr(self, "lbl_log_status") and ("Alındı" in self.lbl_log_status.text())
        if not log_ok:
            reasons.append("Faaliyet logları arşivlenmedi")

        # 4. Aktif Konfigürasyon Snapshot'ı Denetimi
        cfg_ok = (self.captured_config_text is not None)
        if not cfg_ok:
            reasons.append("Aktif konfigürasyon çekilmedi")

        # 5. USB Senkronizasyon Denetimi (Harici USB takılıysa)
        is_running_usb = AppPaths.is_running_from_usb()
        has_removable = bool(AppPaths.detect_removable_drives())
        usb_synced = getattr(self, "_usb_synced", False)
        if not is_running_usb and has_removable and not usb_synced:
            reasons.append("USB senkronizasyonu yapılmadı")

        force_active = hasattr(self, "chk_force_end") and self.chk_force_end.isChecked()

        if not reasons:
            self.lbl_end_summary.setText("<span style='color: #34d399;'>✓ Tüm faaliyet sonu adımları ve kontroller tamamlandı.</span>")
            self.btn_finish_mission.setText("Görevi ve Faaliyeti Resmen Tamamla  ✓")
            self.btn_finish_mission.setEnabled(True)
            self.btn_finish_mission.set_variant("success")
        elif force_active:
            self.lbl_end_summary.setText(f"<span style='color: #fbbf24;'>⚠️ Force Aktif: {len(reasons)} eksik adıma rağmen tamamlanıyor</span>")
            self.btn_finish_mission.setText("⚠️ Eksik Adımlarla Yine de Tamamla  ✓")
            self.btn_finish_mission.setEnabled(True)
            self.btn_finish_mission.set_variant("warning")
        else:
            self.lbl_end_summary.setText(f"<span style='color: #fbbf24;'>Bekleyen: {', '.join(reasons)}</span>")
            self.btn_finish_mission.setText("Görevi ve Faaliyeti Resmen Tamamla  ✓")
            self.btn_finish_mission.setEnabled(False)
            self.btn_finish_mission.set_variant("primary")

    def _finish_mission(self):
        if not self.btn_finish_mission.isEnabled():
            return

        reply = QMessageBox.question(
            self,
            "Görevi Tamamla",
            "Saha faaliyeti başarıyla tamamlandı.\n"
            "Yeni bir görev için başa dönülsün mü?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        if reply == QMessageBox.Yes:
            if self.adapter and hasattr(self.adapter, "close"):
                try:
                    self.adapter.close()
                except Exception:
                    pass
            self.console.append_log("GÖREV RESMEN SONLANDIRILDI.", "system")
            self.mission_finished.emit()
