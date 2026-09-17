"""
FieldOps Assistant - Modern, Akıcı ve Reaktif Ana Pencere (MainWindow)
Sleek Segmented Stepper, modern breadcrumb ve reaktif sayfa geçişleri.
"""

from __future__ import annotations
import platform
import sys
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QStackedWidget, QFrame, QMessageBox
)

from app.adapters.base_adapter import BaseExecutionAdapter
from app.adapters.local_adapter import LocalExecutionAdapter
from app.adapters.ssh_adapter import SSHExecutionAdapter
from app.core.app_paths import AppPaths
from app.core.asset_manager import SoftwareAssetManager
from app.core.mission_context import MissionManager
from app.core.models import LocationProfile, MissionSession
from app.core.profile_manager import ProfileManager
from app.gui.styles import FIELD_DARK_THEME
from app.gui.widgets.touch_button import TouchButton
from app.gui.wizards.stage1_preflight import Stage1PreflightWidget
from app.gui.wizards.stage2_field_init import Stage2FieldInitWidget
from app.gui.wizards.stage3_field_end import Stage3FieldEndWidget
from app.gui.wizards.welcome_stage import MissionSelectionWidget


class ModernStepCapsule(QFrame):
    """Sleek, modern segment aşama kapsülü."""

    def __init__(self, step_num: int, title: str, parent=None):
        super().__init__(parent)
        self.step_num = step_num
        self.step_title = title

        self.setFixedHeight(46)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 6, 16, 6)
        layout.setSpacing(12)

        self.badge_icon = QLabel(str(step_num), self)
        self.badge_icon.setFixedSize(26, 26)
        self.badge_icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.badge_icon)

        self.text_lbl = QLabel(title)
        self.text_lbl.setStyleSheet("font-size: 13px; font-weight: 600;")
        layout.addWidget(self.text_lbl)
        layout.addStretch()

        self.set_state("pending")

    def set_state(self, state: str):
        if state == "active":
            self.setStyleSheet("""
                QFrame {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1e3a8a, stop:1 #312e81);
                    border: 1.5px solid #3b82f6;
                    border-radius: 10px;
                }
            """)
            self.badge_icon.setText(f"{self.step_num}")
            self.badge_icon.setStyleSheet("""
                background-color: #3b82f6;
                color: #ffffff;
                border-radius: 13px;
                font-weight: 800;
                font-size: 12px;
            """)
            self.text_lbl.setStyleSheet("color: #ffffff; font-size: 13px; font-weight: 700;")
        elif state == "completed":
            self.setStyleSheet("""
                QFrame {
                    background-color: rgba(16, 185, 129, 0.12);
                    border: 1px solid rgba(16, 185, 129, 0.35);
                    border-radius: 10px;
                }
            """)
            self.badge_icon.setText("✓")
            self.badge_icon.setStyleSheet("""
                background-color: #10b981;
                color: #ffffff;
                border-radius: 13px;
                font-weight: 800;
                font-size: 13px;
            """)
            self.text_lbl.setStyleSheet("color: #34d399; font-size: 13px; font-weight: 600;")
        else:  # pending / inactive
            self.setStyleSheet("""
                QFrame {
                    background-color: #0f172a;
                    border: 1px solid #1e293b;
                    border-radius: 10px;
                }
            """)
            self.badge_icon.setText(str(self.step_num))
            self.badge_icon.setStyleSheet("""
                background-color: #1e293b;
                color: #64748b;
                border-radius: 13px;
                font-weight: 600;
                font-size: 11px;
            """)
            self.text_lbl.setStyleSheet("color: #64748b; font-size: 13px; font-weight: 500;")


class MainWindow(QMainWindow):
    """Saha operasyonları merkezi kontrol arayüzü."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("FieldOps Assistant - Saha Operasyon & Konfigürasyon Yöneticisi")
        self.resize(1380, 890)
        self.setMinimumSize(1240, 780)
        self.setStyleSheet(FIELD_DARK_THEME)

        self.profile_manager = ProfileManager()
        self.asset_manager = SoftwareAssetManager()
        self.mission_manager = MissionManager()

        self.current_profile: Optional[LocationProfile] = None
        self.current_adapter: Optional[BaseExecutionAdapter] = None

        self._setup_ui()

    def _setup_ui(self):
        central_widget = QWidget(self)
        central_widget.setObjectName("CentralWidget")
        self.setCentralWidget(central_widget)

        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(20, 16, 20, 16)
        root_layout.setSpacing(14)

        # 1. Header Bar
        top_bar = QFrame()
        top_bar.setProperty("class", "ModernCard")
        tb_layout = QVBoxLayout(top_bar)
        tb_layout.setContentsMargins(18, 12, 18, 12)
        tb_layout.setSpacing(10)

        # Üst sıra: Menü Butonu, Başlık & Lokasyon Bilgisi
        info_row = QHBoxLayout()
        info_row.setSpacing(14)

        self.btn_menu = TouchButton("← Ana Menü", variant="ghost")
        self.btn_menu.setFixedHeight(36)
        self.btn_menu.setStyleSheet("font-size: 13px; padding: 4px 14px; min-height: 34px;")
        self.btn_menu.setVisible(False)
        self.btn_menu.clicked.connect(self._return_to_welcome)
        info_row.addWidget(self.btn_menu)

        brand_row = QHBoxLayout()
        brand_row.setSpacing(8)
        brand_icon = QLabel("🛡")
        brand_icon.setStyleSheet("font-size: 18px;")
        brand_row.addWidget(brand_icon)

        app_title = QLabel("FieldOps Assistant")
        app_title.setStyleSheet("font-size: 17px; font-weight: 800; color: #f8fafc; letter-spacing: -0.3px;")
        brand_row.addWidget(app_title)
        info_row.addLayout(brand_row)

        sep = QLabel("/")
        sep.setStyleSheet("color: #475569; font-size: 16px;")
        info_row.addWidget(sep)

        self.lbl_active_loc = QLabel("Faaliyet Seçimi")
        self.lbl_active_loc.setStyleSheet("font-size: 14px; font-weight: 600; color: #94a3b8;")
        info_row.addWidget(self.lbl_active_loc)

        info_row.addStretch()

        # 1. İşletim Sistemi Gösterge Kutucuğu (OS Detection Badge)
        os_sys = platform.system()
        if os_sys == "Windows":
            os_label = "🪟 Windows OS"
            os_pill = "PillBadge PillInfo"
            os_tooltip = f"İşletim Sistemi: Windows {platform.release()} ({platform.machine()})\nDestek Bilgisayarı Modu (Uzak SSH Bağlantısı Varsayılan)"
        elif os_sys == "Linux":
            os_label = "🐧 Linux OS"
            os_pill = "PillBadge PillSuccess"
            os_tooltip = f"İşletim Sistemi: Linux {platform.release()} ({platform.machine()})\nSaha Cihazı Modu (Doğrudan Yerel Çalıştırma Varsayılan)"
        elif os_sys == "Darwin":
            os_label = "🍎 macOS"
            os_pill = "PillBadge PillMuted"
            os_tooltip = f"İşletim Sistemi: macOS {platform.release()} ({platform.machine()})"
        else:
            os_label = f"💻 {os_sys}"
            os_pill = "PillBadge PillMuted"
            os_tooltip = f"İşletim Sistemi: {os_sys} {platform.release()}"

        self.lbl_os_badge = QLabel(os_label)
        self.lbl_os_badge.setProperty("class", os_pill)
        self.lbl_os_badge.setToolTip(os_tooltip)
        info_row.addWidget(self.lbl_os_badge)

        # 2. Taşınabilir USB / Yerel Disk Durumu
        is_usb = AppPaths.is_running_from_usb()
        self.lbl_storage_badge = QLabel("USB Modu" if is_usb else "Yerel Disk")
        self.lbl_storage_badge.setProperty("class", "PillBadge PillInfo" if is_usb else "PillBadge PillWarning")
        self.lbl_storage_badge.setToolTip("Taşınabilir USB Bellek üzerinden çalışıyor" if is_usb else "Bilgisayarın yerel diskinden çalışıyor")
        info_row.addWidget(self.lbl_storage_badge)

        tb_layout.addLayout(info_row)

        # Alt sıra: Segmented Stepper Bar
        self.step_container = QWidget()
        step_row = QHBoxLayout(self.step_container)
        step_row.setContentsMargins(0, 0, 0, 0)
        step_row.setSpacing(10)

        self.step1_widget = ModernStepCapsule(1, "Ön Kontroller & Hazırlık")
        step_row.addWidget(self.step1_widget, 1)

        self.step2_widget = ModernStepCapsule(2, "Faaliyet Başlangıcı & Enjeksiyon")
        step_row.addWidget(self.step2_widget, 1)

        self.step3_widget = ModernStepCapsule(3, "Faaliyet Sonu & Büyük Loglar")
        step_row.addWidget(self.step3_widget, 1)

        tb_layout.addWidget(self.step_container)
        root_layout.addWidget(top_bar)

        # 2. Sayfa Yığını (Stacked Widget)
        self.stacked_widget = QStackedWidget()

        # Sayfa 0: Karşılama Ekranı
        self.page_welcome = MissionSelectionWidget(self.profile_manager, self.mission_manager, self.asset_manager)
        self.page_welcome.start_new_mission.connect(self._on_start_new_mission)
        self.page_welcome.resume_mission.connect(self._on_resume_mission)
        self.stacked_widget.addWidget(self.page_welcome)

        # Sayfa 1: 1. Aşama
        self.page_stage1 = Stage1PreflightWidget(self.profile_manager, self.asset_manager)
        self.page_stage1.stage_completed.connect(self._on_stage1_completed)
        self.stacked_widget.addWidget(self.page_stage1)

        # Sayfa 2: 2. Aşama
        self.page_stage2 = Stage2FieldInitWidget()
        self.page_stage2.stage_completed.connect(self._on_stage2_completed)
        self.stacked_widget.addWidget(self.page_stage2)

        # Sayfa 3: 3. Aşama
        self.page_stage3 = Stage3FieldEndWidget(self.profile_manager, self.mission_manager)
        self.page_stage3.mission_finished.connect(self._on_mission_finished)
        self.stacked_widget.addWidget(self.page_stage3)

        root_layout.addWidget(self.stacked_widget)

        self.stacked_widget.setCurrentIndex(0)
        self._update_stepper_ui(-1)

    def _update_stepper_ui(self, current_step: int):
        steps = [self.step1_widget, self.step2_widget, self.step3_widget]
        if current_step < 0:
            for w in steps:
                w.set_state("pending")
            return

        for idx, w in enumerate(steps):
            if idx == current_step:
                w.set_state("active")
            elif idx < current_step:
                w.set_state("completed")
            else:
                w.set_state("pending")

    def _on_start_new_mission(self, profile: LocationProfile, operator_name: str):
        self.current_profile = profile
        self.lbl_active_loc.setText(f"{profile.name}")
        self.btn_menu.setVisible(True)

        self.mission_manager.start_new_session(profile.id, operator_name)
        self.mission_manager.set_current_stage(1)

        self.page_stage1.set_profile(profile, operator_name)
        self.stacked_widget.setCurrentIndex(1)
        self._update_stepper_ui(0)

    def _on_resume_mission(self, session: MissionSession, profile: LocationProfile, resume_stage: int):
        self.current_profile = profile
        self.mission_manager.load_session(session.session_id)
        self.lbl_active_loc.setText(f"{profile.name}")
        self.btn_menu.setVisible(True)

        if resume_stage == 1:
            self.page_stage1.set_profile(profile, session.operator_name)
            self.stacked_widget.setCurrentIndex(1)
            self._update_stepper_ui(0)
        elif resume_stage == 2:
            self.page_stage2.load_session(profile)
            self.stacked_widget.setCurrentIndex(2)
            self._update_stepper_ui(1)
        elif resume_stage == 3:
            if sys.platform != "win32":
                self.current_adapter = LocalExecutionAdapter()
            else:
                self.current_adapter = SSHExecutionAdapter(profile.target_device)

            self.page_stage3.load_session(profile, self.current_adapter)
            self.stacked_widget.setCurrentIndex(3)
            self._update_stepper_ui(2)

    def _on_stage1_completed(self, profile: LocationProfile, operator_name: str):
        self.current_profile = profile
        self.lbl_active_loc.setText(f"{profile.name}")
        self.mission_manager.set_current_stage(2)

        self.page_stage2.load_session(profile)
        self.stacked_widget.setCurrentIndex(2)
        self._update_stepper_ui(1)

    def _on_stage2_completed(self, adapter: BaseExecutionAdapter):
        self.current_adapter = adapter
        self.mission_manager.set_current_stage(3)

        self.page_stage3.load_session(self.current_profile, self.current_adapter)
        self.stacked_widget.setCurrentIndex(3)
        self._update_stepper_ui(2)

    def _on_mission_finished(self):
        if self.mission_manager.current_session:
            self.mission_manager.current_session.stage3_completed = True
            self.mission_manager.save_current_session()

        QMessageBox.information(
            self,
            "Görev Arşivlendi",
            f"Saha faaliyeti başarıyla tamamlandı ve arşivlendi.\n\n"
            f"Görev Özeti: {self.mission_manager.current_session_dir}"
        )
        self._return_to_welcome()

    def _return_to_welcome(self):
        self.lbl_active_loc.setText("Faaliyet Seçimi")
        self.btn_menu.setVisible(False)
        self.page_welcome.refresh_data()
        self.stacked_widget.setCurrentIndex(0)
        self._update_stepper_ui(-1)
