"""
FieldOps Assistant - Lokasyon Profil Editörü (ProfileEditorDialog)
Kullanıcının YAML/JSON dosyalarına elle dokunmadan yeni hedef istasyonlar eklemesini
veya mevcut lokasyon parametrelerini zengin bir görsel arayüzle düzenlemesini sağlar.
"""

from __future__ import annotations
import json
import re
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPlainTextEdit, QSpinBox, QCheckBox, QScrollArea, QFrame,
    QFileDialog, QMessageBox, QTabWidget, QWidget, QSizePolicy
)

from app.core.models import EquipmentItem, LocationProfile, SoftwareRequirement, TargetDeviceConfig
from app.core.profile_manager import ProfileManager
from app.gui.widgets.touch_button import TouchButton


class SoftwareReqItemCard(QFrame):
    """Yazılım gereksinimi düzenleme satırı."""

    def __init__(self, req: Optional[SoftwareRequirement] = None, on_delete=None, parent=None):
        super().__init__(parent)
        self.on_delete = on_delete
        self.setProperty("class", "ElevatedCard")
        self._setup_ui(req)

    def _setup_ui(self, req: Optional[SoftwareRequirement]):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        # 1. Satır: Paket Adı, Sürüm, Sil Butonu
        row1 = QHBoxLayout()
        row1.setSpacing(10)

        lbl_name = QLabel("Paket / Servis Adı:")
        lbl_name.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 600;")
        self.txt_name = QLineEdit(req.name if req else "")
        self.txt_name.setPlaceholderText("Örn: RadarControlService")
        self.txt_name.setStyleSheet("min-height: 34px;")

        lbl_ver = QLabel("Sürüm:")
        lbl_ver.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 600;")
        self.txt_version = QLineEdit(req.expected_version if req else "1.0.0")
        self.txt_version.setPlaceholderText("Örn: 2.4.0")
        self.txt_version.setFixedWidth(100)
        self.txt_version.setStyleSheet("min-height: 34px;")

        btn_del = TouchButton("🗑", variant="delete")
        btn_del.setFixedSize(32, 32)
        btn_del.setToolTip("Bu Paketi Kaldır")
        if self.on_delete:
            btn_del.clicked.connect(lambda: self.on_delete(self))

        row1.addWidget(lbl_name)
        row1.addWidget(self.txt_name, 2)
        row1.addWidget(lbl_ver)
        row1.addWidget(self.txt_version)
        row1.addWidget(btn_del)
        layout.addLayout(row1)

        # 2. Satır: Arşiv Dosya Adı ve Kurulum Yolu
        row2 = QHBoxLayout()
        row2.setSpacing(10)

        lbl_file = QLabel("Paket Dosya Adı:")
        lbl_file.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 600;")
        self.txt_file = QLineEdit(req.package_filename if req else "")
        self.txt_file.setPlaceholderText("Örn: radar_control_v2.4.0_x86_64.tar.gz")
        self.txt_file.setStyleSheet("min-height: 34px;")

        lbl_path = QLabel("Hedef Kurulum Dizini:")
        lbl_path.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 600;")
        self.txt_path = QLineEdit(req.target_install_path if req else "/opt/app")
        self.txt_path.setStyleSheet("min-height: 34px;")

        row2.addWidget(lbl_file)
        row2.addWidget(self.txt_file, 1)
        row2.addWidget(lbl_path)
        row2.addWidget(self.txt_path, 1)
        layout.addLayout(row2)

        # 3. Satır: Servis Adı ve Versiyon Kontrol Komutu
        row3 = QHBoxLayout()
        row3.setSpacing(10)

        lbl_srv = QLabel("Systemd Servisi:")
        lbl_srv.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 600;")
        self.txt_service = QLineEdit(req.service_name if req and req.service_name else "")
        self.txt_service.setPlaceholderText("Örn: radar_control")
        self.txt_service.setStyleSheet("min-height: 34px;")

        lbl_cmd = QLabel("Versiyon Komutu:")
        lbl_cmd.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 600;")
        self.txt_cmd = QLineEdit(req.version_command if req else "")
        self.txt_cmd.setPlaceholderText("Örn: /opt/app/bin/app --version")
        self.txt_cmd.setStyleSheet("min-height: 34px;")

        row3.addWidget(lbl_srv)
        row3.addWidget(self.txt_service, 1)
        row3.addWidget(lbl_cmd)
        row3.addWidget(self.txt_cmd, 2)
        layout.addLayout(row3)

    def to_model(self) -> Optional[SoftwareRequirement]:
        name = self.txt_name.text().strip()
        if not name:
            return None
        return SoftwareRequirement(
            name=name,
            expected_version=self.txt_version.text().strip() or "1.0.0",
            package_filename=self.txt_file.text().strip() or f"{name.lower()}.tar.gz",
            target_install_path=self.txt_path.text().strip() or "/opt/app",
            service_name=self.txt_service.text().strip() or None,
            version_command=self.txt_cmd.text().strip() or f"/opt/app/bin/{name.lower()} --version"
        )


class EquipmentItemCard(QFrame):
    """Malzeme kontrol listesi satırı."""

    def __init__(self, item: Optional[EquipmentItem] = None, on_delete=None, parent=None):
        super().__init__(parent)
        self.on_delete = on_delete
        self.item_id = item.id if item else f"eq_{int(id(self)) % 10000}"
        self.setProperty("class", "ElevatedCard")
        self._setup_ui(item)

    def _setup_ui(self, item: Optional[EquipmentItem]):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(12)

        lbl_name = QLabel("Malzeme Adı:")
        lbl_name.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 600;")
        self.txt_name = QLineEdit(item.name if item else "")
        self.txt_name.setPlaceholderText("Örn: Yedek Ethernet CAT6 Kablosu (15m)")
        self.txt_name.setStyleSheet("min-height: 34px;")

        lbl_desc = QLabel("Açıklama:")
        lbl_desc.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 600;")
        self.txt_desc = QLineEdit(item.description if item else "")
        self.txt_desc.setPlaceholderText("Örn: Mavi renkli korumalı kablo")
        self.txt_desc.setStyleSheet("min-height: 34px;")

        self.chk_mandatory = QCheckBox("Zorunlu")
        self.chk_mandatory.setChecked(item.is_mandatory if item else True)

        btn_del = TouchButton("🗑", variant="delete")
        btn_del.setFixedSize(32, 32)
        btn_del.setToolTip("Bu Malzemeyi Çıkar")
        if self.on_delete:
            btn_del.clicked.connect(lambda: self.on_delete(self))

        layout.addWidget(lbl_name)
        layout.addWidget(self.txt_name, 2)
        layout.addWidget(lbl_desc)
        layout.addWidget(self.txt_desc, 2)
        layout.addWidget(self.chk_mandatory)
        layout.addWidget(btn_del)

    def to_model(self) -> Optional[EquipmentItem]:
        name = self.txt_name.text().strip()
        if not name:
            return None
        return EquipmentItem(
            id=self.item_id,
            name=name,
            description=self.txt_desc.text().strip(),
            is_mandatory=self.chk_mandatory.isChecked(),
            is_checked=False
        )


class ProfileEditorDialog(QDialog):
    """Zengin, 4 sekmeli modern lokasyon profil editörü modalı."""

    def __init__(
        self,
        profile_manager: ProfileManager,
        profile_to_edit: Optional[LocationProfile] = None,
        parent=None
    ):
        super().__init__(parent)
        self.profile_manager = profile_manager
        self.profile_to_edit = profile_to_edit
        self.is_edit_mode = profile_to_edit is not None
        self.saved_profile_id: Optional[str] = None

        self.sw_cards: List[SoftwareReqItemCard] = []
        self.equip_cards: List[EquipmentItemCard] = []

        self.setWindowTitle(
            f"Lokasyon Profilini Düzenle: {profile_to_edit.name}" if self.is_edit_mode
            else "Yeni Hedef Lokasyon Profili Oluştur"
        )
        self.resize(960, 720)
        self.setMinimumSize(850, 620)
        self._setup_ui()
        self._populate_fields()

    def _setup_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(20, 18, 20, 18)
        root_layout.setSpacing(14)

        # 1. Başlık Banner'ı
        header_frame = QFrame()
        header_frame.setProperty("class", "ModernCard")
        h_layout = QHBoxLayout(header_frame)
        h_layout.setContentsMargins(18, 12, 18, 12)

        icon_lbl = QLabel("⚙️")
        icon_lbl.setStyleSheet("font-size: 24px;")
        h_layout.addWidget(icon_lbl)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title_lbl = QLabel(
            f"Lokasyon Profilini Düzenle ({self.profile_to_edit.id})" if self.is_edit_mode
            else "Yeni Hedef Lokasyon Profili Tanımla"
        )
        title_lbl.setStyleSheet("font-size: 16px; font-weight: 700; color: #f8fafc;")
        title_col.addWidget(title_lbl)

        sub_lbl = QLabel("Bağlantı ayarlarını, yazılım paketlerini, malzeme listesini ve konfigürasyon şablonunu yapılandırın.")
        sub_lbl.setStyleSheet("color: #94a3b8; font-size: 12px;")
        title_col.addWidget(sub_lbl)
        h_layout.addLayout(title_col)
        h_layout.addStretch()

        root_layout.addWidget(header_frame)

        # 2. 4 Sekmeli Ana Tab Yapısı
        self.tabs = QTabWidget()

        self._setup_tab_general()
        self._setup_tab_software()
        self._setup_tab_equipment()
        self._setup_tab_config()

        root_layout.addWidget(self.tabs, 1)

        # 3. Alt Aksiyon Barı
        bottom_bar = QHBoxLayout()
        bottom_bar.setContentsMargins(4, 4, 4, 4)
        bottom_bar.setSpacing(12)

        self.status_lbl = QLabel()
        self.status_lbl.setStyleSheet("color: #f87171; font-size: 13px; font-weight: 600;")
        bottom_bar.addWidget(self.status_lbl)
        bottom_bar.addStretch()

        btn_cancel = TouchButton("Vazgeç", variant="ghost")
        btn_cancel.setFixedHeight(38)
        btn_cancel.setStyleSheet("min-height: 38px; padding: 4px 18px; font-size: 13px;")
        btn_cancel.clicked.connect(self.reject)
        bottom_bar.addWidget(btn_cancel)

        btn_save = TouchButton("✓ Lokasyon Profilini Kaydet", variant="primary")
        btn_save.setFixedHeight(38)
        btn_save.setStyleSheet("min-height: 38px; padding: 4px 22px; font-size: 13px; font-weight: 700;")
        btn_save.clicked.connect(self._on_save_clicked)
        bottom_bar.addWidget(btn_save)

        root_layout.addLayout(bottom_bar)

    def _setup_tab_general(self):
        """Sekme 1: Genel Bilgiler ve Cihaz Ağ/SSH Ayarları."""
        tab = QWidget()
        tab_layout = QHBoxLayout(tab)
        tab_layout.setContentsMargins(10, 10, 10, 10)
        tab_layout.setSpacing(16)

        # SOL: Genel Bilgiler
        left_box = QFrame()
        left_box.setProperty("class", "ElevatedCard")
        left_layout = QVBoxLayout(left_box)
        left_layout.setContentsMargins(16, 14, 16, 14)
        left_layout.setSpacing(10)

        lbl_s1 = QLabel("📍 Genel İstasyon Bilgileri")
        lbl_s1.setStyleSheet("font-size: 14px; font-weight: 700; color: #60a5fa;")
        left_layout.addWidget(lbl_s1)

        left_layout.addWidget(self._make_field_label("Profil Kimliği (ID - Benzersiz):"))
        self.txt_id = QLineEdit()
        self.txt_id.setPlaceholderText("Örn: bursa_gemlik_01")
        if self.is_edit_mode:
            self.txt_id.setEnabled(False)
            self.txt_id.setStyleSheet("color: #64748b; background-color: #080c14;")
        left_layout.addWidget(self.txt_id)

        left_layout.addWidget(self._make_field_label("Lokasyon Adı:"))
        self.txt_name = QLineEdit()
        self.txt_name.setPlaceholderText("Örn: Bursa Gemlik Radar İstasyonu")
        left_layout.addWidget(self.txt_name)

        left_layout.addWidget(self._make_field_label("Açıklama:"))
        self.txt_desc = QLineEdit()
        self.txt_desc.setPlaceholderText("İstasyon tipi, mevki veya görev tanımı...")
        left_layout.addWidget(self.txt_desc)

        left_layout.addWidget(self._make_field_label("Özel Saha / Operatör Notları:"))
        self.txt_notes = QPlainTextEdit()
        self.txt_notes.setPlaceholderText("Örn: Jeneratör faz-2 hattına bağlıdır. Yağışlı havalarda RF kutusunu açmayınız...")
        self.txt_notes.setMaximumHeight(100)
        left_layout.addWidget(self.txt_notes)
        left_layout.addStretch()

        tab_layout.addWidget(left_box, 1)

        # SAĞ: Hedef Cihaz Bağlantı Ayarları
        right_box = QFrame()
        right_box.setProperty("class", "ElevatedCard")
        right_layout = QVBoxLayout(right_box)
        right_layout.setContentsMargins(16, 14, 16, 14)
        right_layout.setSpacing(10)

        lbl_s2 = QLabel("🖥️ Hedef Cihaz & SSH Parametreleri")
        lbl_s2.setStyleSheet("font-size: 14px; font-weight: 700; color: #34d399;")
        right_layout.addWidget(lbl_s2)

        ip_row = QHBoxLayout()
        ip_row.setSpacing(10)

        col_host = QVBoxLayout()
        col_host.addWidget(self._make_field_label("IP / Host Adresi:"))
        self.txt_host = QLineEdit("192.168.1.100")
        col_host.addWidget(self.txt_host)
        ip_row.addLayout(col_host, 3)

        col_port = QVBoxLayout()
        col_port.addWidget(self._make_field_label("SSH Port:"))
        self.spin_port = QSpinBox()
        self.spin_port.setRange(1, 65535)
        self.spin_port.setValue(22)
        col_port.addWidget(self.spin_port)
        ip_row.addLayout(col_port, 1)

        right_layout.addLayout(ip_row)

        user_row = QHBoxLayout()
        user_row.setSpacing(10)

        col_user = QVBoxLayout()
        col_user.addWidget(self._make_field_label("Kullanıcı Adı:"))
        self.txt_user = QLineEdit("root")
        col_user.addWidget(self.txt_user)
        user_row.addLayout(col_user, 1)

        col_pass = QVBoxLayout()
        col_pass.addWidget(self._make_field_label("Şifre (Opsiyonel):"))
        self.txt_pass = QLineEdit()
        self.txt_pass.setEchoMode(QLineEdit.Password)
        self.txt_pass.setPlaceholderText("SSH şifresi...")
        col_pass.addWidget(self.txt_pass)
        user_row.addLayout(col_pass, 1)

        right_layout.addLayout(user_row)

        key_col = QVBoxLayout()
        key_col.addWidget(self._make_field_label("SSH Özel Anahtar Yolu (.pem/.id_rsa):"))
        key_row = QHBoxLayout()
        key_row.setSpacing(8)
        self.txt_key = QLineEdit()
        self.txt_key.setPlaceholderText("Boş bırakılabilir veya anahtar dosyası seçilebilir...")
        btn_browse_key = TouchButton("Seç...", variant="ghost")
        btn_browse_key.setFixedHeight(34)
        btn_browse_key.setStyleSheet("min-height: 32px; padding: 2px 12px; font-size: 12px;")
        btn_browse_key.clicked.connect(self._browse_key_file)
        key_row.addWidget(self.txt_key, 1)
        key_row.addWidget(btn_browse_key)
        key_col.addLayout(key_row)
        right_layout.addLayout(key_col)

        self.chk_local_mode = QCheckBox("Yerel Linux Modu (Uygulama doğrudan hedef Linux'ta çalışır, SSH atlanır)")
        right_layout.addWidget(self.chk_local_mode)

        paths_row = QHBoxLayout()
        paths_row.setSpacing(10)

        col_log = QVBoxLayout()
        col_log.addWidget(self._make_field_label("Uzak Log Dizini:"))
        self.txt_log_dir = QLineEdit("/opt/fieldapp/logs")
        col_log.addWidget(self.txt_log_dir)
        paths_row.addLayout(col_log, 1)

        col_cfg = QVBoxLayout()
        col_cfg.addWidget(self._make_field_label("Uzak Konfigürasyon Yolu:"))
        self.txt_cfg_path = QLineEdit("/opt/fieldapp/config/config.json")
        col_cfg.addWidget(self.txt_cfg_path)
        paths_row.addLayout(col_cfg, 1)

        right_layout.addLayout(paths_row)
        right_layout.addStretch()

        tab_layout.addWidget(right_box, 1)
        self.tabs.addTab(tab, "📍 Genel & Cihaz Bağlantısı")

    def _setup_tab_software(self):
        """Sekme 2: Yazılım Paketleri Gereksinimleri."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        header_row = QHBoxLayout()
        desc = QLabel("Hedef sistemde kontrol edilecek veya yüklenecek yazılım paketleri:")
        desc.setStyleSheet("color: #94a3b8; font-size: 13px;")
        header_row.addWidget(desc)
        header_row.addStretch()

        btn_add = TouchButton("+ Yeni Paket Ekle", variant="primary")
        btn_add.setFixedHeight(34)
        btn_add.setStyleSheet("min-height: 32px; padding: 2px 14px; font-size: 12px; font-weight: 700;")
        btn_add.clicked.connect(lambda: self._add_software_card())
        header_row.addWidget(btn_add)
        layout.addLayout(header_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        self.sw_list_layout = QVBoxLayout(container)
        self.sw_list_layout.setContentsMargins(0, 0, 4, 0)
        self.sw_list_layout.setSpacing(10)
        scroll.setWidget(container)
        layout.addWidget(scroll, 1)

        self.tabs.addTab(tab, "📦 Yazılım Paketleri")

    def _setup_tab_equipment(self):
        """Sekme 3: Saha Ekipmanları Kontrol Listesi."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        header_row = QHBoxLayout()
        desc = QLabel("Saha operasyonuna çıkarken operatörün yanında götürmesi gereken malzemeler:")
        desc.setStyleSheet("color: #94a3b8; font-size: 13px;")
        header_row.addWidget(desc)
        header_row.addStretch()

        btn_add = TouchButton("+ Yeni Malzeme Ekle", variant="primary")
        btn_add.setFixedHeight(34)
        btn_add.setStyleSheet("min-height: 32px; padding: 2px 14px; font-size: 12px; font-weight: 700;")
        btn_add.clicked.connect(lambda: self._add_equipment_card())
        header_row.addWidget(btn_add)
        layout.addLayout(header_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        self.equip_list_layout = QVBoxLayout(container)
        self.equip_list_layout.setContentsMargins(0, 0, 4, 0)
        self.equip_list_layout.setSpacing(10)
        scroll.setWidget(container)
        layout.addWidget(scroll, 1)

        self.tabs.addTab(tab, "🎒 Saha Ekipmanları")

    def _setup_tab_config(self):
        """Sekme 4: Referans Konfigürasyon Şablonu (Baseline Config)."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        header_row = QHBoxLayout()
        desc = QLabel("Bu istasyona ait referans konfigürasyon metni (JSON veya metin):")
        desc.setStyleSheet("color: #94a3b8; font-size: 13px;")
        header_row.addWidget(desc)
        header_row.addStretch()

        btn_sample = TouchButton("📋 Örnek Şablon", variant="ghost")
        btn_sample.setFixedHeight(32)
        btn_sample.setStyleSheet("min-height: 30px; padding: 2px 12px; font-size: 12px;")
        btn_sample.clicked.connect(self._load_sample_config)
        header_row.addWidget(btn_sample)

        btn_format = TouchButton("✨ JSON Formatla & Doğrula", variant="ghost")
        btn_format.setFixedHeight(32)
        btn_format.setStyleSheet("min-height: 30px; padding: 2px 12px; font-size: 12px;")
        btn_format.clicked.connect(self._format_json_config)
        header_row.addWidget(btn_format)

        layout.addLayout(header_row)

        self.txt_baseline_config = QPlainTextEdit()
        self.txt_baseline_config.setPlaceholderText('{\n  "station_id": "STATION_01",\n  "log_level": "INFO"\n}')
        self.txt_baseline_config.setStyleSheet("""
            font-family: 'Cascadia Code', 'Consolas', monospace;
            font-size: 13px;
            line-height: 1.5;
            background-color: #06090f;
            border: 1px solid #1e293b;
            color: #38bdf8;
        """)
        layout.addWidget(self.txt_baseline_config, 1)

        self.cfg_status_lbl = QLabel()
        self.cfg_status_lbl.setStyleSheet("font-size: 12px; color: #64748b;")
        layout.addWidget(self.cfg_status_lbl)

        self.tabs.addTab(tab, "📝 Referans Konfigürasyon")

    def _make_field_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #cbd5e1;")
        return lbl

    def _add_software_card(self, req: Optional[SoftwareRequirement] = None):
        card = SoftwareReqItemCard(req, on_delete=self._remove_software_card)
        self.sw_cards.append(card)
        self.sw_list_layout.addWidget(card)

    def _remove_software_card(self, card: SoftwareReqItemCard):
        if card in self.sw_cards:
            self.sw_cards.remove(card)
            self.sw_list_layout.removeWidget(card)
            card.deleteLater()

    def _add_equipment_card(self, item: Optional[EquipmentItem] = None):
        card = EquipmentItemCard(item, on_delete=self._remove_equipment_card)
        self.equip_cards.append(card)
        self.equip_list_layout.addWidget(card)

    def _remove_equipment_card(self, card: EquipmentItemCard):
        if card in self.equip_cards:
            self.equip_cards.remove(card)
            self.equip_list_layout.removeWidget(card)
            card.deleteLater()

    def _browse_key_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "SSH Özel Anahtar Dosyası Seç",
            "",
            "Anahtar Dosyaları (*.pem *.id_rsa *.key);;Tüm Dosyalar (*.*)"
        )
        if path:
            self.txt_key.setText(path)

    def _load_sample_config(self):
        sample = {
            "station_id": self.txt_id.text().strip().upper() or "STATION-01",
            "log_level": "INFO",
            "telemetry_interval_sec": 5,
            "network": {
                "ip": self.txt_host.text().strip() or "192.168.1.100",
                "port": 8080
            },
            "features": {
                "auto_backup": True,
                "encryption_enabled": True
            }
        }
        self.txt_baseline_config.setPlainText(json.dumps(sample, indent=2, ensure_ascii=False))
        self.cfg_status_lbl.setText("✓ Örnek şablon yüklendi.")
        self.cfg_status_lbl.setStyleSheet("color: #34d399; font-size: 12px;")

    def _format_json_config(self):
        text = self.txt_baseline_config.toPlainText().strip()
        if not text:
            self.cfg_status_lbl.setText("Konfigürasyon boş.")
            self.cfg_status_lbl.setStyleSheet("color: #94a3b8; font-size: 12px;")
            return

        try:
            parsed = json.loads(text)
            formatted = json.dumps(parsed, indent=2, ensure_ascii=False)
            self.txt_baseline_config.setPlainText(formatted)
            self.cfg_status_lbl.setText("✓ JSON formatlandı ve başarıyla doğrulandı.")
            self.cfg_status_lbl.setStyleSheet("color: #34d399; font-size: 12px;")
        except Exception as e:
            self.cfg_status_lbl.setText(f"✕ Geçersiz JSON sözdizimi: {e}")
            self.cfg_status_lbl.setStyleSheet("color: #f87171; font-size: 12px;")

    def _populate_fields(self):
        """Mevcut profil düzenleniyorsa alanları doldurur; yeniyse varsayılanları koyar."""
        if not self.profile_to_edit:
            # Varsayılan 1 paket ve 2 malzeme ile başlat
            self._add_software_card()
            self._add_equipment_card()
            self._load_sample_config()
            return

        p = self.profile_to_edit
        self.txt_id.setText(p.id)
        self.txt_name.setText(p.name)
        self.txt_desc.setText(p.description)
        self.txt_notes.setPlainText(p.custom_notes)

        td = p.target_device
        self.txt_host.setText(td.host)
        self.spin_port.setValue(td.port)
        self.txt_user.setText(td.username)
        if td.password:
            self.txt_pass.setText(td.password)
        if td.key_path:
            self.txt_key.setText(td.key_path)
        self.chk_local_mode.setChecked(td.use_local_mode)
        self.txt_log_dir.setText(td.remote_log_dir)
        self.txt_cfg_path.setText(td.remote_config_path)

        for sw in p.software_requirements:
            self._add_software_card(sw)

        for eq in p.equipment_checklist:
            self._add_equipment_card(eq)

        self.txt_baseline_config.setPlainText(p.baseline_config_content)

    def _on_save_clicked(self):
        """Formu doğrular ve profili YAML olarak kaydeder."""
        self.status_lbl.setText("")

        profile_id = self.txt_id.text().strip().lower()
        name = self.txt_name.text().strip()
        host = self.txt_host.text().strip()
        user = self.txt_user.text().strip()

        # Doğrulamalar
        if not profile_id:
            self.status_lbl.setText("Lütfen benzersiz bir Profil Kimliği (ID) giriniz.")
            self.tabs.setCurrentIndex(0)
            self.txt_id.setFocus()
            return

        if not re.match(r"^[a-z0-9_\-]+$", profile_id):
            self.status_lbl.setText("Profil Kimliği yalnızca küçük harf, rakam ve alt çizgi içerebilir.")
            self.tabs.setCurrentIndex(0)
            self.txt_id.setFocus()
            return

        if not self.is_edit_mode and self.profile_manager.profile_exists(profile_id):
            self.status_lbl.setText(f"'{profile_id}' kimliğine sahip bir profil zaten mevcut!")
            self.tabs.setCurrentIndex(0)
            self.txt_id.setFocus()
            return

        if not name:
            self.status_lbl.setText("Lütfen Lokasyon Adını giriniz.")
            self.tabs.setCurrentIndex(0)
            self.txt_name.setFocus()
            return

        if not host:
            self.status_lbl.setText("Hedef cihaz IP veya Host adresi boş bırakılamaz.")
            self.tabs.setCurrentIndex(0)
            self.txt_host.setFocus()
            return

        # Yazılım ve Malzeme listelerini topla
        sw_list = [card.to_model() for card in self.sw_cards if card.to_model() is not None]
        eq_list = [card.to_model() for card in self.equip_cards if card.to_model() is not None]

        # Konfigürasyon metni
        cfg_content = self.txt_baseline_config.toPlainText().strip()
        if not cfg_content:
            cfg_content = "{}"

        # TargetDeviceConfig oluştur
        target_device = TargetDeviceConfig(
            host=host,
            port=self.spin_port.value(),
            username=user or "root",
            password=self.txt_pass.text() or None,
            key_path=self.txt_key.text().strip() or None,
            use_local_mode=self.chk_local_mode.isChecked(),
            remote_log_dir=self.txt_log_dir.text().strip() or "/opt/fieldapp/logs",
            remote_config_path=self.txt_cfg_path.text().strip() or "/opt/fieldapp/config/config.json",
        )

        # LocationProfile nesnesi
        profile = LocationProfile(
            id=profile_id,
            name=name,
            description=self.txt_desc.text().strip(),
            target_device=target_device,
            equipment_checklist=eq_list,
            software_requirements=sw_list,
            baseline_config_content=cfg_content,
            custom_notes=self.txt_notes.toPlainText().strip(),
        )

        try:
            saved_path = self.profile_manager.save_profile(profile)
            self.saved_profile_id = profile.id
            QMessageBox.information(
                self,
                "Profil Kaydedildi",
                f"'{profile.name}' lokasyon profili başarıyla kaydedildi:\n{saved_path.name}"
            )
            self.accept()
        except Exception as e:
            self.status_lbl.setText(f"Kaydetme hatası: {e}")

