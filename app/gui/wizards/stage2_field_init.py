"""
FieldOps Assistant - 2. Aşama: Sahada Faaliyet Başlangıcı (Stage 2: Field Initiation)
Modern kart mimarisi, interaktif sürüm denetimi ve developer terminal akışı.
"""

from __future__ import annotations
import sys
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QMessageBox, QScrollArea, QRadioButton, QButtonGroup, QCheckBox,
    QLineEdit, QFileDialog
)

from app.adapters.base_adapter import BaseExecutionAdapter
from app.adapters.local_adapter import LocalExecutionAdapter
from app.adapters.ssh_adapter import SSHExecutionAdapter
from app.core.models import LocationProfile, SoftwareRequirement, TargetDeviceConfig
from app.gui.widgets.live_console import LiveConsoleWidget
from app.gui.widgets.touch_button import TouchButton


class Stage2FieldInitWidget(QWidget):
    """2. Aşama Ekranı: Cihaz bağlantısı, sürüm denetimi ve konfigürasyon aktivasyonu."""
    stage_completed = Signal(BaseExecutionAdapter)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.profile: Optional[LocationProfile] = None
        self.adapter: Optional[BaseExecutionAdapter] = None
        self._sw_checked: bool = False
        self._sw_pending: list[str] = []

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

        title = QLabel("2. AŞAMA: Sahada Faaliyet Başlangıcı")
        title.setProperty("class", "SectionTitle")
        h_layout.addWidget(title)

        self.info_lbl = QLabel("Saha lokasyonuna ulaşıldığında cihaz bağlantısı ve operasyonel hazırlıklar yürütülür.")
        self.info_lbl.setProperty("class", "SectionSubtitle")
        h_layout.addWidget(self.info_lbl)
        main_layout.addWidget(header)

        # İki Sütunlu Düzen (Sol: Adım Kartları, Sağ: Canlı Terminal)
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

        # 1. KART: Bağlantı Modu
        conn_card = QFrame()
        conn_card.setProperty("class", "ModernCard")
        c_box = QVBoxLayout(conn_card)
        c_box.setSpacing(12)

        mode_header = QHBoxLayout()
        lbl_s1 = QLabel("🔌 Cihaz Bağlantı Modu")
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

        # 2. KART: Kurulu Yazılım Sürüm Denetimi
        self.sw_card = QFrame()
        self.sw_card.setProperty("class", "ModernCard")
        self.sw_layout = QVBoxLayout(self.sw_card)
        self.sw_layout.setSpacing(12)

        sw_header = QHBoxLayout()
        lbl_s2 = QLabel("🔍 Sahadaki Kurulu Yazılım Sürümleri")
        lbl_s2.setStyleSheet("font-size: 15px; font-weight: 700; color: #f8fafc;")
        sw_header.addWidget(lbl_s2)
        sw_header.addStretch()

        self.btn_check_version = TouchButton("Sürümleri Sorgula", variant="ghost")
        self.btn_check_version.setFixedHeight(34)
        self.btn_check_version.setStyleSheet("font-size: 12px; padding: 2px 14px; min-height: 32px;")
        self.btn_check_version.clicked.connect(self._check_installed_versions)
        sw_header.addWidget(self.btn_check_version)
        self.sw_layout.addLayout(sw_header)

        self.sw_cards_container = QVBoxLayout()
        self.sw_cards_container.setSpacing(8)
        self.sw_layout.addLayout(self.sw_cards_container)
        l_layout.addWidget(self.sw_card)

        # 3. KART: Konfigürasyon Enjeksiyonu
        cfg_card = QFrame()
        cfg_card.setProperty("class", "ModernCard")
        cfg_layout = QVBoxLayout(cfg_card)
        cfg_layout.setSpacing(12)

        lbl_s3 = QLabel("⚙ Lokasyona Özel Konfigürasyon Enjeksiyonu")
        lbl_s3.setStyleSheet("font-size: 15px; font-weight: 700; color: #f8fafc;")
        cfg_layout.addWidget(lbl_s3)

        self.lbl_cfg_target = QLabel()
        self.lbl_cfg_target.setStyleSheet("color: #94a3b8; font-size: 12px;")
        cfg_layout.addWidget(self.lbl_cfg_target)

        cfg_action_row = QHBoxLayout()
        self.btn_apply_config = TouchButton("Konfigürasyonu Uygula (Onaylı)", variant="warning")
        self.btn_apply_config.setFixedHeight(38)
        self.btn_apply_config.clicked.connect(self._apply_configuration)
        cfg_action_row.addWidget(self.btn_apply_config)

        self.lbl_cfg_status = QLabel("Beklemede")
        self.lbl_cfg_status.setProperty("class", "PillBadge PillWarning")
        cfg_action_row.addWidget(self.lbl_cfg_status)
        cfg_action_row.addStretch()
        cfg_layout.addLayout(cfg_action_row)
        l_layout.addWidget(cfg_card)

        l_layout.addStretch()
        scroll.setWidget(left_container)
        content_layout.addWidget(scroll, 5)

        # Sağ Kolon: Terminal
        self.console = LiveConsoleWidget("Terminal & Canlı Saha Akışı")
        content_layout.addWidget(self.console, 4)

        main_layout.addLayout(content_layout)

        # Alt Buton & Durum Çubuğu
        bottom_bar = QHBoxLayout()
        bottom_bar.setContentsMargins(0, 10, 0, 0)

        self.lbl_init_summary = QLabel("")
        self.lbl_init_summary.setStyleSheet("font-size: 13px; font-weight: 500;")
        bottom_bar.addWidget(self.lbl_init_summary)
        bottom_bar.addStretch()

        self.chk_force_init = QCheckBox("Eksik adımlara rağmen ilerlemeye izin ver (Force)")
        self.chk_force_init.setStyleSheet("color: #94a3b8; font-size: 13px;")
        self.chk_force_init.stateChanged.connect(self._update_readiness)
        bottom_bar.addWidget(self.chk_force_init)

        self.btn_complete_stage2 = TouchButton("Faaliyeti Başlat ve Aşama 3'e Geç  ➔", variant="primary")
        self.btn_complete_stage2.setMinimumWidth(320)
        self.btn_complete_stage2.setFixedHeight(42)
        self.btn_complete_stage2.setEnabled(False)
        self.btn_complete_stage2.clicked.connect(self._on_complete_stage2)
        bottom_bar.addWidget(self.btn_complete_stage2)

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
        if not checked:
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
        self._sw_checked = False
        self._sw_pending = [req.name for req in self.profile.software_requirements] if self.profile else []
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
        if checked and self.profile:
            if hasattr(self, "txt_ssh_host") and not self.txt_ssh_host.text().strip():
                self._sync_ssh_inputs_from_profile()
        self._on_ssh_credentials_changed()
        mode_desc = "Elle girilen özel SSH bilgileri" if checked else "Plandaki varsayılan cihaz ayarları"
        if hasattr(self, "console"):
            self.console.append_log(f"SSH Bağlantı Kaynağı: {mode_desc}", "system")

    def _on_ssh_credentials_changed(self):
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

    def load_session(self, profile: LocationProfile):
        self.profile = profile
        self.adapter = None
        self._sw_checked = False
        self._sw_pending = [req.name for req in profile.software_requirements] if profile else []
        if hasattr(self, "chk_force_init"):
            self.chk_force_init.setChecked(False)
        if hasattr(self, "chk_custom_ssh"):
            self.chk_custom_ssh.setChecked(False)
        self._sync_ssh_inputs_from_profile()

        self.lbl_conn_status.setText("Test Edilmedi")
        self.lbl_conn_status.setProperty("class", "PillBadge PillWarning")
        self.lbl_conn_status.style().unpolish(self.lbl_conn_status)
        self.lbl_conn_status.style().polish(self.lbl_conn_status)

        self.lbl_cfg_status.setText("Beklemede")
        self.lbl_cfg_status.setProperty("class", "PillBadge PillWarning")
        self.lbl_cfg_status.style().unpolish(self.lbl_cfg_status)
        self.lbl_cfg_status.style().polish(self.lbl_cfg_status)

        self.info_lbl.setText(f"Aktif Lokasyon: <b>{profile.name}</b>  •  Hedef: {profile.target_device.host}")
        self.lbl_cfg_target.setText(f"Hedef Dosya: <code>{profile.target_device.remote_config_path}</code>")
        self.console.append_log(f"2. Aşama Başlatıldı. Hedef: {profile.target_device.host}", "system")
        self._apply_platform_default_mode()
        self._update_readiness()

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
            self._check_installed_versions()
        else:
            self.lbl_conn_status.setText("Hata")
            self.lbl_conn_status.setProperty("class", "PillBadge PillDanger")
            self.console.append_log(f"HATA: {msg}", "error")

        self.lbl_conn_status.style().unpolish(self.lbl_conn_status)
        self.lbl_conn_status.style().polish(self.lbl_conn_status)
        self._update_readiness()

    def _check_installed_versions(self):
        if not self.profile:
            return
        if not self.adapter:
            if hasattr(self, "console"):
                self.console.append_log("Önce cihaz bağlantısını doğrulayınız.", "warn")
            return

        while self.sw_cards_container.count():
            item = self.sw_cards_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._sw_checked = True
        self._sw_pending = []

        for req in self.profile.software_requirements:
            card = QFrame()
            card.setProperty("class", "ElevatedCard")
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(14, 10, 14, 10)

            info_col = QVBoxLayout()
            info_col.setSpacing(2)
            name_lbl = QLabel(f"<b>{req.name}</b> &nbsp;(Beklenen: v{req.expected_version})")
            name_lbl.setStyleSheet("font-size: 13px; color: #f8fafc;")
            info_col.addWidget(name_lbl)

            self.console.append_log(f"Sürüm sorgulanıyor: {req.version_command}", "dim")
            detected_version = self.adapter.get_installed_version(req.version_command)

            card_layout.addLayout(info_col)
            card_layout.addStretch()

            if detected_version:
                self.console.append_log(f"{req.name} sürüm: {detected_version}", "info")
                if req.expected_version in detected_version:
                    badge = QLabel(f"✓ v{detected_version} Güncel")
                    badge.setProperty("class", "PillBadge PillSuccess")
                    card_layout.addWidget(badge)
                else:
                    self._sw_pending.append(req.name)
                    badge = QLabel(f"v{detected_version} Farklı")
                    badge.setProperty("class", "PillBadge PillWarning")
                    card_layout.addWidget(badge)

                    btn_update = TouchButton("Güncelle", variant="warning")
                    btn_update.setFixedHeight(32)
                    btn_update.setStyleSheet("font-size: 12px; padding: 2px 12px; min-height: 30px;")
                    btn_update.clicked.connect(lambda _, r=req: self._deploy_software(r))
                    card_layout.addWidget(btn_update)
            else:
                self._sw_pending.append(req.name)
                self.console.append_log(f"{req.name} kurulu değil.", "warn")
                badge = QLabel("Kurulu Değil")
                badge.setProperty("class", "PillBadge PillDanger")
                card_layout.addWidget(badge)

                btn_install = TouchButton("Kur", variant="primary")
                btn_install.setFixedHeight(32)
                btn_install.setStyleSheet("font-size: 12px; padding: 2px 12px; min-height: 30px;")
                btn_install.clicked.connect(lambda _, r=req: self._deploy_software(r))
                card_layout.addWidget(btn_install)

            self.sw_cards_container.addWidget(card)

        self._update_readiness()

    def _deploy_software(self, req: SoftwareRequirement):
        if not req.resolved_package_path:
            QMessageBox.warning(self, "Paket Bulunamadı", f"{req.name} için yüklenecek paket dosyası mevcut değil!")
            return

        reply = QMessageBox.question(
            self,
            "Yazılım Güncelleme Onayı",
            f"'{req.name}' yazılımı hedef cihaza yüklenecektir.\n\n"
            f"Paket: {req.resolved_package_path}\n"
            f"Hedef Dizin: {req.target_install_path}\n\n"
            "İşlemi başlatmak istiyor musunuz?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply != QMessageBox.Yes:
            return

        self.console.append_log(f"{req.name} kurulumu başlatılıyor...", "system")
        success, msg = self.adapter.deploy_package(
            local_package_path=req.resolved_package_path,
            target_install_path=req.target_install_path,
            service_name=req.service_name
        )

        if success:
            self.console.append_log(f"KURULUM BAŞARILI: {msg}", "info")
            QMessageBox.information(self, "Başarılı", f"{req.name} başarıyla güncellendi!")
            self._check_installed_versions()
        else:
            self.console.append_log(f"KURULUM HATASI: {msg}", "error")
            QMessageBox.critical(self, "Hata", f"Yazılım yüklenirken hata oluştu:\n{msg}")
            self._update_readiness()

    def _apply_configuration(self):
        if not self.profile:
            return
        if not self.adapter:
            if hasattr(self, "console"):
                self.console.append_log("Önce cihaz bağlantısını doğrulayınız.", "warn")
            return

        reply = QMessageBox.question(
            self,
            "Konfigürasyon Uygulama Onayı",
            f"'{self.profile.name}' ayarları hedef cihaza basılacak:\n\n"
            f"Hedef Dosya: {self.profile.target_device.remote_config_path}\n\n"
            "Mevcut ayarlar güncellensin mi?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply != QMessageBox.Yes:
            return

        self.console.append_log("Konfigürasyon hedefe aktarılıyor...", "info")
        success, msg = self.adapter.apply_configuration(
            config_content=self.profile.baseline_config_content,
            remote_config_path=self.profile.target_device.remote_config_path
        )

        if success:
            self.lbl_cfg_status.setText("✓ Uygulandı")
            self.lbl_cfg_status.setProperty("class", "PillBadge PillSuccess")
            self.console.append_log(f"KONFİGÜRASYON UYGULANDI: {msg}", "info")
        else:
            self.lbl_cfg_status.setText("Hata")
            self.lbl_cfg_status.setProperty("class", "PillBadge PillDanger")
            self.console.append_log(f"HATA: {msg}", "error")

        self.lbl_cfg_status.style().unpolish(self.lbl_cfg_status)
        self.lbl_cfg_status.style().polish(self.lbl_cfg_status)
        self._update_readiness()

    def _update_readiness(self):
        if not hasattr(self, "lbl_init_summary") or not hasattr(self, "btn_complete_stage2"):
            return

        if not self.profile:
            self.lbl_init_summary.setText("<span style='color: #94a3b8;'>Lokasyon profili yüklenmedi</span>")
            self.btn_complete_stage2.setText("Faaliyeti Başlat ve Aşama 3'e Geç  ➔")
            self.btn_complete_stage2.setEnabled(False)
            self.btn_complete_stage2.set_variant("primary")
            return

        reasons = []

        # 1. Cihaz Bağlantı Kontrolü
        conn_ok = (self.adapter is not None and "Başarılı" in self.lbl_conn_status.text())
        if not conn_ok:
            if "Hata" in self.lbl_conn_status.text():
                reasons.append("Cihaz bağlantısı başarısız")
            else:
                reasons.append("Cihaz bağlantısı test edilmedi")

        # 2. Yazılım Sürüm Denetimi
        if self.profile.software_requirements:
            if not getattr(self, "_sw_checked", False):
                reasons.append("Yazılım sürümleri sorgulanmadı")
            elif getattr(self, "_sw_pending", []):
                reasons.append(f"Güncelleme bekleyen yazılımlar var ({len(self._sw_pending)})")

        # 3. Konfigürasyon Enjeksiyonu Kontrolü
        has_config = bool(self.profile.baseline_config_content and self.profile.baseline_config_content.strip())
        if has_config:
            cfg_ok = ("Uygulandı" in self.lbl_cfg_status.text())
            if not cfg_ok:
                reasons.append("Konfigürasyon uygulanmadı")

        force_active = hasattr(self, "chk_force_init") and self.chk_force_init.isChecked()

        if not reasons:
            self.lbl_init_summary.setText("<span style='color: #34d399;'>✓ Tüm sistem ve servis kontrolleri tamamlandı.</span>")
            self.btn_complete_stage2.setText("Faaliyeti Başlat ve Aşama 3'e Geç  ➔")
            self.btn_complete_stage2.setEnabled(True)
            self.btn_complete_stage2.set_variant("success")
        elif force_active:
            self.lbl_init_summary.setText(f"<span style='color: #fbbf24;'>⚠️ Force Aktif: {len(reasons)} eksik kontrole rağmen ilerleniyor</span>")
            self.btn_complete_stage2.setText("⚠️ Doğrulamadan Yine de Başlat  ➔")
            self.btn_complete_stage2.setEnabled(True)
            self.btn_complete_stage2.set_variant("warning")
        else:
            self.lbl_init_summary.setText(f"<span style='color: #fbbf24;'>Bekleyen: {', '.join(reasons)}</span>")
            self.btn_complete_stage2.setText("Faaliyeti Başlat ve Aşama 3'e Geç  ➔")
            self.btn_complete_stage2.setEnabled(False)
            self.btn_complete_stage2.set_variant("primary")

    def _on_complete_stage2(self):
        if not self.btn_complete_stage2.isEnabled():
            return

        reply = QMessageBox.question(
            self,
            "Faaliyeti Başlat",
            "Tüm kontroller tamamlandı ve servisler hazırlandı.\n\n"
            "Faaliyet resmen başlatılsın ve 3. Aşamaya geçilsin mi?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        if reply == QMessageBox.Yes:
            self.console.append_log("2. AŞAMA TAMAMLANDI.", "system")
            if not self.adapter:
                self.adapter = self._get_active_adapter()
            self.stage_completed.emit(self.adapter)
