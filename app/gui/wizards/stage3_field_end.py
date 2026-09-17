"""
FieldOps Assistant - 3. Aşama: Faaliyet Sonu & Log Toplama (Stage 3: Field Wrap-up)
Modern kart mimarisi, 20-30GB log sıkıştırma ve çekme, görsel diff kıyaslama ve USB aktarımı.
"""

from __future__ import annotations
import shutil
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QMessageBox, QScrollArea, QProgressBar
)

from app.adapters.base_adapter import BaseExecutionAdapter
from app.core.app_paths import AppPaths
from app.core.diff_engine import ConfigDiffEngine
from app.core.mission_context import MissionManager
from app.core.models import EquipmentItem, LocationProfile
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

        # 1. KART: Kapanış Kontrolleri
        wrap_card = QFrame()
        wrap_card.setProperty("class", "ModernCard")
        w_layout = QVBoxLayout(wrap_card)
        w_layout.setSpacing(12)

        lbl_s1 = QLabel("🎒 Kapanış ve Toplanma Kontrolleri")
        lbl_s1.setStyleSheet("font-size: 15px; font-weight: 700; color: #f8fafc;")
        w_layout.addWidget(lbl_s1)

        self.wrap_items = [
            EquipmentItem(id="w1", name="Sensör ve RF bağlantıları güvenle söküldü", is_mandatory=True),
            EquipmentItem(id="w2", name="Cihaz güç kaynağı ve aküsü kapatıldı", is_mandatory=True),
            EquipmentItem(id="w3", name="Kablolar ve antenler toplanıp çantaya yerleştirildi", is_mandatory=True),
        ]
        self.wrap_checklist = ChecklistWidget(self.wrap_items)
        w_layout.addWidget(self.wrap_checklist)
        l_layout.addWidget(wrap_card)

        # 2. KART: 20-30 GB Log Toplama
        log_card = QFrame()
        log_card.setProperty("class", "ModernCard")
        log_layout = QVBoxLayout(log_card)
        log_layout.setSpacing(12)

        lbl_s2 = QLabel("📦 Faaliyet Loglarının Paketlenmesi (20-30 GB)")
        lbl_s2.setStyleSheet("font-size: 15px; font-weight: 700; color: #f8fafc;")
        log_layout.addWidget(lbl_s2)

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

        # 3. KART: Konfigürasyon Snapshot'ı & Diff
        cfg_card = QFrame()
        cfg_card.setProperty("class", "ModernCard")
        cfg_layout = QVBoxLayout(cfg_card)
        cfg_layout.setSpacing(12)

        lbl_s3 = QLabel("🔍 Aktif Konfigürasyon Snapshot'ı & Kıyaslama")
        lbl_s3.setStyleSheet("font-size: 15px; font-weight: 700; color: #f8fafc;")
        cfg_layout.addWidget(lbl_s3)

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

        # 4. KART: USB Senkronizasyon Kartı
        usb_card = QFrame()
        usb_card.setProperty("class", "ModernCard")
        usb_layout = QVBoxLayout(usb_card)
        usb_layout.setSpacing(12)

        lbl_s4 = QLabel("💾 USB Bellek Senkronizasyonu")
        lbl_s4.setStyleSheet("font-size: 15px; font-weight: 700; color: #f8fafc;")
        usb_layout.addWidget(lbl_s4)

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

        # Alt Kapanış Butonu
        bottom_bar = QHBoxLayout()
        bottom_bar.addStretch()

        self.btn_finish_mission = TouchButton("Görevi ve Faaliyeti Resmen Tamamla  ✓", variant="success")
        self.btn_finish_mission.setMinimumWidth(340)
        self.btn_finish_mission.clicked.connect(self._finish_mission)
        bottom_bar.addWidget(self.btn_finish_mission)

        main_layout.addLayout(bottom_bar)

    def load_session(self, profile: LocationProfile, adapter: BaseExecutionAdapter):
        self.profile = profile
        self.adapter = adapter
        self.console.append_log(f"3. Aşama Başlatıldı. Lokasyon: {profile.name}", "system")
        self._check_usb_status()

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

    def _collect_logs(self):
        if not self.adapter or not self.profile:
            return

        reply = QMessageBox.question(
            self,
            "Büyük Log Toplama Onayı",
            f"'{self.profile.target_device.remote_log_dir}' klasöründeki tüm loglar "
            f"sıkıştırılacak (tar.gz) ve görev arşivine aktarılacaktır.\n\n"
            "İşlem başlatılsın mı?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply != QMessageBox.Yes:
            return

        self.console.append_log("Log toplama işlemi başlatıldı...", "system")
        self.log_progress.setVisible(True)
        self.log_progress.setValue(25)

        session_dir = self.mission_manager.current_session_dir or AppPaths.get_missions_dir()
        archive_name = f"logs_{self.profile.id}.tar.gz"
        remote_archive_path = f"/tmp/{archive_name}"
        local_archive_path = session_dir / archive_name

        self.console.append_log("Hedef cihazda çok çekirdekli tar sıkıştırma tetikleniyor...", "info")
        success, sha = self.adapter.compress_logs(
            log_source_dir=self.profile.target_device.remote_log_dir,
            output_archive_path=remote_archive_path,
            log_callback=lambda msg: self.console.append_log(msg, "dim")
        )

        if not success:
            self.console.append_log(f"SIKIŞTIRMA HATASI: {sha}", "error")
            QMessageBox.critical(self, "Hata", f"Loglar sıkıştırılamadı:\n{sha}")
            self.log_progress.setVisible(False)
            return

        self.log_progress.setValue(60)
        self.console.append_log(f"Sıkıştırma başarılı. SHA-256: {sha}", "info")

        self.console.append_log(f"Arşiv indiriliyor: {remote_archive_path} -> {local_archive_path}", "info")
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
                f"Tüm loglar sıkıştırılarak indirildi.\n\nSHA-256: {sha}\nKonum: {local_archive_path}"
            )
        else:
            self.lbl_log_status.setText("Hata")
            self.lbl_log_status.setProperty("class", "PillBadge PillDanger")
            self.console.append_log(f"İNDİRME HATASI: {fetch_msg}", "error")

        self.lbl_log_status.style().unpolish(self.lbl_log_status)
        self.lbl_log_status.style().polish(self.lbl_log_status)

    def _on_download_progress(self, current_bytes: int, total_bytes: int):
        if total_bytes > 0:
            pct = int((current_bytes / total_bytes) * 100)
            self.log_progress.setValue(pct)

    def _pull_active_config(self):
        if not self.adapter or not self.profile:
            return

        self.console.append_log("Sahadaki aktif konfigürasyon çekiliyor...", "info")
        success, content = self.adapter.pull_active_configuration(
            self.profile.target_device.remote_config_path
        )

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
            self.console.append_log(f"KONFİGÜRASYON ÇEKİLEMEDİ: {content}", "error")
            QMessageBox.warning(self, "Hata", f"Konfigürasyon dosyası okunamadı:\n{content}")

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
                self.console.append_log(f"Senkronizasyon tamamlandı: {dest_dir}", "info")
                QMessageBox.information(
                    self,
                    "Senkronizasyon Başarılı",
                    f"Tüm görev ve log dosyaları başarıyla aktarıldı:\n{dest_dir}"
                )
        except Exception as e:
            self.console.append_log(f"USB Kopyalama Hatası: {e}", "error")
            QMessageBox.critical(self, "Hata", f"USB'ye kopyalama sırasında hata oluştu:\n{e}")

    def _finish_mission(self):
        reply = QMessageBox.question(
            self,
            "Görevi Tamamla",
            "Saha faaliyeti başarıyla tamamlandı.\n"
            "Yeni bir görev için başa dönülsün mü?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        if reply == QMessageBox.Yes:
            self.console.append_log("GÖREV RESMEN SONLANDIRILDI.", "system")
            self.mission_finished.emit()
