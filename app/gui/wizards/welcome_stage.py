"""
FieldOps Assistant - Modern Launchpad & Görev Başlatıcı (Welcome & Mission Selection)
Modern kart akışı, reaktif görev listesi, sıfır tablo karmaşası ve kusursuz ergonomi.
"""

from __future__ import annotations
from typing import List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QLineEdit, QFrame, QScrollArea, QMessageBox, QDialog
)

from app.core.mission_context import MissionManager
from app.core.models import LocationProfile, MissionSession
from app.core.profile_manager import ProfileManager
from app.gui.widgets.mission_card import MissionCardWidget
from app.gui.widgets.touch_button import TouchButton


class MissionSelectionWidget(QWidget):
    """İlk açılışta faaliyet sorgulama ve modern kart listesiyle devam ettirme ekranı."""
    start_new_mission = Signal(LocationProfile, str)
    resume_mission = Signal(MissionSession, LocationProfile, int)

    def __init__(
        self,
        profile_manager: ProfileManager,
        mission_manager: MissionManager,
        parent=None
    ):
        super().__init__(parent)
        self.profile_manager = profile_manager
        self.mission_manager = mission_manager
        self.profiles: List[LocationProfile] = []
        self.saved_sessions: List[MissionSession] = []
        self.selected_session: Optional[MissionSession] = None
        self.card_widgets: List[MissionCardWidget] = []

        self._setup_ui()
        self.refresh_data()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(18)

        # Üst Başlık Banner (Minimalist & Şık)
        header = QFrame()
        header.setProperty("class", "ModernCard")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(20, 16, 20, 16)

        title_col = QVBoxLayout()
        title_col.setSpacing(4)
        title = QLabel("Saha Operasyon Kontrol Merkezi")
        title.setProperty("class", "SectionTitle")
        title_col.addWidget(title)

        subtitle = QLabel("Yeni bir saha görevi başlatabilir veya kayıtlı bir faaliyete kaldığı yerden devam edebilirsiniz.")
        subtitle.setProperty("class", "SectionSubtitle")
        title_col.addWidget(subtitle)
        h_layout.addLayout(title_col)
        h_layout.addStretch()

        self.lbl_stats = QLabel("0 Kayıtlı Görev")
        self.lbl_stats.setProperty("class", "PillBadge PillInfo")
        h_layout.addWidget(self.lbl_stats)

        main_layout.addWidget(header)

        # İki Kolonlu Panel Düzeni
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)

        # SOL PANEL: YENİ FAALİYET BAŞLAT
        new_card = QFrame()
        new_card.setProperty("class", "ModernCard")
        new_card_layout = QVBoxLayout(new_card)
        new_card_layout.setContentsMargins(22, 20, 22, 20)
        new_card_layout.setSpacing(16)

        card1_header = QHBoxLayout()
        card1_title = QLabel("🚀 Yeni Faaliyet Başlat")
        card1_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #60a5fa;")
        card1_header.addWidget(card1_title)
        card1_header.addStretch()
        new_card_layout.addLayout(card1_header)

        card1_desc = QLabel("Yeni bir saha faaliyeti kaydı oluşturur ve 1. Aşama (Ön Kontroller) hazırlıklarını başlatır.")
        card1_desc.setStyleSheet("color: #94a3b8; font-size: 13px; line-height: 1.4;")
        card1_desc.setWordWrap(True)
        new_card_layout.addWidget(card1_desc)

        new_card_layout.addSpacing(6)

        # Lokasyon Seçimi
        loc_header = QHBoxLayout()
        lbl_loc = QLabel("Hedef Görev Lokasyonu:")
        lbl_loc.setStyleSheet("font-weight: 600; color: #f8fafc; font-size: 13px;")
        loc_header.addWidget(lbl_loc)
        loc_header.addStretch()

        self.btn_new_loc = TouchButton("+ Yeni", variant="ghost")
        self.btn_new_loc.setFixedHeight(28)
        self.btn_new_loc.setStyleSheet("min-height: 26px; padding: 2px 10px; font-size: 12px; font-weight: 600; color: #60a5fa; border-color: rgba(59, 130, 246, 0.4); border-radius: 6px;")
        self.btn_new_loc.setToolTip("Yeni Hedef Lokasyon Profili Tanımla")
        self.btn_new_loc.clicked.connect(self._on_create_location_clicked)
        loc_header.addWidget(self.btn_new_loc)

        self.btn_edit_loc = TouchButton("✏️ Düzenle", variant="ghost")
        self.btn_edit_loc.setFixedHeight(28)
        self.btn_edit_loc.setStyleSheet("min-height: 26px; padding: 2px 10px; font-size: 12px; font-weight: 500; border-radius: 6px;")
        self.btn_edit_loc.setToolTip("Seçili Lokasyonun Parametrelerini Düzenle")
        self.btn_edit_loc.clicked.connect(self._on_edit_location_clicked)
        loc_header.addWidget(self.btn_edit_loc)

        new_card_layout.addLayout(loc_header)

        self.loc_combo = QComboBox()
        self.loc_combo.currentIndexChanged.connect(self._on_profile_preview)
        new_card_layout.addWidget(self.loc_combo)

        self.loc_preview_lbl = QLabel()
        self.loc_preview_lbl.setStyleSheet("color: #94a3b8; font-size: 12px; line-height: 1.3;")
        self.loc_preview_lbl.setWordWrap(True)
        new_card_layout.addWidget(self.loc_preview_lbl)

        # Operatör
        lbl_op = QLabel("Saha Operatörü:")
        lbl_op.setStyleSheet("font-weight: 600; color: #f8fafc; font-size: 13px;")
        new_card_layout.addWidget(lbl_op)

        self.op_input = QLineEdit()
        self.op_input.setPlaceholderText("Operatör adı...")
        self.op_input.setText("Saha Mühendisi")
        new_card_layout.addWidget(self.op_input)

        new_card_layout.addStretch()

        self.btn_start_new = TouchButton("Yeni Görevi Başlat  ➔", variant="primary")
        self.btn_start_new.clicked.connect(self._on_start_new_clicked)
        new_card_layout.addWidget(self.btn_start_new)

        cards_layout.addWidget(new_card, 4)

        # SAĞ PANEL: KAYITLI FAALİYETLER (MODERN KART AKIŞI)
        resume_card = QFrame()
        resume_card.setProperty("class", "ModernCard")
        resume_layout = QVBoxLayout(resume_card)
        resume_layout.setContentsMargins(22, 20, 22, 20)
        resume_layout.setSpacing(14)

        card2_header = QHBoxLayout()
        card2_title = QLabel("📂 Kayıtlı Faaliyetler")
        card2_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #34d399;")
        card2_header.addWidget(card2_title)
        card2_header.addStretch()

        lbl_hint = QLabel("Devam etmek için bir karta tıklayın")
        lbl_hint.setStyleSheet("color: #64748b; font-size: 12px;")
        card2_header.addWidget(lbl_hint)
        resume_layout.addLayout(card2_header)

        # Scrollable Kart Alanı
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.cards_container = QWidget()
        self.cards_list_layout = QVBoxLayout(self.cards_container)
        self.cards_list_layout.setContentsMargins(0, 0, 6, 0)
        self.cards_list_layout.setSpacing(10)

        self.scroll_area.setWidget(self.cards_container)
        resume_layout.addWidget(self.scroll_area)

        # Boş Durum Bilgisi (Empty State)
        self.empty_state_lbl = QLabel(
            "📋 Henüz kayıtlı bir geçmiş faaliyet bulunmuyor.\n"
            "Sol panelden yeni bir saha faaliyeti başlatabilirsiniz."
        )
        self.empty_state_lbl.setAlignment(Qt.AlignCenter)
        self.empty_state_lbl.setStyleSheet("color: #64748b; font-size: 14px; line-height: 1.6; padding: 40px;")
        self.empty_state_lbl.setVisible(False)
        resume_layout.addWidget(self.empty_state_lbl)

        cards_layout.addWidget(resume_card, 6)
        main_layout.addLayout(cards_layout)

    def refresh_data(self):
        """Profilleri ve kayıtlı oturumları diskten yükler."""
        self.profiles = self.profile_manager.list_profiles()
        self.loc_combo.clear()
        for p in self.profiles:
            self.loc_combo.addItem(f"{p.name} ({p.id})", p.id)
        self._on_profile_preview()

        # Kayıtlı oturumları temizle ve yeniden oluştur
        while self.cards_list_layout.count():
            item = self.cards_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.card_widgets.clear()

        self.saved_sessions = self.mission_manager.list_saved_sessions()
        self.lbl_stats.setText(f"{len(self.saved_sessions)} Kayıtlı Görev")

        if not self.saved_sessions:
            self.empty_state_lbl.setVisible(True)
            self.scroll_area.setVisible(False)
        else:
            self.empty_state_lbl.setVisible(False)
            self.scroll_area.setVisible(True)

            for s in self.saved_sessions:
                prof = next((p for p in self.profiles if p.id == s.location_id), None)
                card = MissionCardWidget(s, prof)
                card.resume_requested.connect(self._resume_specific_session)
                card.delete_requested.connect(self._delete_specific_session)
                card.clicked.connect(self._on_card_clicked)
                self.card_widgets.append(card)
                self.cards_list_layout.addWidget(card)

            self.cards_list_layout.addStretch()

    def _on_profile_preview(self):
        profile_id = self.loc_combo.currentData()
        if not profile_id:
            return
        p = next((x for x in self.profiles if x.id == profile_id), None)
        if p:
            self.loc_preview_lbl.setText(f"Hedef: {p.target_device.username}@{p.target_device.host} &nbsp;•&nbsp; {p.description}")

    def _on_create_location_clicked(self):
        from app.gui.widgets.profile_editor_dialog import ProfileEditorDialog
        dlg = ProfileEditorDialog(self.profile_manager, profile_to_edit=None, parent=self)
        if dlg.exec() == QDialog.Accepted and dlg.saved_profile_id:
            self.refresh_data()
            idx = self.loc_combo.findData(dlg.saved_profile_id)
            if idx >= 0:
                self.loc_combo.setCurrentIndex(idx)

    def _on_edit_location_clicked(self):
        profile_id = self.loc_combo.currentData()
        if not profile_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen düzenlemek istediğiniz bir lokasyon seçin.")
            return

        profile = self.profile_manager.load_profile(profile_id)
        if not profile:
            QMessageBox.critical(self, "Hata", f"'{profile_id}' lokasyon profili bulunamadı!")
            return

        from app.gui.widgets.profile_editor_dialog import ProfileEditorDialog
        dlg = ProfileEditorDialog(self.profile_manager, profile_to_edit=profile, parent=self)
        if dlg.exec() == QDialog.Accepted and dlg.saved_profile_id:
            self.refresh_data()
            idx = self.loc_combo.findData(dlg.saved_profile_id)
            if idx >= 0:
                self.loc_combo.setCurrentIndex(idx)

    def _on_card_clicked(self, session: MissionSession):
        self.selected_session = session
        for w in self.card_widgets:
            w.set_selected(w.session.session_id == session.session_id)

    def _on_start_new_clicked(self):
        profile_id = self.loc_combo.currentData()
        if not profile_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir hedef lokasyon seçiniz.")
            return

        profile = self.profile_manager.load_profile(profile_id)
        if not profile:
            QMessageBox.critical(self, "Hata", "Seçilen lokasyon profili yüklenemedi!")
            return

        operator_name = self.op_input.text().strip() or "Saha_Operatoru"

        reply = QMessageBox.question(
            self,
            "Yeni Faaliyet Başlat",
            f"Lokasyon: {profile.name}\n"
            f"Operatör: {operator_name}\n\n"
            "Yeni faaliyet kaydı açılsın ve 1. Aşama başlatılsın mı?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply == QMessageBox.Yes:
            self.start_new_mission.emit(profile, operator_name)

    def _resume_specific_session(self, session: MissionSession):
        profile = self.profile_manager.load_profile(session.location_id)
        if not profile:
            QMessageBox.critical(
                self,
                "Hata",
                f"Bu görevin bağlı olduğu '{session.location_id}' lokasyon profili bulunamadı!"
            )
            return

        if session.stage2_completed or session.current_stage == 3:
            resume_stage = 3
            stage_desc = "3. Aşama: Faaliyet Sonu ve Log Toplama"
        elif session.stage1_completed or session.current_stage == 2:
            resume_stage = 2
            stage_desc = "2. Aşama: Faaliyet Başlangıcı"
        else:
            resume_stage = 1
            stage_desc = "1. Aşama: Yola Çıkış ve Ön Kontroller"

        reply = QMessageBox.question(
            self,
            "Faaliyete Devam Et",
            f"Görev ID: {session.session_id}\n"
            f"Lokasyon: {profile.name}\n"
            f"Operatör: {session.operator_name}\n"
            f"Kaldığı Aşama: {stage_desc}\n\n"
            "Bu aşamadan faaliyete devam edilsin mi?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply == QMessageBox.Yes:
            self.resume_mission.emit(session, profile, resume_stage)

    def _delete_specific_session(self, session: MissionSession):
        reply = QMessageBox.question(
            self,
            "Görevi Sil",
            f"'{session.session_id}' numaralı saha görevi ve tüm arşivleri silinecektir.\n\n"
            "Onaylıyor musunuz?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.mission_manager.delete_session(session.session_id)
            self.refresh_data()
