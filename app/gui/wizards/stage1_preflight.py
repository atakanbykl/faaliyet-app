"""
FieldOps Assistant - 1. Aşama: Yola Çıkış & Ön Hazırlık (Stage 1: Pre-Departure)
İki sütunlu modern, ferah düzen: Sol tarafta Lokasyon ve Paketler, sağ tarafta geniş Saha Ekipmanları Listesi.
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QLineEdit, QFileDialog, QMessageBox, QFrame, QSizePolicy, QCheckBox
)

from app.core.asset_manager import SoftwareAssetManager
from app.core.models import LocationProfile, SoftwareRequirement
from app.core.profile_manager import ProfileManager
from app.gui.widgets.checklist_widget import ChecklistWidget
from app.gui.widgets.touch_button import TouchButton


class Stage1PreflightWidget(QWidget):
    """1. Aşama Ekranı: İki sütunlu geniş ve rahat hazırlık kontrol paneli."""
    stage_completed = Signal(LocationProfile, str)

    def __init__(
        self,
        profile_manager: ProfileManager,
        asset_manager: SoftwareAssetManager,
        parent=None
    ):
        super().__init__(parent)
        self.profile_manager = profile_manager
        self.asset_manager = asset_manager
        self.current_profile: Optional[LocationProfile] = None
        self.checklist_widget: Optional[ChecklistWidget] = None

        self._setup_ui()
        self._load_profiles()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 16, 24, 16)
        main_layout.setSpacing(14)

        # Üst Başlık Kartı
        header_frame = QFrame()
        header_frame.setProperty("class", "ModernCard")
        h_layout = QVBoxLayout(header_frame)
        h_layout.setContentsMargins(18, 12, 18, 12)
        h_layout.setSpacing(4)

        title = QLabel("1. AŞAMA: Yola Çıkış & Saha Ön Hazırlığı")
        title.setProperty("class", "SectionTitle")
        h_layout.addWidget(title)

        desc = QLabel("Hedef lokasyon konfigürasyonlarını, yazılım paketlerini ve malzeme çantanızı doğrulayın.")
        desc.setProperty("class", "SectionSubtitle")
        h_layout.addWidget(desc)
        main_layout.addWidget(header_frame)

        # İKİ SÜTUNLU ANA GÖVDE (SOL: Lokasyon & Paketler, SAĞ: Geniş Ekipman Listesi)
        body_layout = QHBoxLayout()
        body_layout.setSpacing(18)

        # ==========================================
        # SOL KOLON (Lokasyon + Paketler)
        # ==========================================
        left_column = QVBoxLayout()
        left_column.setSpacing(14)

        # 1. KART: Lokasyon & Operatör
        loc_card = QFrame()
        loc_card.setProperty("class", "ModernCard")
        loc_layout = QVBoxLayout(loc_card)
        loc_layout.setContentsMargins(18, 16, 18, 16)
        loc_layout.setSpacing(12)

        lbl_s1 = QLabel("📍 Lokasyon ve Operatör Bilgisi")
        lbl_s1.setStyleSheet("font-size: 15px; font-weight: 700; color: #f8fafc;")
        loc_layout.addWidget(lbl_s1)

        row1 = QHBoxLayout()
        lbl_loc = QLabel("Hedef Lokasyon:")
        lbl_loc.setStyleSheet("font-weight: 600; min-width: 120px; color: #e2e8f0; font-size: 13px;")
        self.loc_combo = QComboBox()
        self.loc_combo.currentIndexChanged.connect(self._on_profile_selected)
        row1.addWidget(lbl_loc)
        row1.addWidget(self.loc_combo, 1)
        loc_layout.addLayout(row1)

        row2 = QHBoxLayout()
        lbl_op = QLabel("Saha Operatörü:")
        lbl_op.setStyleSheet("font-weight: 600; min-width: 120px; color: #e2e8f0; font-size: 13px;")
        self.op_input = QLineEdit()
        self.op_input.setPlaceholderText("Operatör adı...")
        self.op_input.setText("Saha Mühendisi")
        row2.addWidget(lbl_op)
        row2.addWidget(self.op_input, 1)
        loc_layout.addLayout(row2)

        self.loc_desc_lbl = QLabel()
        self.loc_desc_lbl.setStyleSheet("color: #94a3b8; font-size: 12px; line-height: 1.3;")
        self.loc_desc_lbl.setWordWrap(True)
        loc_layout.addWidget(self.loc_desc_lbl)
        left_column.addWidget(loc_card)

        # 2. KART: Yazılım Paketleri & Konfigürasyon Taraması
        self.pkg_card = QFrame()
        self.pkg_card.setProperty("class", "ModernCard")
        self.pkg_layout = QVBoxLayout(self.pkg_card)
        self.pkg_layout.setContentsMargins(18, 16, 18, 16)
        self.pkg_layout.setSpacing(12)

        lbl_s2 = QLabel("📦 Yazılım Paketleri & Konfigürasyon")
        lbl_s2.setStyleSheet("font-size: 15px; font-weight: 700; color: #f8fafc;")
        self.pkg_layout.addWidget(lbl_s2)

        # Paketlerin listesi doğrudan kart içinde doğal boyutuyla listelenir (scroll alanı kaldırıldı)
        self.pkg_items_layout = QVBoxLayout()
        self.pkg_items_layout.setContentsMargins(0, 4, 0, 0)
        self.pkg_items_layout.setSpacing(10)
        self.pkg_layout.addLayout(self.pkg_items_layout)

        left_column.addWidget(self.pkg_card)
        left_column.addStretch()
        body_layout.addLayout(left_column, 5)

        # ==========================================
        # SAĞ KOLON: GENİŞ VE FERAH EKİPMAN LİSTESİ
        # ==========================================
        self.equip_card = QFrame()
        self.equip_card.setProperty("class", "ModernCard")
        self.equip_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.equip_layout = QVBoxLayout(self.equip_card)
        self.equip_layout.setContentsMargins(20, 18, 20, 18)
        self.equip_layout.setSpacing(14)

        equip_header = QHBoxLayout()
        lbl_s3 = QLabel("🎒 Saha Ekipmanları ve Malzeme Kontrol Listesi")
        lbl_s3.setStyleSheet("font-size: 15px; font-weight: 700; color: #34d399;")
        equip_header.addWidget(lbl_s3)
        equip_header.addStretch()

        lbl_hint = QLabel("Maddeye tıklayarak işaretleyin")
        lbl_hint.setStyleSheet("color: #64748b; font-size: 12px;")
        equip_header.addWidget(lbl_hint)
        self.equip_layout.addLayout(equip_header)

        self.equip_container = QVBoxLayout()
        self.equip_container.setContentsMargins(0, 4, 0, 0)
        self.equip_layout.addLayout(self.equip_container, 1)

        body_layout.addWidget(self.equip_card, 6)
        main_layout.addLayout(body_layout, 1)

        # ==========================================
        # ALT AKSİYON BARI
        # ==========================================
        bottom_bar = QHBoxLayout()
        bottom_bar.setContentsMargins(4, 0, 4, 0)

        self.status_summary_lbl = QLabel()
        self.status_summary_lbl.setStyleSheet("font-size: 14px; font-weight: 600;")
        bottom_bar.addWidget(self.status_summary_lbl)
        bottom_bar.addStretch()

        self.chk_force_equipment = QCheckBox("⚠️ Zorunlu Ekipmanı Yoksay (Force Geçiş)")
        self.chk_force_equipment.setStyleSheet("""
            QCheckBox {
                color: #fbbf24;
                font-size: 13px;
                font-weight: 600;
                spacing: 8px;
            }
            QCheckBox:hover {
                color: #f59e0b;
            }
        """)
        self.chk_force_equipment.setToolTip("Acil durumlarda eksik zorunlu ekipman olsa dahi operatör onayıyla faaliyete devam etmeyi sağlar")
        self.chk_force_equipment.toggled.connect(self._update_readiness)
        bottom_bar.addWidget(self.chk_force_equipment)

        self.complete_btn = TouchButton("Hazırlığı Tamamla ve Yola Çık  ➔", variant="primary")
        self.complete_btn.setMinimumWidth(320)
        self.complete_btn.clicked.connect(self._on_complete_clicked)
        bottom_bar.addWidget(self.complete_btn)

        main_layout.addLayout(bottom_bar)

    def _load_profiles(self):
        profiles = self.profile_manager.list_profiles()
        self.loc_combo.clear()
        for prof in profiles:
            self.loc_combo.addItem(f"{prof.name} ({prof.id})", prof.id)

    def set_profile(self, profile: LocationProfile, operator_name: str):
        idx = self.loc_combo.findData(profile.id)
        if idx >= 0:
            self.loc_combo.setCurrentIndex(idx)
        else:
            self.loc_combo.addItem(f"{profile.name} ({profile.id})", profile.id)
            self.loc_combo.setCurrentIndex(self.loc_combo.count() - 1)
        self.op_input.setText(operator_name)
        self._on_profile_selected(self.loc_combo.currentIndex())

    def _on_profile_selected(self, index: int):
        profile_id = self.loc_combo.currentData()
        if not profile_id:
            return

        self.current_profile = self.profile_manager.load_profile(profile_id)
        if not self.current_profile:
            return

        self.loc_desc_lbl.setText(
            f"Hedef Sistem: <b>{self.current_profile.target_device.username}@{self.current_profile.target_device.host}</b><br>"
            f"{self.current_profile.description}"
        )

        self._refresh_software_packages()
        self._refresh_equipment_checklist()
        self._update_readiness()

    def _refresh_software_packages(self):
        while self.pkg_items_layout.count():
            item = self.pkg_items_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.current_profile:
            return

        # Konfigürasyon Şablonu
        cfg_frame = QFrame()
        cfg_frame.setProperty("class", "ElevatedCard")
        cfg_layout = QHBoxLayout(cfg_frame)
        cfg_layout.setContentsMargins(14, 10, 14, 10)

        cfg_lbl = QLabel(f"Konfigürasyon: <code>{self.current_profile.target_device.remote_config_path}</code>")
        cfg_lbl.setStyleSheet("color: #e2e8f0; font-size: 12px;")
        cfg_layout.addWidget(cfg_lbl)
        cfg_layout.addStretch()

        if self.current_profile.baseline_config_content.strip():
            badge = QLabel("✓ Mevcut")
            badge.setProperty("class", "PillBadge PillSuccess")
        else:
            badge = QLabel("Eksik")
            badge.setProperty("class", "PillBadge PillDanger")
        cfg_layout.addWidget(badge)
        self.pkg_items_layout.addWidget(cfg_frame)

        # Yazılım Paketleri
        for req in self.current_profile.software_requirements:
            found, path = self.asset_manager.check_requirement(self.current_profile.id, req)
            row_frame = QFrame()
            row_frame.setProperty("class", "ElevatedCard")
            row_layout = QHBoxLayout(row_frame)
            row_layout.setContentsMargins(14, 10, 14, 10)
            row_layout.setSpacing(12)

            info_layout = QVBoxLayout()
            info_layout.setSpacing(2)
            name_lbl = QLabel(f"<b>{req.name}</b> (v{req.expected_version})")
            name_lbl.setStyleSheet("font-size: 13px; color: #f8fafc;")

            file_lbl = QLabel(f"<code>{req.package_filename}</code>")
            file_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")
            info_layout.addWidget(name_lbl)
            info_layout.addWidget(file_lbl)
            row_layout.addLayout(info_layout)
            row_layout.addStretch()

            if found:
                badge = QLabel("✓ Bulundu")
                badge.setProperty("class", "PillBadge PillSuccess")
                badge.setToolTip(str(path))
                row_layout.addWidget(badge)
            else:
                badge = QLabel("Bulunamadı")
                badge.setProperty("class", "PillBadge PillWarning")
                row_layout.addWidget(badge)

                browse_btn = TouchButton("Seç...", variant="ghost")
                browse_btn.setFixedHeight(30)
                browse_btn.setStyleSheet("font-size: 12px; padding: 2px 10px; min-height: 28px;")
                browse_btn.clicked.connect(lambda _, r=req: self._browse_external_package(r))
                row_layout.addWidget(browse_btn)

            self.pkg_items_layout.addWidget(row_frame)

    def _browse_external_package(self, req: SoftwareRequirement):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"{req.name} İçin Yazılım Paketini Seçin",
            "",
            "Arşiv Paketleri (*.tar.gz *.tgz *.zip *.bin *.exe);;Tüm Dosyalar (*.*)"
        )
        if file_path:
            p = Path(file_path)
            self.asset_manager.register_external_package(
                self.current_profile.id,
                req,
                p,
                copy_to_storage=True
            )
            QMessageBox.information(self, "Paket Eklendi", f"'{p.name}' paketi dahil edildi.")
            self._refresh_software_packages()
            self._update_readiness()

    def _refresh_equipment_checklist(self):
        while self.equip_container.count():
            item = self.equip_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.current_profile:
            return

        self.chk_force_equipment.setChecked(False)
        self.checklist_widget = ChecklistWidget(self.current_profile.equipment_checklist)
        self.checklist_widget.checklist_updated.connect(self._update_readiness)
        self.equip_container.addWidget(self.checklist_widget)

    def _update_readiness(self):
        if not self.current_profile:
            self.complete_btn.setEnabled(False)
            return

        all_pkgs_ok = all(
            req.resolved_package_path is not None
            for req in self.current_profile.software_requirements
        )
        checklist_ok = self.checklist_widget.are_all_mandatory_checked() if self.checklist_widget else False
        force_active = self.chk_force_equipment.isChecked()

        if all_pkgs_ok and (checklist_ok or force_active):
            if checklist_ok:
                self.status_summary_lbl.setText("<span style='color: #34d399;'>✓ Tüm hazırlıklar tamamlandı.</span>")
                self.complete_btn.setText("Hazırlığı Tamamla ve Yola Çık  ➔")
                self.complete_btn.setEnabled(True)
                self.complete_btn.set_variant("success")
            else:
                missing = self.checklist_widget.get_missing_mandatory_items() if self.checklist_widget else []
                self.status_summary_lbl.setText(f"<span style='color: #fbbf24;'>⚠️ Force Aktif: {len(missing)} zorunlu malzeme işaretlenmedi</span>")
                self.complete_btn.setText("⚠️ Eksik Ekipmanla Yine de Yola Çık  ➔")
                self.complete_btn.setEnabled(True)
                self.complete_btn.set_variant("warning")
        else:
            reasons = []
            if not all_pkgs_ok:
                reasons.append("Eksik yazılım paketleri var")
            if not checklist_ok and not force_active:
                reasons.append("İşaretlenmemiş zorunlu ekipmanlar var")
            self.status_summary_lbl.setText(f"<span style='color: #fbbf24;'>Bekleyen: {', '.join(reasons)}</span>")
            self.complete_btn.setText("Hazırlığı Tamamla ve Yola Çık  ➔")
            self.complete_btn.setEnabled(False)
            self.complete_btn.set_variant("primary")

    def _on_complete_clicked(self):
        if not self.current_profile:
            return

        checklist_ok = self.checklist_widget.are_all_mandatory_checked() if self.checklist_widget else False
        if not checklist_ok:
            missing = self.checklist_widget.get_missing_mandatory_items() if self.checklist_widget else []
            missing_text = "\n• " + "\n• ".join([item.name for item in missing])
            reply = QMessageBox.warning(
                self,
                "Zorunlu Ekipman Eksik (Force Geçiş)",
                f"DİKKAT: Aşağıdaki zorunlu malzemeler işaretlenmedi:{missing_text}\n\n"
                "Bu malzemeler eksik olarak sahaya çıkmak istediğinizden emin misiniz?\n"
                "(Tüm sorumluluk saha operatörüne aittir.)",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

        op_name = self.op_input.text().strip() or "Saha_Operatoru"
        reply = QMessageBox.question(
            self,
            "1. Aşamayı Tamamla",
            f"'{self.current_profile.name}' hazırlıkları onaylandı.\n"
            "Faaliyet lokasyonuna yola çıkılıyor mu?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        if reply == QMessageBox.Yes:
            self.stage_completed.emit(self.current_profile, op_name)
