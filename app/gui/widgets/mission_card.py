"""
FieldOps Assistant - Etkileşimli Görev Kartı (MissionCardWidget)
Kayıtlı faaliyetleri modern, akıcı ve reaktif kartlar halinde görüntüler.
"""

from __future__ import annotations
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QLabel, QWidget
)

from app.core.models import LocationProfile, MissionSession
from app.gui.widgets.touch_button import TouchButton


class MissionCardWidget(QFrame):
    """Tek bir kayıtlı faaliyeti temsil eden şık, reaktif kart."""
    resume_requested = Signal(MissionSession)
    delete_requested = Signal(MissionSession)
    clicked = Signal(MissionSession)

    def __init__(self, session: MissionSession, profile: LocationProfile | None = None, parent=None):
        super().__init__(parent)
        self.session = session
        self.profile = profile
        self.is_selected = False

        self.setCursor(Qt.PointingHandCursor)
        self.setProperty("class", "ElevatedCard")
        self._setup_ui()
        self._update_appearance()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(14)

        # 1. Sol Aşama Gösterge Halkası
        self.icon_ring = QLabel(self)
        self.icon_ring.setFixedSize(38, 38)
        self.icon_ring.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.icon_ring, 0, Qt.AlignVCenter)

        # 2. Orta Bilgi Kolonu (Başlık ve Alt Metadata)
        info_col = QVBoxLayout()
        info_col.setSpacing(4)
        info_col.setAlignment(Qt.AlignVCenter)

        loc_title = self.profile.name if self.profile else self.session.location_id
        self.title_lbl = QLabel(loc_title)
        self.title_lbl.setStyleSheet("font-size: 15px; font-weight: 700; color: #f8fafc;")
        info_col.addWidget(self.title_lbl)

        # Alt Bilgiler: Operatör, Tarih, ID
        created_date = self.session.created_at[:16] if len(self.session.created_at) >= 16 else self.session.created_at
        short_id = self.session.session_id
        if len(short_id) > 24:
            short_id = short_id[:10] + "…" + short_id[-6:]

        sub_info = f"👤 {self.session.operator_name} &nbsp;•&nbsp; 📅 {created_date} &nbsp;•&nbsp; <code>{short_id}</code>"
        self.sub_lbl = QLabel(sub_info)
        self.sub_lbl.setStyleSheet("font-size: 12px; color: #94a3b8;")
        self.sub_lbl.setWordWrap(True)
        self.sub_lbl.setToolTip(f"Görev ID: {self.session.session_id}\nTarih: {self.session.created_at}\nOperatör: {self.session.operator_name}")
        info_col.addWidget(self.sub_lbl)

        layout.addLayout(info_col, 1)

        # 3. Sağ Kolon (Üstte Rozet, Altta Devam Et + Logolu Silme Butonu)
        right_col = QVBoxLayout()
        right_col.setSpacing(6)
        right_col.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Üst Sıra: Aşama Rozeti
        badge_row = QHBoxLayout()
        badge_row.setContentsMargins(0, 0, 0, 0)
        badge_row.addStretch()
        self.badge_lbl = QLabel()
        self.badge_lbl.setProperty("class", "PillBadge")
        badge_row.addWidget(self.badge_lbl)
        right_col.addLayout(badge_row)

        # Alt Sıra: Aksiyon Butonları (Devam Et + Çöp Kutusu Logolu Sil Butonu)
        btns_row = QHBoxLayout()
        btns_row.setContentsMargins(0, 0, 0, 0)
        btns_row.setSpacing(8)
        btns_row.addStretch()

        self.btn_resume = TouchButton("Devam Et ➔", variant="primary")
        self.btn_resume.setFixedHeight(32)
        self.btn_resume.setStyleSheet("font-size: 13px; font-weight: 700; padding: 2px 14px; min-height: 32px; border-radius: 8px;")
        self.btn_resume.clicked.connect(lambda: self.resume_requested.emit(self.session))
        btns_row.addWidget(self.btn_resume)

        self.btn_del = TouchButton("🗑", variant="delete")
        self.btn_del.setFixedSize(32, 32)
        self.btn_del.setStyleSheet("font-size: 15px; padding: 0px; min-height: 32px; min-width: 32px; border-radius: 8px;")
        self.btn_del.setToolTip("Bu Görev Kaydını Sil")
        self.btn_del.clicked.connect(lambda: self.delete_requested.emit(self.session))
        btns_row.addWidget(self.btn_del)

        right_col.addLayout(btns_row)
        layout.addLayout(right_col, 0)

    def _update_appearance(self):
        s = self.session
        if s.stage3_completed:
            self.icon_ring.setText("✓")
            self.icon_ring.setStyleSheet("""
                background-color: rgba(16, 185, 129, 0.15);
                color: #34d399;
                border: 2px solid #10b981;
                border-radius: 19px;
                font-size: 16px;
                font-weight: bold;
            """)
            self.badge_lbl.setText("Tamamlandı")
            self.badge_lbl.setProperty("class", "PillBadge PillSuccess")
            self.btn_resume.setText("İncele ➔")
            self.btn_resume.set_variant("ghost")
        elif s.stage2_completed or s.current_stage == 3:
            self.icon_ring.setText("3")
            self.icon_ring.setStyleSheet("""
                background-color: rgba(59, 130, 246, 0.15);
                color: #60a5fa;
                border: 2px solid #3b82f6;
                border-radius: 19px;
                font-size: 15px;
                font-weight: bold;
            """)
            self.badge_lbl.setText("Aşama 3: Log Toplama")
            self.badge_lbl.setProperty("class", "PillBadge PillInfo")
            self.btn_resume.setText("Devam Et ➔")
            self.btn_resume.set_variant("primary")
        elif s.stage1_completed or s.current_stage == 2:
            self.icon_ring.setText("2")
            self.icon_ring.setStyleSheet("""
                background-color: rgba(245, 158, 11, 0.15);
                color: #fbbf24;
                border: 2px solid #f59e0b;
                border-radius: 19px;
                font-size: 15px;
                font-weight: bold;
            """)
            self.badge_lbl.setText("Aşama 2: Başlangıç")
            self.badge_lbl.setProperty("class", "PillBadge PillWarning")
            self.btn_resume.setText("Devam Et ➔")
            self.btn_resume.set_variant("primary")
        else:
            self.icon_ring.setText("1")
            self.icon_ring.setStyleSheet("""
                background-color: rgba(148, 163, 184, 0.15);
                color: #cbd5e1;
                border: 2px solid #64748b;
                border-radius: 19px;
                font-size: 15px;
                font-weight: bold;
            """)
            self.badge_lbl.setText("Aşama 1: Ön Hazırlık")
            self.badge_lbl.setProperty("class", "PillBadge PillMuted")
            self.btn_resume.setText("Devam Et ➔")
            self.btn_resume.set_variant("primary")

        self.badge_lbl.style().unpolish(self.badge_lbl)
        self.badge_lbl.style().polish(self.badge_lbl)

    def mousePressEvent(self, event):
        self.clicked.emit(self.session)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        self.resume_requested.emit(self.session)
        super().mouseDoubleClickEvent(event)

    def set_selected(self, selected: bool):
        self.is_selected = selected
        if selected:
            self.setStyleSheet("""
                QFrame.ElevatedCard {
                    background-color: #172440;
                    border: 1.5px solid #3b82f6;
                    border-radius: 12px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame.ElevatedCard {
                    background-color: #111a2e;
                    border: 1px solid #1e293b;
                    border-radius: 12px;
                }
                QFrame.ElevatedCard:hover {
                    background-color: #15223c;
                    border-color: #334155;
                }
            """)

