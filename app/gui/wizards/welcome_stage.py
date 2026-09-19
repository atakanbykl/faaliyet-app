"""
FieldOps Assistant - Modern Launchpad & Görev Başlatıcı (Welcome & Mission Selection)
Dikey kaydırılabilir tekil ana alan (FieldOps Assistant dışındaki tüm alan), ince kontrol merkezi başlığı,
dikine genişletilmiş yan yana Yeni Faaliyet ve Kayıtlı Faaliyetler kartları ve altta tam genişlikte
Hafızadaki Yazılımlar & Versiyonlar ağacı.
"""

from __future__ import annotations
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QLineEdit, QFrame, QScrollArea, QMessageBox, QDialog,
    QSizePolicy, QPushButton
)

from app.core.asset_manager import SoftwareAssetManager
from app.core.equipment_manager import EquipmentCatalogManager
from app.core.mission_context import MissionManager
from app.core.models import LocationProfile, MissionSession, StoredSoftwareInfo
from app.core.profile_manager import ProfileManager
from app.gui.widgets.mission_card import MissionCardWidget
from app.gui.widgets.touch_button import TouchButton


class CollapsibleCardFrame(QFrame):
    """Genişletilebilir / daraltılabilir kart çerçevesi. Daraltılmış durumdayken herhangi bir yerine tıklanırsa genişletilir."""
    def __init__(self, is_expanded_fn, toggle_callback, parent=None):
        super().__init__(parent)
        self._is_expanded_fn = is_expanded_fn
        self._toggle_callback = toggle_callback

    def mousePressEvent(self, event):
        if not self._is_expanded_fn() and event.button() == Qt.LeftButton:
            self._toggle_callback()
            return
        super().mousePressEvent(event)


class CollapsibleHeaderFrame(QFrame):
    """Tıklanabilir başlık alanı. Tıklandığında genişletme/daraltma tetikler."""
    def __init__(self, toggle_callback, parent=None):
        super().__init__(parent)
        self._toggle_callback = toggle_callback
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Doğrudan aksiyon butonlarına tıklandıysa ana toggle çağrısını engelle
            child = self.childAt(event.pos())
            if isinstance(child, (TouchButton, QPushButton)):
                super().mousePressEvent(event)
                return
            self._toggle_callback()
            return
        super().mousePressEvent(event)


class MissionSelectionWidget(QWidget):
    """İlk açılışta faaliyet sorgulama, hafızadaki yazılımları listeleme ve modern kart listesiyle devam ettirme ekranı."""
    start_new_mission = Signal(LocationProfile, str)
    resume_mission = Signal(MissionSession, LocationProfile, int)

    def __init__(
        self,
        profile_manager: ProfileManager,
        mission_manager: MissionManager,
        asset_manager: Optional[SoftwareAssetManager] = None,
        equipment_manager: Optional[EquipmentCatalogManager] = None,
        parent=None
    ):
        super().__init__(parent)
        self.profile_manager = profile_manager
        self.mission_manager = mission_manager
        self.asset_manager = asset_manager or SoftwareAssetManager()
        self.equipment_manager = equipment_manager or EquipmentCatalogManager()

        self.profiles: List[LocationProfile] = []
        self.saved_sessions: List[MissionSession] = []
        self.selected_session: Optional[MissionSession] = None
        self.card_widgets: List[MissionCardWidget] = []
        self.software_widgets: List[QWidget] = []
        self.is_soft_expanded: bool = False  # Default olarak daraltılmış

        self._setup_ui()
        self.refresh_data()

    def _setup_ui(self):
        # Dış Kök Düzen
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # =========================================================================
        # ANA SAYFA TEK DİKEY KAYDIRMA ALANI (FieldOps Assistant dışındaki tüm alan)
        # Sadece yukarı/aşağı kayar, yatay kaydırma kesinlikle kapalıdır.
        # =========================================================================
        self.page_scroll_area = QScrollArea(self)
        self.page_scroll_area.setWidgetResizable(True)
        self.page_scroll_area.setFrameShape(QFrame.NoFrame)
        self.page_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.page_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.scroll_content = QWidget()
        self.scroll_content.setObjectName("WelcomeScrollContent")
        content_layout = QVBoxLayout(self.scroll_content)
        content_layout.setContentsMargins(20, 10, 20, 16)
        content_layout.setSpacing(12)

        # -------------------------------------------------------------------------
        # 1. BAŞLIK BARI (Saha Operasyon Kontrol Merkezi - İçerik Yüksekliğine Göre Dinamik)
        # -------------------------------------------------------------------------
        header = QFrame()
        header.setObjectName("WelcomeHeader")
        header.setStyleSheet("""
            QFrame#WelcomeHeader {
                background-color: #0f172a;
                border: 1px solid #1e293b;
                border-radius: 10px;
                padding: 4px 8px;
            }
        """)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(14, 8, 14, 8)
        h_layout.setSpacing(12)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)

        title = QLabel("Saha Operasyon Kontrol Merkezi")
        title.setStyleSheet("font-size: 15px; font-weight: 700; color: #f8fafc; letter-spacing: -0.2px;")
        title_col.addWidget(title)

        subtitle = QLabel("Yeni bir saha görevi başlatabilir, hafızadaki yazılımları yönetebilir veya kayıtlı faaliyete devam edebilirsiniz.")
        subtitle.setStyleSheet("color: #94a3b8; font-size: 12px;")
        title_col.addWidget(subtitle)

        h_layout.addLayout(title_col)
        h_layout.addStretch()

        self.lbl_stats = QLabel("0 Kayıtlı Görev")
        self.lbl_stats.setProperty("class", "PillBadge PillInfo")
        self.lbl_stats.setStyleSheet("font-size: 12px; font-weight: 600; padding: 4px 12px;")
        h_layout.addWidget(self.lbl_stats)

        # Başlığın pencere boyutuna göre dikeyde esnemesini engelle; içeriğinin doğal yüksekliğine fixle
        header.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        header.setFixedHeight(header.sizeHint().height())

        content_layout.addWidget(header)

        # =========================================================================
        # 2. ÜST BÖLÜM: YENİ FAALİYET (SOL) + KAYITLI FAALİYETLER (SAĞ) YANYANA
        # Dikine daha ferah alan kaplar (345px)
        # =========================================================================
        top_row = QHBoxLayout()
        top_row.setSpacing(14)

        # -------------------------------------------------------------------------
        # KART 1: YENİ FAALİYET BAŞLAT (SOL)
        # -------------------------------------------------------------------------
        new_card = QFrame()
        new_card.setProperty("class", "ModernCard")
        new_card.setMinimumHeight(345)
        new_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        new_card_layout = QVBoxLayout(new_card)
        new_card_layout.setContentsMargins(20, 16, 20, 16)
        new_card_layout.setSpacing(10)

        card1_header = QHBoxLayout()
        card1_title = QLabel("Yeni Faaliyet Başlat")
        card1_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #60a5fa;")
        card1_header.addWidget(card1_title)
        card1_header.addStretch()
        new_card_layout.addLayout(card1_header)

        card1_desc = QLabel("Hedef istasyon ve operatör bilgisiyle yeni bir saha görevi başlatın.")
        card1_desc.setStyleSheet("color: #94a3b8; font-size: 12px;")
        new_card_layout.addWidget(card1_desc)

        # Lokasyon Seçimi
        loc_header = QHBoxLayout()
        lbl_loc = QLabel("Hedef Görev Lokasyonu:")
        lbl_loc.setStyleSheet("font-weight: 600; color: #f8fafc; font-size: 12.5px;")
        loc_header.addWidget(lbl_loc)
        loc_header.addStretch()

        self.btn_new_loc = TouchButton("+ Yeni", variant="ghost")
        self.btn_new_loc.setFixedHeight(24)
        self.btn_new_loc.setStyleSheet("min-height: 22px; padding: 2px 8px; font-size: 12px; font-weight: 600; color: #60a5fa; border-color: rgba(59, 130, 246, 0.4); border-radius: 5px;")
        self.btn_new_loc.setToolTip("Yeni Hedef Lokasyon Profili Tanımla")
        self.btn_new_loc.clicked.connect(self._on_create_location_clicked)
        loc_header.addWidget(self.btn_new_loc)

        self.btn_edit_loc = TouchButton("Düzenle", variant="ghost")
        self.btn_edit_loc.setFixedHeight(24)
        self.btn_edit_loc.setStyleSheet("min-height: 22px; padding: 2px 8px; font-size: 12px; font-weight: 500; border-radius: 5px;")
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

        # Operatör ve Görevi Başlat Butonu
        action_row = QHBoxLayout()
        action_row.setSpacing(12)

        op_col = QVBoxLayout()
        op_col.setSpacing(3)
        lbl_op = QLabel("Saha Operatörü:")
        lbl_op.setStyleSheet("font-weight: 600; color: #f8fafc; font-size: 12px;")
        op_col.addWidget(lbl_op)

        self.op_input = QLineEdit()
        self.op_input.setPlaceholderText("Operatör adı...")
        self.op_input.setText("Saha Mühendisi")
        op_col.addWidget(self.op_input)
        action_row.addLayout(op_col, 5)

        btn_col = QVBoxLayout()
        btn_col.setSpacing(3)
        lbl_dummy = QLabel("")
        lbl_dummy.setStyleSheet("font-size: 12px;")
        btn_col.addWidget(lbl_dummy)

        self.btn_start_new = TouchButton("Görevi Başlat  ➔", variant="primary")
        self.btn_start_new.setFixedHeight(38)
        self.btn_start_new.setStyleSheet("font-size: 13px; font-weight: 700; padding: 4px 16px;")
        self.btn_start_new.clicked.connect(self._on_start_new_clicked)
        btn_col.addWidget(self.btn_start_new)
        action_row.addLayout(btn_col, 5)

        new_card_layout.addLayout(action_row)
        new_card_layout.addStretch()

        top_row.addWidget(new_card, 5)

        # -------------------------------------------------------------------------
        # KART 2: KAYITLI FAALİYETLER (SAĞ)
        # -------------------------------------------------------------------------
        resume_card = QFrame()
        resume_card.setProperty("class", "ModernCard")
        resume_card.setMinimumHeight(345)
        resume_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        resume_layout = QVBoxLayout(resume_card)
        resume_layout.setContentsMargins(20, 16, 20, 16)
        resume_layout.setSpacing(10)

        card2_header = QHBoxLayout()
        card2_title = QLabel("Kayıtlı Faaliyetler")
        card2_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #34d399;")
        card2_header.addWidget(card2_title)
        card2_header.addStretch()

        lbl_hint = QLabel("Devam etmek için bir göreve tıklayın")
        lbl_hint.setStyleSheet("color: #94a3b8; font-size: 12px;")
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
        self.cards_list_layout.setSpacing(8)

        self.scroll_area.setWidget(self.cards_container)
        resume_layout.addWidget(self.scroll_area, 1)

        # Boş Durum Bilgisi (Empty State)
        self.empty_state_lbl = QLabel(
            " Henüz kayıtlı bir geçmiş faaliyet bulunmuyor.<br>"
            "<span style='color: #94a3b8;'>Sol panelden yeni bir saha faaliyeti başlatabilirsiniz.</span>"
        )
        self.empty_state_lbl.setAlignment(Qt.AlignCenter)
        self.empty_state_lbl.setStyleSheet("color: #94a3b8; font-size: 12px; line-height: 1.5; padding: 40px;")
        self.empty_state_lbl.setVisible(False)
        resume_layout.addWidget(self.empty_state_lbl)

        top_row.addWidget(resume_card, 5)
        content_layout.addLayout(top_row)

        # =========================================================================
        # 3. ALT BÖLÜM: HAFIZADAKİ YAZILIMLAR (Açılır / Kapanır - Default Daraltılmış)
        # =========================================================================
        self.soft_card = CollapsibleCardFrame(lambda: self.is_soft_expanded, self._toggle_softwares_expanded)
        self.soft_card.setObjectName("SoftwaresCard")
        self.soft_card.setProperty("class", "ModernCard")
        self.soft_card.setMinimumHeight(0)
        self.soft_card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.soft_card.setCursor(Qt.PointingHandCursor)

        soft_layout = QVBoxLayout(self.soft_card)
        soft_layout.setContentsMargins(18, 12, 18, 12)
        soft_layout.setSpacing(8)

        # Tıklanabilir Başlık Çubuğu
        self.soft_header_frame = CollapsibleHeaderFrame(self._toggle_softwares_expanded)
        self.soft_header_frame.setObjectName("SoftHeaderFrame")
        self.soft_header_frame.setStyleSheet("""
            QFrame#SoftHeaderFrame {
                background-color: transparent;
                border-radius: 8px;
            }
            QFrame#SoftHeaderFrame:hover {
                background-color: rgba(30, 41, 59, 0.45);
            }
        """)

        soft_header = QHBoxLayout(self.soft_header_frame)
        soft_header.setContentsMargins(4, 2, 4, 2)
        soft_header.setSpacing(10)

        self.lbl_soft_arrow = QLabel("▶")
        self.lbl_soft_arrow.setStyleSheet("font-size: 13px; font-weight: 700; color: #38bdf8;")
        self.lbl_soft_arrow.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        soft_header.addWidget(self.lbl_soft_arrow)

        soft_title = QLabel("Hafızadaki Yazılımlar")
        soft_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #38bdf8;")
        soft_title.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        soft_header.addWidget(soft_title)

        self.lbl_softwares_count = QLabel("0 Sürüm")
        self.lbl_softwares_count.setProperty("class", "PillBadge PillInfo")
        self.lbl_softwares_count.setStyleSheet("font-size: 12px; padding: 2px 8px;")
        self.lbl_softwares_count.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        soft_header.addWidget(self.lbl_softwares_count)

        self.lbl_soft_hint = QLabel("(İçeriği görüntülemek için tıklayın)")
        self.lbl_soft_hint.setStyleSheet("color: #94a3b8; font-size: 12px;")
        self.lbl_soft_hint.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        soft_header.addWidget(self.lbl_soft_hint)

        soft_header.addStretch()

        self.btn_refresh_soft = TouchButton("Yenile", variant="ghost")
        self.btn_refresh_soft.setFixedHeight(26)
        self.btn_refresh_soft.setStyleSheet("min-height: 24px; padding: 2px 10px; font-size: 12px; border-radius: 6px;")
        self.btn_refresh_soft.setToolTip("softwares/ klasörünü yeniden tara")
        self.btn_refresh_soft.clicked.connect(self._refresh_softwares)
        soft_header.addWidget(self.btn_refresh_soft)

        self.btn_open_soft_dir = TouchButton("Klasörü Aç", variant="ghost")
        self.btn_open_soft_dir.setFixedHeight(26)
        self.btn_open_soft_dir.setStyleSheet("min-height: 24px; padding: 2px 10px; font-size: 12px; border-radius: 6px; color: #38bdf8; border-color: rgba(56, 189, 248, 0.35);")
        self.btn_open_soft_dir.setToolTip("softwares/ kök klasörünü dosya gezgininde aç")
        self.btn_open_soft_dir.clicked.connect(self._on_open_softwares_folder)
        soft_header.addWidget(self.btn_open_soft_dir)

        self.btn_soft_toggle = TouchButton("▶ Genişlet", variant="ghost")
        self.btn_soft_toggle.setFixedHeight(26)
        self.btn_soft_toggle.setStyleSheet("min-height: 24px; padding: 2px 12px; font-size: 12px; font-weight: 600; border-radius: 6px; color: #38bdf8; border-color: rgba(56, 189, 248, 0.4);")
        self.btn_soft_toggle.setToolTip("Hafızadaki yazılımlar listesini genişlet / daralt")
        self.btn_soft_toggle.clicked.connect(self._toggle_softwares_expanded)
        soft_header.addWidget(self.btn_soft_toggle)

        soft_layout.addWidget(self.soft_header_frame)

        # -------------------------------------------------------------------------
        # Gövde Konteyneri (soft_body): Default olarak daraltılmış (gizli)
        # -------------------------------------------------------------------------
        self.soft_body = QWidget()
        self.soft_body_layout = QVBoxLayout(self.soft_body)
        self.soft_body_layout.setContentsMargins(0, 6, 0, 0)
        self.soft_body_layout.setSpacing(10)

        soft_desc = QLabel("Taşınabilir diskteki <code>softwares/&lt;uygulama&gt;/&lt;versiyon&gt;</code> hiyerarşisi taranarak tüm ana ve yardımcı yazılımlar listelenir.")
        soft_desc.setStyleSheet("color: #94a3b8; font-size: 12px;")
        self.soft_body_layout.addWidget(soft_desc)

        # Scrollable Yazılım Paketleri Listesi
        self.soft_scroll = QScrollArea()
        self.soft_scroll.setWidgetResizable(True)
        self.soft_scroll.setFrameShape(QFrame.NoFrame)
        self.soft_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.soft_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.soft_scroll.setMinimumHeight(260)

        self.soft_container = QWidget()
        self.soft_list_layout = QVBoxLayout(self.soft_container)
        self.soft_list_layout.setContentsMargins(0, 0, 6, 0)
        self.soft_list_layout.setSpacing(10)

        self.soft_scroll.setWidget(self.soft_container)
        self.soft_body_layout.addWidget(self.soft_scroll, 1)

        # Boş Durum Bilgisi (Software Empty State)
        self.soft_empty_lbl = QLabel(
            " <b>softwares/</b> klasöründe henüz paket bulunamadı.<br>"
            "<span style='color: #94a3b8;'>Paketleri (.tar.gz, .zip vb.) klasöre bırakıp 'Yenile' butonuna basabilirsiniz.</span>"
        )
        self.soft_empty_lbl.setAlignment(Qt.AlignCenter)
        self.soft_empty_lbl.setStyleSheet("color: #94a3b8; font-size: 12.5px; line-height: 1.5; padding: 24px;")
        self.soft_empty_lbl.setVisible(False)
        self.soft_body_layout.addWidget(self.soft_empty_lbl)

        # Default olarak kapalı
        self.soft_body.setVisible(False)
        soft_layout.addWidget(self.soft_body)

        content_layout.addWidget(self.soft_card)
        content_layout.addStretch(1)

        self.page_scroll_area.setWidget(self.scroll_content)
        root_layout.addWidget(self.page_scroll_area)

    def refresh_data(self):
        """Profilleri, yazılım havuzunu ve kayıtlı oturumları diskten yükler."""
        # 1. Lokasyon profilleri
        self.profiles = self.profile_manager.list_profiles()
        self.loc_combo.clear()
        for p in self.profiles:
            self.loc_combo.addItem(f"{p.name} ({p.id})", p.id)
        self._on_profile_preview()

        # 2. Kayıtlı oturumlar
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

        # 3. Hafızadaki yazılımlar
        self._refresh_softwares()

    def _refresh_softwares(self):
        """softwares/<app>/<version> hiyerarşisini tarar ve arayüzdeki yazılım listesini gruplandırarak günceller."""
        while self.soft_list_layout.count():
            item = self.soft_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.software_widgets.clear()

        grouped = self.asset_manager.scan_softwares_grouped()
        all_items = [v for versions in grouped.values() for v in versions]
        total_count = len(all_items)
        ready_count = sum(1 for s in all_items if not s.is_empty)
        empty_count = sum(1 for s in all_items if s.is_empty)

        if empty_count > 0:
            self.lbl_softwares_count.setText(f"{len(grouped)} Yazılım • {total_count} Sürüm ({ready_count} Hazır, {empty_count} Boş )")
            self.lbl_softwares_count.setProperty("class", "PillBadge PillWarning")
        else:
            self.lbl_softwares_count.setText(f"{len(grouped)} Yazılım • {total_count} Sürüm (Hazır)")
            self.lbl_softwares_count.setProperty("class", "PillBadge PillSuccess")
        self.lbl_softwares_count.style().unpolish(self.lbl_softwares_count)
        self.lbl_softwares_count.style().polish(self.lbl_softwares_count)

        if not grouped:
            self.soft_empty_lbl.setVisible(True)
            self.soft_scroll.setVisible(False)
        else:
            self.soft_empty_lbl.setVisible(False)
            self.soft_scroll.setVisible(True)

            for app_name, versions in grouped.items():
                group_widget = self._create_app_group_widget(app_name, versions)
                self.software_widgets.append(group_widget)
                self.soft_list_layout.addWidget(group_widget)

            self.soft_list_layout.addStretch()

        # Kartın açık/kapalı durumuna göre gövde görünürlüğünü koru
        self.soft_body.setVisible(self.is_soft_expanded)

    def _toggle_softwares_expanded(self):
        """Hafızadaki yazılımlar kartını genişletir veya daraltır."""
        self.is_soft_expanded = not self.is_soft_expanded
        self._update_softwares_expanded_state()

    def _update_softwares_expanded_state(self):
        """Açık/kapalı durumuna göre arayüz elemanlarını günceller."""
        if self.is_soft_expanded:
            self.soft_card.setCursor(Qt.ArrowCursor)
            self.soft_body.setVisible(True)
            self.soft_card.setMinimumHeight(360)
            self.soft_card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
            self.lbl_soft_arrow.setText("▼")
            self.lbl_soft_hint.setText("(Daraltmak için tıklayın)")
            self.btn_soft_toggle.setText("▼ Daralt")
            self.btn_soft_toggle.setToolTip("Hafızadaki yazılımlar listesini daralt")
        else:
            self.soft_card.setCursor(Qt.PointingHandCursor)
            self.soft_body.setVisible(False)
            self.soft_card.setMinimumHeight(0)
            self.soft_card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
            self.lbl_soft_arrow.setText("▶")
            self.lbl_soft_hint.setText("(İçeriği görüntülemek için tıklayın)")
            self.btn_soft_toggle.setText("▶ Genişlet")
            self.btn_soft_toggle.setToolTip("Hafızadaki yazılımlar listesini genişlet")

    def _create_app_group_widget(self, app_name: str, versions: List[StoredSoftwareInfo]) -> QWidget:
        """Belirli bir uygulama ve ona ait versiyonlar için ağaç formatında grup kartı oluşturur."""
        group_frame = QFrame()
        group_frame.setStyleSheet("""
            QFrame.AppGroupCard {
                background-color: #0f172a;
                border: 1px solid #1e293b;
                border-radius: 9px;
            }
        """)
        group_frame.setProperty("class", "AppGroupCard")

        group_layout = QVBoxLayout(group_frame)
        group_layout.setContentsMargins(16, 12, 16, 12)
        group_layout.setSpacing(10)

        # 1. Başlık Satırı (Uygulama Adı, Sürüm Sayısı Rozeti, Klasörü Aç Butonu)
        header_row = QHBoxLayout()
        header_row.setSpacing(10)

        app_icon = QLabel("")
        app_icon.setStyleSheet("font-size: 19px;")
        header_row.addWidget(app_icon)

        name_col = QVBoxLayout()
        name_col.setSpacing(2)
        name_lbl = QLabel(app_name)
        name_lbl.setStyleSheet("font-size: 14px; font-weight: 700; color: #f8fafc;")
        name_col.addWidget(name_lbl)

        path_lbl = QLabel(f"softwares/{app_name}/")
        path_lbl.setStyleSheet("font-size: 12px; color: #94a3b8; font-family: monospace;")
        name_col.addWidget(path_lbl)
        header_row.addLayout(name_col)

        header_row.addStretch()

        # Versiyon Sayaç Rozeti
        ready_count = sum(1 for v in versions if not v.is_empty)
        empty_count = sum(1 for v in versions if v.is_empty)
        if empty_count > 0:
            badge_text = f"{len(versions)} Sürüm ({ready_count} Hazır, {empty_count} Boş )"
            badge_cls = "PillBadge PillWarning"
        else:
            badge_text = f"{len(versions)} Sürüm (Hazır)"
            badge_cls = "PillBadge PillSuccess"

        v_badge = QLabel(badge_text)
        v_badge.setProperty("class", badge_cls)
        v_badge.setStyleSheet("font-size: 10.5px; font-weight: 600; padding: 2px 8px;")
        header_row.addWidget(v_badge)

        # Uygulama Dizinini Aç Butonu
        app_dir_path = str(self.asset_manager.packages_dir / app_name)
        btn_app_dir = TouchButton("Klasörü Aç", variant="ghost")
        btn_app_dir.setFixedHeight(26)
        btn_app_dir.setStyleSheet("min-height: 24px; padding: 2px 10px; font-size: 12px; border-radius: 6px;")
        btn_app_dir.setToolTip(f"'{app_name}' uygulamasının klasörünü aç")
        btn_app_dir.clicked.connect(lambda checked=False, p=app_dir_path: QDesktopServices.openUrl(QUrl.fromLocalFile(p)))
        header_row.addWidget(btn_app_dir)

        group_layout.addLayout(header_row)

        # 2. Versiyonlar Listesi (Ağaç formatında sol çizgi ile girintili)
        tree_container = QWidget()
        tree_layout = QVBoxLayout(tree_container)
        tree_layout.setContentsMargins(16, 2, 2, 2)
        tree_layout.setSpacing(6)
        tree_container.setStyleSheet("""
            QWidget {
                border-left: 2px solid #334155;
                margin-left: 10px;
            }
        """)

        for idx, v_item in enumerate(versions):
            is_last = (idx == len(versions) - 1)
            v_widget = self._create_version_item_widget(v_item, is_last=is_last)
            tree_layout.addWidget(v_widget)

        group_layout.addWidget(tree_container)
        return group_frame

    def _create_version_item_widget(self, item: StoredSoftwareInfo, is_last: bool = False) -> QWidget:
        """Uygulama ağacında listelenecek her bir versiyon satırı (Tam ekran genişliğine yayılmış)."""
        frame = QFrame()
        if item.is_empty:
            frame.setStyleSheet("""
                QFrame {
                    background-color: rgba(245, 158, 11, 0.04);
                    border: 1px dashed rgba(245, 158, 11, 0.4);
                    border-radius: 6px;
                }
                QFrame:hover {
                    border: 1px solid #f59e0b;
                    background-color: rgba(245, 158, 11, 0.08);
                }
            """)
        else:
            frame.setStyleSheet("""
                QFrame {
                    background-color: rgba(30, 41, 59, 0.65);
                    border: 1px solid #1e293b;
                    border-radius: 6px;
                }
                QFrame:hover {
                    border-color: #38bdf8;
                    background-color: rgba(30, 41, 59, 0.95);
                }
            """)

        row = QHBoxLayout(frame)
        row.setContentsMargins(12, 8, 12, 8)
        row.setSpacing(12)

        # Ağaç Bağlantı Çizgisi Simge
        branch_icon = QLabel("└──" if is_last else "├──")
        branch_icon.setStyleSheet("color: #94a3b8; font-family: monospace; font-size: 13px; font-weight: bold;")
        row.addWidget(branch_icon)

        # Versiyon Rozeti
        v_lbl = QLabel(item.version_name)
        if item.is_empty:
            v_lbl.setStyleSheet(
                "background-color: rgba(245, 158, 11, 0.15); color: #fbbf24; "
                "border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 4px; "
                "padding: 2px 8px; font-size: 12px; font-weight: 700;"
            )
        else:
            v_lbl.setStyleSheet(
                "background-color: rgba(56, 189, 248, 0.15); color: #38bdf8; "
                "border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 4px; "
                "padding: 2px 8px; font-size: 12px; font-weight: 700;"
            )
        row.addWidget(v_lbl)

        # Bilgi Satırı
        if item.is_empty:
            meta_lbl = QLabel(
                "<span style='color: #f59e0b; font-weight: 600;'> İçi Boş</span> "
                "<span style='color: #94a3b8;'>— Bu versiyon klasöründe kurulabilir paket dosyası (.tar.gz, .zip vb.) bulunmuyor</span> &nbsp;•&nbsp; "
                f"<span style='color: #94a3b8; font-family: monospace;'>softwares/{item.relative_path}</span>"
            )
        else:
            pkg_name = item.primary_package or (item.files[0] if item.files else "Paket Dosyası")
            more_str = f" <span style='color: #94a3b8;'>(+{item.file_count - 1} ek dosya)</span>" if item.file_count > 1 else ""
            meta_lbl = QLabel(
                f" <b style='color: #f1f5f9;'>{pkg_name}</b>{more_str} &nbsp;&nbsp;•&nbsp;&nbsp; "
                f"⚖️ <b style='color: #cbd5e1;'>{item.formatted_size}</b> &nbsp;&nbsp;•&nbsp;&nbsp; 🕒 {item.modified_time_str} &nbsp;&nbsp;•&nbsp;&nbsp; "
                f"<span style='color: #94a3b8; font-family: monospace;'>softwares/{item.relative_path}</span>"
            )
        meta_lbl.setStyleSheet("font-size: 12px;")
        row.addWidget(meta_lbl)

        row.addStretch()

        # Durum Rozeti
        if item.is_empty:
            status_badge = QLabel("Paket Yok")
            status_badge.setProperty("class", "PillBadge PillWarning")
            status_badge.setStyleSheet("font-size: 10px; font-weight: 700; padding: 2px 8px;")
        else:
            status_badge = QLabel("✓ Hazır")
            status_badge.setProperty("class", "PillBadge PillSuccess")
            status_badge.setStyleSheet("font-size: 10px; font-weight: 700; padding: 2px 8px;")
        row.addWidget(status_badge)

        # Klasörü Aç Butonu (Geniş & Rahat Tıklanabilir)
        btn_v_folder = TouchButton("Klasörü Aç", variant="ghost")
        btn_v_folder.setFixedHeight(26)
        btn_v_folder.setStyleSheet("font-size: 12px; padding: 2px 8px; min-height: 24px; border-radius: 5px;")
        btn_v_folder.setToolTip(f"'{item.relative_path}' versiyon klasörünü aç")
        target_f = item.folder_path
        btn_v_folder.clicked.connect(lambda checked=False, f=target_f: QDesktopServices.openUrl(QUrl.fromLocalFile(f)))
        row.addWidget(btn_v_folder)

        return frame

    def _on_open_softwares_folder(self):
        """softwares/ kök klasörünü işletim sisteminin dosya yöneticisinde açar."""
        folder = self.asset_manager.packages_dir
        if folder.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder.resolve())))
        else:
            QMessageBox.warning(self, "Uyarı", f"'{folder}' klasörü bulunamadı!")

    def _on_profile_preview(self):
        profile_id = self.loc_combo.currentData()
        if not profile_id:
            return
        p = next((x for x in self.profiles if x.id == profile_id), None)
        if p:
            self.loc_preview_lbl.setText(f"Hedef: {p.target_device.username}@{p.target_device.host} &nbsp;•&nbsp; {p.description}")

    def _on_create_location_clicked(self):
        from app.gui.widgets.profile_editor_dialog import ProfileEditorDialog
        dlg = ProfileEditorDialog(
            self.profile_manager,
            profile_to_edit=None,
            asset_manager=self.asset_manager,
            equipment_manager=self.equipment_manager,
            parent=self
        )
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
        dlg = ProfileEditorDialog(
            self.profile_manager,
            profile_to_edit=profile,
            asset_manager=self.asset_manager,
            equipment_manager=self.equipment_manager,
            parent=self
        )
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
