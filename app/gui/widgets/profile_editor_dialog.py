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
    QFileDialog, QMessageBox, QTabWidget, QWidget, QSizePolicy,
    QComboBox
)

from app.core.asset_manager import SoftwareAssetManager
from app.core.equipment_manager import EquipmentCatalogItem, EquipmentCatalogManager
from app.core.models import (
    EquipmentItem, LocationProfile, SoftwareRequirement,
    StoredSoftwareInfo, TargetDeviceConfig
)
from app.core.profile_manager import ProfileManager
from app.gui.widgets.equipment_catalog_dialog import EquipmentCatalogDialog
from app.gui.widgets.touch_button import TouchButton


class ScannedSoftwareCard(QFrame):
    """Hafızadaki hazır yazılımları gösteren tıklanabilir kompakt seçim kartı."""

    def __init__(self, item: StoredSoftwareInfo, on_clicked, parent=None):
        super().__init__(parent)
        self.item = item
        self.on_clicked = on_clicked
        self._is_selected = False
        self.setCursor(Qt.PointingHandCursor)
        self._update_style()
        self._setup_ui()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.on_clicked(self.item)
        super().mousePressEvent(event)

    def set_selected(self, selected: bool):
        self._is_selected = selected
        self._update_style()

    def _update_style(self):
        if self._is_selected:
            self.setStyleSheet("""
                QFrame {
                    background-color: #132238;
                    border: 1.5px solid #3b82f6;
                    border-radius: 8px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: #0b1120;
                    border: 1px solid #1e293b;
                    border-radius: 8px;
                }
                QFrame:hover {
                    border-color: #3b82f6;
                    background-color: #0d1527;
                }
            """)

    def _setup_ui(self):
        row = QHBoxLayout(self)
        row.setContentsMargins(12, 9, 12, 9)
        row.setSpacing(12)

        name_lbl = QLabel(f"<b>{self.item.app_name}</b> <span style='color: #38bdf8;'>({self.item.version_name})</span>")
        name_lbl.setStyleSheet("font-size: 13px; color: #f8fafc;")
        name_lbl.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        row.addWidget(name_lbl)

        file_lbl = QLabel(f"<code>{self.item.primary_package or 'Paket Dosyası Yok'}</code>")
        file_lbl.setStyleSheet("color: #94a3b8; font-size: 12px;")
        file_lbl.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        row.addWidget(file_lbl)

        row.addStretch()

        if not self.item.is_empty:
            badge = QLabel(f"✓ {self.item.formatted_size}")
            badge.setProperty("class", "PillBadge PillSuccess")
        else:
            badge = QLabel("Boş")
            badge.setProperty("class", "PillBadge PillWarning")
        badge.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        row.addWidget(badge)


class AddSoftwareDialog(QDialog):
    """Yeni yazılım paketi ekleme ve yapılandırma modalı.
    
    Welcome page'de taranıp tespit edilen yazılımları listeler,
    kullanıcı birini seçtiğinde alanları otomatik doldurur ve aynı zamanda
    tüm alanların manuel olarak elle yazılmasına/düzenlenmesine izin verir.
    """

    def __init__(
        self,
        asset_manager: Optional[SoftwareAssetManager] = None,
        initial_req: Optional[SoftwareRequirement] = None,
        parent=None
    ):
        super().__init__(parent)
        self.asset_manager = asset_manager or SoftwareAssetManager()
        self.initial_req = initial_req
        self.result_requirement: Optional[SoftwareRequirement] = None
        self.scanned_items: List[StoredSoftwareInfo] = self.asset_manager.scan_available_softwares()
        self.scanned_card_widgets: List[ScannedSoftwareCard] = []
        self._is_adv_expanded: bool = False

        self.setWindowTitle("Yazılım Paketi Ekle & Yapılandır")
        self.resize(760, 680)
        self.setMinimumSize(600, 480)
        self._setup_ui()

        # Default olarak ilk açıldığında manuel giriş seçili gelir
        if initial_req:
            self._fill_form_from_req(initial_req)
        else:
            self._set_manual_mode()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        # 1. Başlık Banner
        header = QFrame()
        header.setProperty("class", "ModernCard")
        h_box = QHBoxLayout(header)
        h_box.setContentsMargins(16, 12, 16, 12)
        h_box.setSpacing(12)

        icon_lbl = QLabel("")
        icon_lbl.setStyleSheet("font-size: 26px;")
        h_box.addWidget(icon_lbl)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title_lbl = QLabel("Yazılım Paketi Ekle & Yapılandır")
        title_lbl.setStyleSheet("font-size: 16px; font-weight: 700; color: #f8fafc;")
        title_col.addWidget(title_lbl)

        sub_lbl = QLabel("Hafızadaki (softwares/) hazır paketlerden seçebilir veya tamamen elle yeni bir paket tanımlayabilirsiniz.")
        sub_lbl.setStyleSheet("color: #94a3b8; font-size: 12px;")
        title_col.addWidget(sub_lbl)
        h_box.addLayout(title_col)
        h_box.addStretch()
        layout.addWidget(header)

        # =====================================================================
        # KAYDIRILABİLİR İÇERİK ALANI (Form elemanlarının iç içe girmesini önler)
        # =====================================================================
        self.body_scroll = QScrollArea()
        self.body_scroll.setWidgetResizable(True)
        self.body_scroll.setFrameShape(QFrame.NoFrame)
        self.body_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.body_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        scroll_content = QWidget()
        scroll_content_layout = QVBoxLayout(scroll_content)
        scroll_content_layout.setContentsMargins(0, 4, 8, 4)
        scroll_content_layout.setSpacing(14)

        # 2. ÜST BÖLÜM: Hafızadaki Tespit Edilen Yazılımlar
        scanned_card = QFrame()
        scanned_card.setProperty("class", "ElevatedCard")
        scanned_layout = QVBoxLayout(scanned_card)
        scanned_layout.setContentsMargins(16, 14, 16, 14)
        scanned_layout.setSpacing(10)

        top_row = QHBoxLayout()
        lbl_scanned_title = QLabel("Hafızada Tespit Edilen Yazılımlar (Welcome Page):")
        lbl_scanned_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #60a5fa;")
        top_row.addWidget(lbl_scanned_title)
        top_row.addStretch()

        btn_manual_clear = TouchButton("Formu Temizle (Manuel Giriş)", variant="ghost")
        btn_manual_clear.setFixedHeight(30)
        btn_manual_clear.setStyleSheet("font-size: 12px; padding: 2px 12px; min-height: 28px;")
        btn_manual_clear.clicked.connect(self._set_manual_mode)
        top_row.addWidget(btn_manual_clear)
        scanned_layout.addLayout(top_row)

        # Açılır Kutu (ComboBox)
        self.combo_scanned = QComboBox()
        self.combo_scanned.setFixedHeight(38)
        self.combo_scanned.setStyleSheet("font-size: 13px; padding: 4px 12px;")
        self.combo_scanned.addItem("[Manuel Giriş] — Özel / Farklı bir paket tanımla (Elle Yaz)", None)

        for it in self.scanned_items:
            status_str = "✓ Hazır" if not it.is_empty else " Boş Klasör"
            size_str = f" ({it.formatted_size})" if not it.is_empty else ""
            file_str = f" — {it.primary_package}" if it.primary_package else ""
            self.combo_scanned.addItem(
                f" {it.app_name} ({it.version_name}){file_str}{size_str} [{status_str}]",
                it
            )
        self.combo_scanned.currentIndexChanged.connect(self._on_combo_selection_changed)
        scanned_layout.addWidget(self.combo_scanned)

        # Hızlı Seçim Listesi (Görsel ve Tıklanabilir Kartlar)
        scanned_list_layout = QVBoxLayout()
        scanned_list_layout.setContentsMargins(0, 2, 0, 2)
        scanned_list_layout.setSpacing(6)

        self.scanned_card_widgets = []
        if self.scanned_items:
            for it in self.scanned_items:
                card = ScannedSoftwareCard(it, on_clicked=self._select_scanned_item)
                self.scanned_card_widgets.append(card)
                scanned_list_layout.addWidget(card)
        else:
            no_item_lbl = QLabel("softwares/ dizininde henüz kayıtlı paket tespit edilemedi.<br>Aşağıdaki formdan manuel olarak paket tanımlayabilirsiniz.")
            no_item_lbl.setStyleSheet("color: #94a3b8; font-size: 12px; padding: 12px;")
            no_item_lbl.setAlignment(Qt.AlignCenter)
            scanned_list_layout.addWidget(no_item_lbl)

        scanned_layout.addLayout(scanned_list_layout)

        # Durum Bilgi Satırı
        self.lbl_source_status = QLabel()
        self.lbl_source_status.setStyleSheet("font-size: 12px; color: #94a3b8;")
        scanned_layout.addWidget(self.lbl_source_status)

        scroll_content_layout.addWidget(scanned_card)

        # 3. ORTA BÖLÜM: Form Alanları (Manuel Düzenlenebilir)
        form_card = QFrame()
        form_card.setProperty("class", "ElevatedCard")
        form_layout = QVBoxLayout(form_card)
        form_layout.setContentsMargins(16, 14, 16, 14)
        form_layout.setSpacing(10)

        lbl_form_title = QLabel("📝 Paket Parametreleri (Serbestçe Düzenlenebilir):")
        lbl_form_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #34d399;")
        form_layout.addWidget(lbl_form_title)

        # Satır 1: Paket Adı & Sürüm
        row1 = QHBoxLayout()
        row1.setSpacing(12)

        col_name = QVBoxLayout()
        col_name.setSpacing(4)
        lbl_name = QLabel("Paket / Servis Adı:")
        lbl_name.setStyleSheet("font-size: 12px; font-weight: 600; color: #cbd5e1;")
        self.txt_name = QLineEdit()
        self.txt_name.setPlaceholderText("Örn: radar_control veya RadarControlService")
        self.txt_name.setStyleSheet("min-height: 36px;")
        col_name.addWidget(lbl_name)
        col_name.addWidget(self.txt_name)
        row1.addLayout(col_name, 2)

        col_ver = QVBoxLayout()
        col_ver.setSpacing(4)
        lbl_ver = QLabel("Beklenen Sürüm:")
        lbl_ver.setStyleSheet("font-size: 12px; font-weight: 600; color: #cbd5e1;")
        self.txt_version = QLineEdit("1.0.0")
        self.txt_version.setPlaceholderText("Örn: 2.4.0")
        self.txt_version.setStyleSheet("min-height: 36px;")
        col_ver.addWidget(lbl_ver)
        col_ver.addWidget(self.txt_version)
        row1.addLayout(col_ver, 1)

        form_layout.addLayout(row1)

        # Satır 2: Paket Dosya Adı (Arşiv) & Gözat
        lbl_file = QLabel("Paket Dosya Adı (Arşiv .tar.gz / .zip / .bin):")
        lbl_file.setStyleSheet("font-size: 12px; font-weight: 600; color: #cbd5e1;")
        form_layout.addWidget(lbl_file)

        row_file = QHBoxLayout()
        row_file.setSpacing(8)
        self.txt_file = QLineEdit()
        self.txt_file.setPlaceholderText("Örn: radar_control_v2.4.0_x86_64.tar.gz")
        self.txt_file.setStyleSheet("min-height: 36px;")
        btn_browse_file = TouchButton("Dosya Seç...", variant="ghost")
        btn_browse_file.setFixedHeight(36)
        btn_browse_file.setStyleSheet("min-height: 34px; padding: 2px 14px; font-size: 12px;")
        btn_browse_file.clicked.connect(self._browse_external_file)
        row_file.addWidget(self.txt_file, 1)
        row_file.addWidget(btn_browse_file)
        form_layout.addLayout(row_file)

        # Gelişmiş Parametreler (Progressive Disclosure - Akordiyon Yapısı)
        self.btn_toggle_adv = TouchButton("▶ Gelişmiş Parametreleri Göster (Kurulum Dizini, Servis, Komut)", variant="ghost")
        self.btn_toggle_adv.setFixedHeight(34)
        self.btn_toggle_adv.setStyleSheet(
            "min-height: 32px; font-size: 12px; font-weight: 600; text-align: left; "
            "padding: 4px 12px; color: #38bdf8; border: 1px dashed rgba(56, 189, 248, 0.35); border-radius: 8px;"
        )
        self.btn_toggle_adv.clicked.connect(self._toggle_advanced_settings)
        form_layout.addWidget(self.btn_toggle_adv)

        self.adv_container = QWidget()
        adv_layout = QVBoxLayout(self.adv_container)
        adv_layout.setContentsMargins(0, 4, 0, 0)
        adv_layout.setSpacing(10)

        # Satır 3: Hedef Kurulum Yolu & Systemd Servisi
        row3 = QHBoxLayout()
        row3.setSpacing(12)

        col_path = QVBoxLayout()
        col_path.setSpacing(4)
        lbl_path = QLabel("Hedef Kurulum Dizini (Linux):")
        lbl_path.setStyleSheet("font-size: 12px; font-weight: 600; color: #cbd5e1;")
        self.txt_path = QLineEdit("/opt/app")
        self.txt_path.setStyleSheet("min-height: 36px;")
        col_path.addWidget(lbl_path)
        col_path.addWidget(self.txt_path)
        row3.addLayout(col_path, 1)

        col_srv = QVBoxLayout()
        col_srv.setSpacing(4)
        lbl_srv = QLabel("Systemd Servis Adı (Opsiyonel):")
        lbl_srv.setStyleSheet("font-size: 12px; font-weight: 600; color: #cbd5e1;")
        self.txt_service = QLineEdit()
        self.txt_service.setPlaceholderText("Örn: radar_control")
        self.txt_service.setStyleSheet("min-height: 36px;")
        col_srv.addWidget(lbl_srv)
        col_srv.addWidget(self.txt_service)
        row3.addLayout(col_srv, 1)

        adv_layout.addLayout(row3)

        # Satır 4: Sürüm Kontrol Komutu
        lbl_cmd = QLabel("Cihazda Sürüm Kontrol Komutu:")
        lbl_cmd.setStyleSheet("font-size: 12px; font-weight: 600; color: #cbd5e1;")
        self.txt_cmd = QLineEdit("/opt/app/bin/app --version")
        self.txt_cmd.setStyleSheet("min-height: 36px;")
        adv_layout.addWidget(lbl_cmd)
        adv_layout.addWidget(self.txt_cmd)

        self.adv_container.setVisible(False)
        form_layout.addWidget(self.adv_container)

        scroll_content_layout.addWidget(form_card)
        scroll_content_layout.addStretch(1)

        self.body_scroll.setWidget(scroll_content)
        layout.addWidget(self.body_scroll, 1)

        # 4. Alt Aksiyon Barı (Sabit ve daima görünür)
        bottom_bar = QHBoxLayout()
        bottom_bar.setSpacing(12)

        self.lbl_error = QLabel()
        self.lbl_error.setStyleSheet("color: #f87171; font-size: 12px; font-weight: 600;")
        bottom_bar.addWidget(self.lbl_error)
        bottom_bar.addStretch()

        btn_cancel = TouchButton("Vazgeç", variant="ghost")
        btn_cancel.setFixedHeight(38)
        btn_cancel.setStyleSheet("min-height: 36px; padding: 2px 18px; font-size: 13px;")
        btn_cancel.clicked.connect(self.reject)
        bottom_bar.addWidget(btn_cancel)

        btn_add = TouchButton("✓ Paketi Ekle", variant="primary")
        btn_add.setFixedHeight(38)
        btn_add.setStyleSheet("min-height: 36px; padding: 2px 22px; font-size: 13px; font-weight: 700;")
        btn_add.clicked.connect(self._on_add_clicked)
        bottom_bar.addWidget(btn_add)

        layout.addLayout(bottom_bar)

    def _toggle_advanced_settings(self):
        self._is_adv_expanded = not self._is_adv_expanded
        self.adv_container.setVisible(self._is_adv_expanded)
        if self._is_adv_expanded:
            self.btn_toggle_adv.setText("▼ Gelişmiş Parametreleri Gizle (Kurulum Dizini, Servis, Komut)")
        else:
            self.btn_toggle_adv.setText("▶ Gelişmiş Parametreleri Göster (Kurulum Dizini, Servis, Komut)")

    def _select_scanned_item(self, item: StoredSoftwareInfo):
        for card in getattr(self, "scanned_card_widgets", []):
            card.set_selected(card.item == item)
        for i in range(1, self.combo_scanned.count()):
            if self.combo_scanned.itemData(i) == item:
                self.combo_scanned.blockSignals(True)
                self.combo_scanned.setCurrentIndex(i)
                self.combo_scanned.blockSignals(False)
                break
        self._fill_form_from_scanned(item)

    def _on_combo_selection_changed(self, index: int):
        data = self.combo_scanned.currentData()
        if data is None:
            self._set_manual_mode()
        else:
            self._select_scanned_item(data)

    def _set_manual_mode(self):
        for card in getattr(self, "scanned_card_widgets", []):
            card.set_selected(False)
        self.combo_scanned.blockSignals(True)
        self.combo_scanned.setCurrentIndex(0)
        self.combo_scanned.blockSignals(False)

        # Paket parametreleri alanlarını temizle
        self.txt_name.clear()
        self.txt_version.setText("1.0.0")
        self.txt_file.clear()
        self.txt_path.setText("/opt/app")
        self.txt_service.clear()
        self.txt_cmd.setText("/opt/app/bin/app --version")

        # Gelişmiş ayarları daralt
        if getattr(self, "_is_adv_expanded", False):
            self._toggle_advanced_settings()

        self.lbl_source_status.setText("Manuel Mod: İstediğiniz paket bilgilerini aşağıdaki formdan serbestçe tanımlayabilirsiniz.")
        self.lbl_source_status.setStyleSheet("color: #38bdf8; font-size: 12px;")
        self.lbl_error.clear()
        self.txt_name.setFocus()

    def _fill_form_from_scanned(self, item: StoredSoftwareInfo):
        self.lbl_error.clear()
        clean_version = item.version_name.lstrip("v") if item.version_name.startswith("v") else item.version_name
        self.txt_name.setText(item.app_name)
        self.txt_version.setText(clean_version or "1.0.0")

        if item.primary_package:
            self.txt_file.setText(item.primary_package)
        else:
            self.txt_file.setText(f"{item.app_name}_{item.version_name}.tar.gz")

        install_path = f"/opt/{item.app_name}"
        self.txt_path.setText(install_path)
        self.txt_service.setText(item.app_name)
        self.txt_cmd.setText(f"{install_path}/bin/{item.app_name} --version")

        if item.is_empty:
            self.lbl_source_status.setText(
                f" Dikkat: Bu versiyon klasörü (softwares/{item.relative_path}) henüz boş. "
                f"Paket dosyasını daha sonra klasöre ekleyebilirsiniz."
            )
            self.lbl_source_status.setStyleSheet("color: #fbbf24; font-size: 12px;")
        else:
            self.lbl_source_status.setText(
                f"✓ Hafızada Hazır: softwares/{item.relative_path}/{item.primary_package} ({item.formatted_size})"
            )
            self.lbl_source_status.setStyleSheet("color: #34d399; font-size: 12px;")

    def _fill_form_from_req(self, req: SoftwareRequirement):
        self.txt_name.setText(req.name)
        self.txt_version.setText(req.expected_version)
        self.txt_file.setText(req.package_filename)
        self.txt_path.setText(req.target_install_path)
        self.txt_service.setText(req.service_name or "")
        self.txt_cmd.setText(req.version_command)

        # Eğer özel servis adı veya standart dışı kurulum yolu varsa gelişmiş ayarları otomatik aç
        if req.service_name or (req.target_install_path and req.target_install_path != f"/opt/{req.name.lower()}"):
            self._is_adv_expanded = True
            self.adv_container.setVisible(True)
            self.btn_toggle_adv.setText("▼ Gelişmiş Parametreleri Gizle (Kurulum Dizini, Servis, Komut)")

        match_idx = -1
        matched_item = None
        for i in range(1, self.combo_scanned.count()):
            it = self.combo_scanned.itemData(i)
            if it and (it.primary_package == req.package_filename or it.app_name.lower() == req.name.lower()):
                match_idx = i
                matched_item = it
                break
        if match_idx >= 0:
            for card in getattr(self, "scanned_card_widgets", []):
                card.set_selected(card.item == matched_item)
            self.combo_scanned.blockSignals(True)
            self.combo_scanned.setCurrentIndex(match_idx)
            self.combo_scanned.blockSignals(False)
            self.lbl_source_status.setText("✓ Hafızadaki eşleşen paket seçildi.")
            self.lbl_source_status.setStyleSheet("color: #34d399; font-size: 12px;")
        else:
            for card in getattr(self, "scanned_card_widgets", []):
                card.set_selected(False)
            self.combo_scanned.blockSignals(True)
            self.combo_scanned.setCurrentIndex(0)
            self.combo_scanned.blockSignals(False)
            self.lbl_source_status.setText("Manuel Mod: Özel paket yapılandırması.")
            self.lbl_source_status.setStyleSheet("color: #38bdf8; font-size: 12px;")

    def _browse_external_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Paket Arşiv Dosyası Seç",
            str(self.asset_manager.packages_dir),
            "Paket Arşivleri (*.tar.gz *.tgz *.zip *.bin *.exe);;Tüm Dosyalar (*.*)"
        )
        if path:
            p = Path(path)
            self.txt_file.setText(p.name)

    def _on_add_clicked(self):
        name = self.txt_name.text().strip()
        version = self.txt_version.text().strip()
        file_name = self.txt_file.text().strip()

        if not name:
            self.lbl_error.setText("✕ Lütfen paket adını girin.")
            self.txt_name.setFocus()
            return
        if not file_name:
            self.lbl_error.setText("✕ Lütfen paket dosya adını girin.")
            self.txt_file.setFocus()
            return

        self.result_requirement = SoftwareRequirement(
            name=name,
            expected_version=version or "1.0.0",
            package_filename=file_name,
            target_install_path=self.txt_path.text().strip() or f"/opt/{name.lower()}",
            service_name=self.txt_service.text().strip() or None,
            version_command=self.txt_cmd.text().strip() or f"/opt/{name.lower()}/bin/{name.lower()} --version"
        )
        self.accept()

    def get_software_requirement(self) -> Optional[SoftwareRequirement]:
        return self.result_requirement


class SoftwareReqItemCard(QFrame):
    """Yazılım gereksinimi düzenleme satırı."""

    def __init__(
        self,
        req: Optional[SoftwareRequirement] = None,
        on_delete=None,
        asset_manager: Optional[SoftwareAssetManager] = None,
        parent=None
    ):
        super().__init__(parent)
        self.on_delete = on_delete
        self.asset_manager = asset_manager
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

        btn_fill = TouchButton("Hafızadan Doldur...", variant="ghost")
        btn_fill.setFixedHeight(32)
        btn_fill.setStyleSheet("min-height: 30px; padding: 2px 10px; font-size: 12px;")
        btn_fill.setToolTip("Hafızadaki (softwares/) paketlerden seçerek bu kartın alanlarını otomatik doldurur")
        btn_fill.clicked.connect(self._open_fill_dialog)

        btn_del = TouchButton("Sil", variant="delete")
        btn_del.setFixedSize(32, 32)
        btn_del.setToolTip("Bu Paketi Kaldır")
        if self.on_delete:
            btn_del.clicked.connect(lambda: self.on_delete(self))

        row1.addWidget(lbl_name)
        row1.addWidget(self.txt_name, 2)
        row1.addWidget(lbl_ver)
        row1.addWidget(self.txt_version)
        row1.addWidget(btn_fill)
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

    def _open_fill_dialog(self):
        dlg = AddSoftwareDialog(self.asset_manager, initial_req=self.to_model(), parent=self)
        if dlg.exec():
            selected = dlg.get_software_requirement()
            if selected:
                self.fill_from_model(selected)

    def fill_from_model(self, req: SoftwareRequirement):
        self.txt_name.setText(req.name)
        self.txt_version.setText(req.expected_version)
        self.txt_file.setText(req.package_filename)
        self.txt_path.setText(req.target_install_path)
        self.txt_service.setText(req.service_name or "")
        self.txt_cmd.setText(req.version_command)

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

    def __init__(
        self,
        item: Optional[EquipmentItem] = None,
        on_delete=None,
        parent=None
    ):
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

        btn_del = TouchButton("Sil", variant="delete")
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
        asset_manager: Optional[SoftwareAssetManager] = None,
        equipment_manager: Optional[EquipmentCatalogManager] = None,
        parent=None
    ):
        super().__init__(parent)
        self.profile_manager = profile_manager
        self.profile_to_edit = profile_to_edit
        self.asset_manager = asset_manager or SoftwareAssetManager()
        self.equipment_manager = equipment_manager or EquipmentCatalogManager()
        self.is_edit_mode = profile_to_edit is not None
        self.saved_profile_id: Optional[str] = None

        self.sw_cards: List[SoftwareReqItemCard] = []
        self.equip_cards: List[EquipmentItemCard] = []

        self.setWindowTitle(
            f"Lokasyon Profilini Düzenle: {profile_to_edit.name}" if self.is_edit_mode
            else "Yeni Hedef Lokasyon Profili Oluştur"
        )
        self.resize(900, 620)
        self.setMinimumSize(760, 480)
        self._setup_ui()
        self._populate_fields()

    def _setup_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(18, 14, 18, 14)
        root_layout.setSpacing(10)

        # 1. Başlık Banner'ı
        header_frame = QFrame()
        header_frame.setProperty("class", "ModernCard")
        h_layout = QHBoxLayout(header_frame)
        h_layout.setContentsMargins(16, 10, 16, 10)

        icon_lbl = QLabel("")
        icon_lbl.setStyleSheet("font-size: 24px;")
        h_layout.addWidget(icon_lbl)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title_lbl = QLabel(
            f"Lokasyon Profilini Düzenle ({self.profile_to_edit.id})" if self.is_edit_mode
            else "Yeni Hedef Lokasyon Profili Tanımla"
        )
        title_lbl.setStyleSheet("font-size: 15px; font-weight: 700; color: #f8fafc;")
        title_col.addWidget(title_lbl)

        sub_lbl = QLabel("Bağlantı ayarlarını, yazılım paketlerini, malzeme listesini ve konfigürasyon şablonunu yapılandırın.")
        sub_lbl.setStyleSheet("color: #94a3b8; font-size: 11.5px;")
        sub_lbl.setWordWrap(True)
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
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        tab_layout = QHBoxLayout(container)
        tab_layout.setContentsMargins(10, 10, 10, 10)
        tab_layout.setSpacing(16)

        # SOL: Genel Bilgiler
        left_box = QFrame()
        left_box.setProperty("class", "ElevatedCard")
        left_layout = QVBoxLayout(left_box)
        left_layout.setContentsMargins(16, 14, 16, 14)
        left_layout.setSpacing(10)

        lbl_s1 = QLabel("Genel İstasyon Bilgileri")
        lbl_s1.setStyleSheet("font-size: 14px; font-weight: 700; color: #60a5fa;")
        left_layout.addWidget(lbl_s1)

        # Yeni profil oluşturuluyorsa: Var olan lokasyondan kopyalama seçeneği
        if not self.is_edit_mode:
            clone_box = QFrame()
            clone_box.setStyleSheet("""
                QFrame {
                    background-color: #0b1120;
                    border: 1px dashed rgba(56, 189, 248, 0.4);
                    border-radius: 8px;
                    padding: 4px 6px;
                }
            """)
            c_vbox = QVBoxLayout(clone_box)
            c_vbox.setContentsMargins(6, 6, 6, 6)
            c_vbox.setSpacing(5)

            lbl_c_title = QLabel("Şablondan Doldur (İsteğe Bağlı):")
            lbl_c_title.setStyleSheet("font-size: 11.5px; font-weight: 600; color: #38bdf8;")
            c_vbox.addWidget(lbl_c_title)

            c_row = QHBoxLayout()
            c_row.setSpacing(6)

            self.combo_clone = QComboBox()
            self.combo_clone.setFixedHeight(30)
            self.combo_clone.setStyleSheet("font-size: 12px; min-height: 28px;")
            self.combo_clone.addItem("-- Var Olan Lokasyondan Seç --", None)

            existing_profiles = self.profile_manager.list_profiles()
            for p in existing_profiles:
                self.combo_clone.addItem(f"{p.name}", p.id)

            self.combo_clone.currentIndexChanged.connect(self._on_clone_combo_changed)
            c_row.addWidget(self.combo_clone, 1)

            btn_clone = TouchButton("Doldur", variant="ghost")
            btn_clone.setFixedHeight(30)
            btn_clone.setStyleSheet("min-height: 28px; font-size: 11.5px; font-weight: 600; padding: 2px 10px; color: #38bdf8; border-color: rgba(56, 189, 248, 0.4);")
            btn_clone.setToolTip("Seçili lokasyonun ayarlarını (isim hariç) bu forma aktarır")
            btn_clone.clicked.connect(self._apply_clone_from_selected)
            c_row.addWidget(btn_clone)

            c_vbox.addLayout(c_row)
            left_layout.addWidget(clone_box)

        left_layout.addWidget(self._make_field_label("Profil Kimliği (ID - Benzersiz):"))
        self.txt_id = QLineEdit()
        self.txt_id.setPlaceholderText("Örn: bursa_gemlik_01")
        if self.is_edit_mode:
            self.txt_id.setEnabled(False)
            self.txt_id.setStyleSheet("color: #94a3b8; background-color: #080c14;")
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

        lbl_s2 = QLabel("Hedef Cihaz & SSH Parametreleri")
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

        self.chk_local_mode = QCheckBox("Yerel Linux Modu (SSH atlanır)")
        self.chk_local_mode.setToolTip("Uygulama doğrudan hedef Linux cihazında çalışıyorsa işaretleyin, SSH bağlantısı atlanır.")
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

        scroll.setWidget(container)
        self.tabs.addTab(scroll, " Genel & Cihaz Bağlantısı")

    def _setup_tab_software(self):
        """Sekme 2: Yazılım Paketleri Gereksinimleri."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        header_row = QHBoxLayout()
        desc = QLabel("Hedef sistemde kontrol edilecek veya yüklenecek yazılım paketleri:")
        desc.setStyleSheet("color: #94a3b8; font-size: 13px;")
        desc.setWordWrap(True)
        header_row.addWidget(desc)
        header_row.addStretch()

        btn_add = TouchButton("+ Yeni Paket Ekle...", variant="primary")
        btn_add.setFixedHeight(34)
        btn_add.setStyleSheet("min-height: 32px; padding: 2px 14px; font-size: 12.5px; font-weight: 700;")
        btn_add.setToolTip("Hafızadaki (softwares/) hazır paketleri listeleyip seçin veya manuel paket ekleyin")
        btn_add.clicked.connect(self._open_add_software_dialog)
        header_row.addWidget(btn_add)

        btn_manual = TouchButton("Hızlı Boş Kart", variant="ghost")
        btn_manual.setFixedHeight(34)
        btn_manual.setStyleSheet("min-height: 32px; padding: 2px 12px; font-size: 12px;")
        btn_manual.setToolTip("Doğrudan elle yazabileceğiniz boş bir düzenleme kartı ekler")
        btn_manual.clicked.connect(lambda: self._add_software_card())
        header_row.addWidget(btn_manual)
        layout.addLayout(header_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        self.sw_list_layout = QVBoxLayout(container)
        self.sw_list_layout.setContentsMargins(0, 0, 4, 0)
        self.sw_list_layout.setSpacing(10)

        self.sw_empty_lbl = QLabel(
            "📦 Henüz bu profile yazılım paketi eklenmedi.<br>"
            "<span style='color: #64748b;'>Yukarıdaki <b>'+ Yeni Paket Ekle...'</b> veya <b>'Hızlı Boş Kart'</b> butonu ile paketinizi dahil edebilirsiniz.</span>"
        )
        self.sw_empty_lbl.setAlignment(Qt.AlignCenter)
        self.sw_empty_lbl.setStyleSheet("color: #94a3b8; font-size: 12.5px; line-height: 1.6; padding: 40px;")
        self.sw_empty_lbl.setWordWrap(True)
        self.sw_list_layout.addWidget(self.sw_empty_lbl)

        scroll.setWidget(container)
        layout.addWidget(scroll, 1)

        self.tabs.addTab(tab, " Yazılım Paketleri")

    def _setup_tab_equipment(self):
        """Sekme 3: Saha Ekipmanları Kontrol Listesi."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        header_row = QHBoxLayout()
        desc = QLabel("Saha operasyonuna çıkarken operatörün yanında götürmesi gereken malzemeler:")
        desc.setStyleSheet("color: #94a3b8; font-size: 13px;")
        desc.setWordWrap(True)
        header_row.addWidget(desc)
        header_row.addStretch()

        btn_pool = TouchButton("Hafızadan Malzeme Ekle...", variant="primary")
        btn_pool.setFixedHeight(34)
        btn_pool.setStyleSheet("min-height: 32px; padding: 2px 14px; font-size: 12.5px; font-weight: 700;")
        btn_pool.setToolTip("Hafızadaki ekipman havuzundan arayıp tekli veya çoklu malzeme seçerek profile ekleyin")
        btn_pool.clicked.connect(self._open_equipment_catalog_dialog)
        header_row.addWidget(btn_pool)

        btn_manual = TouchButton("Boş Satır Ekle", variant="ghost")
        btn_manual.setFixedHeight(34)
        btn_manual.setStyleSheet("min-height: 32px; padding: 2px 12px; font-size: 12px;")
        btn_manual.setToolTip("Doğrudan elle yazabileceğiniz boş bir malzeme satırı ekler")
        btn_manual.clicked.connect(lambda: self._add_equipment_card())
        header_row.addWidget(btn_manual)
        layout.addLayout(header_row)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        self.equip_list_layout = QVBoxLayout(container)
        self.equip_list_layout.setContentsMargins(0, 0, 4, 0)
        self.equip_list_layout.setSpacing(10)

        self.equip_empty_lbl = QLabel(
            "🎒 Henüz bu profile malzeme listesi eklenmedi.<br>"
            "<span style='color: #64748b;'>Yukarıdaki <b>'Hafızadan Malzeme Ekle...'</b> veya <b>'Boş Satır Ekle'</b> butonları ile malzeme dahil edebilirsiniz.</span>"
        )
        self.equip_empty_lbl.setAlignment(Qt.AlignCenter)
        self.equip_empty_lbl.setStyleSheet("color: #94a3b8; font-size: 12.5px; line-height: 1.6; padding: 40px;")
        self.equip_empty_lbl.setWordWrap(True)
        self.equip_list_layout.addWidget(self.equip_empty_lbl)

        scroll.setWidget(container)
        layout.addWidget(scroll, 1)

        self.tabs.addTab(tab, " Saha Ekipmanları")

    def _setup_tab_config(self):
        """Sekme 4: Referans Konfigürasyon Şablonu (Baseline Config)."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        header_row = QHBoxLayout()
        desc = QLabel("Bu istasyona ait referans konfigürasyon metni (JSON veya metin):")
        desc.setStyleSheet("color: #94a3b8; font-size: 13px;")
        desc.setWordWrap(True)
        header_row.addWidget(desc)
        header_row.addStretch()

        btn_sample = TouchButton("Örnek Şablon", variant="ghost")
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
        self.cfg_status_lbl.setStyleSheet("font-size: 12px; color: #94a3b8;")
        layout.addWidget(self.cfg_status_lbl)

        self.tabs.addTab(tab, "📝 Referans Konfigürasyon")

    def _make_field_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #cbd5e1;")
        return lbl

    def _open_add_software_dialog(self):
        dlg = AddSoftwareDialog(self.asset_manager, parent=self)
        if dlg.exec():
            req = dlg.get_software_requirement()
            if req:
                self._add_software_card(req)

    def _add_software_card(self, req: Optional[SoftwareRequirement] = None):
        card = SoftwareReqItemCard(req, on_delete=self._remove_software_card, asset_manager=self.asset_manager)
        self.sw_cards.append(card)
        self.sw_list_layout.addWidget(card)
        if hasattr(self, "sw_empty_lbl"):
            self.sw_empty_lbl.setVisible(False)

    def _remove_software_card(self, card: SoftwareReqItemCard):
        if card in self.sw_cards:
            self.sw_cards.remove(card)
            self.sw_list_layout.removeWidget(card)
            card.deleteLater()
            if hasattr(self, "sw_empty_lbl"):
                self.sw_empty_lbl.setVisible(len(self.sw_cards) == 0)

    def _open_equipment_catalog_dialog(self):
        existing_names = [
            card.txt_name.text().strip()
            for card in self.equip_cards
            if card.txt_name.text().strip()
        ]
        dlg = EquipmentCatalogDialog(
            self.equipment_manager,
            existing_item_names=existing_names,
            parent=self
        )
        if dlg.exec():
            items = dlg.get_selected_items()
            for it in items:
                self._add_equipment_card(it)

    def _add_equipment_card(self, item: Optional[EquipmentItem] = None):
        card = EquipmentItemCard(item, on_delete=self._remove_equipment_card)
        self.equip_cards.append(card)
        self.equip_list_layout.addWidget(card)
        if hasattr(self, "equip_empty_lbl"):
            self.equip_empty_lbl.setVisible(False)

    def _remove_equipment_card(self, card: EquipmentItemCard):
        if card in self.equip_cards:
            self.equip_cards.remove(card)
            self.equip_list_layout.removeWidget(card)
            card.deleteLater()
            if hasattr(self, "equip_empty_lbl"):
                self.equip_empty_lbl.setVisible(len(self.equip_cards) == 0)

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

    def _on_clone_combo_changed(self, index: int):
        """Klonlama açılır kutusundan bir lokasyon seçildiğinde tetiklenir."""
        if index > 0:
            self._apply_clone_from_selected()

    def _apply_clone_from_selected(self):
        """Seçilen mevcut lokasyon profilinin tüm ayarlarını isim ve ID hariç bu forma aktarır."""
        if not hasattr(self, "combo_clone"):
            return
        source_id = self.combo_clone.currentData()
        if not source_id:
            return

        source = self.profile_manager.load_profile(source_id)
        if not source:
            self.status_lbl.setText(f"✕ '{source_id}' lokasyon profili yüklenemedi!")
            self.status_lbl.setStyleSheet("color: #f87171; font-size: 12px; font-weight: 600;")
            return

        # 1. Genel Bilgiler (İsim hariç: kullanıcının girdiği isim korunur)
        self.txt_desc.setText(source.description)
        self.txt_notes.setPlainText(source.custom_notes)

        # 2. Hedef Cihaz & Bağlantı Ayarları
        td = source.target_device
        self.txt_host.setText(td.host)
        self.spin_port.setValue(td.port)
        self.txt_user.setText(td.username)
        if td.password:
            self.txt_pass.setText(td.password)
        else:
            self.txt_pass.clear()
        if td.key_path:
            self.txt_key.setText(td.key_path)
        else:
            self.txt_key.clear()
        self.chk_local_mode.setChecked(td.use_local_mode)
        self.txt_log_dir.setText(td.remote_log_dir)
        self.txt_cfg_path.setText(td.remote_config_path)

        # 3. Yazılım Paketleri (Mevcut kartları temizle ve kopyala)
        while self.sw_cards:
            self._remove_software_card(self.sw_cards[0])
        for sw in source.software_requirements:
            sw_copy = SoftwareRequirement(
                name=sw.name,
                expected_version=sw.expected_version,
                package_filename=sw.package_filename,
                target_install_path=sw.target_install_path,
                service_name=sw.service_name,
                version_command=sw.version_command,
                status="pending"
            )
            self._add_software_card(sw_copy)

        # 4. Saha Ekipmanları (Mevcut kartları temizle ve kopyala)
        while self.equip_cards:
            self._remove_equipment_card(self.equip_cards[0])
        for idx, eq in enumerate(source.equipment_checklist):
            eq_copy = EquipmentItem(
                id=f"eq_clone_{idx}_{int(id(eq)) % 1000}",
                name=eq.name,
                description=eq.description,
                is_mandatory=eq.is_mandatory,
                is_checked=False
            )
            self._add_equipment_card(eq_copy)

        # 5. Referans Konfigürasyon
        self.txt_baseline_config.setPlainText(source.baseline_config_content)
        self.cfg_status_lbl.setText(f"✓ '{source.name}' referans konfigürasyonu kopyalandı.")
        self.cfg_status_lbl.setStyleSheet("color: #34d399; font-size: 12px;")

        # Durum bildirimi
        self.status_lbl.setText(f"✓ '{source.name}' lokasyonunun tüm bilgileri kopyalandı (İsim hariç).")
        self.status_lbl.setStyleSheet("color: #34d399; font-size: 12px; font-weight: 600;")

        # Yeni isim verilmesi için imleci odakla
        if not self.txt_name.text().strip():
            self.txt_name.setFocus()
        elif not self.txt_id.text().strip():
            self.txt_id.setFocus()

    def _populate_fields(self):
        """Mevcut profil düzenleniyorsa alanları doldurur; yeniyse varsayılanları koyar."""
        if not self.profile_to_edit:
            # Yeni profil oluştururken boş kart eklenmez, liste temiz başlar
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

        # Elle yazılmış veya profildeki tüm malzemeleri kalıcı ekipman havuzuna otomatik kaydet
        if eq_list:
            try:
                self.equipment_manager.register_items(eq_list)
            except Exception as ex:
                print(f"[ProfileEditorDialog] Ekipman havuzuna otomatik kaydetme uyarısı: {ex}")

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
            self.accept()
        except Exception as e:
            self.status_lbl.setText(f"Kaydetme hatası: {e}")

