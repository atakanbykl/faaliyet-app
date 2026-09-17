"""
FieldOps Assistant - Modern ve Reaktif Kontrol Listesi Bileşeni (Interactive Task Cards)
Görev maddelerine tıklanarak işaretlenen akıcı kartlar, geniş ve ferah görünüm.
"""

from __future__ import annotations
from typing import List
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QScrollArea, QSizePolicy
)

from app.core.models import EquipmentItem
from app.gui.widgets.touch_button import TouchButton


class ChecklistItemWidget(QFrame):
    """Tek bir kontrol listesi satırı - Reaktif ve tıklanabilir modern görev kartı."""
    toggled = Signal(bool)

    def __init__(self, item: EquipmentItem, parent=None):
        super().__init__(parent)
        self.item = item
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(52)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(14)

        # 1. Dairesel Onay Butonu / İkonu
        self.check_circle = QLabel(self)
        self.check_circle.setFixedSize(26, 26)
        self.check_circle.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.check_circle)

        # 2. Başlık ve Açıklama Kolonu
        text_layout = QVBoxLayout()
        text_layout.setSpacing(3)

        title_row = QHBoxLayout()
        title_row.setSpacing(10)

        self.title_lbl = QLabel(item.name)
        self.title_lbl.setStyleSheet("font-size: 14px; font-weight: 600; color: #f8fafc;")
        title_row.addWidget(self.title_lbl)

        # Zorunlu / Opsiyonel Rozeti
        self.badge_lbl = QLabel()
        if item.is_mandatory:
            self.badge_lbl.setText("Zorunlu")
            self.badge_lbl.setProperty("class", "PillBadge PillDanger")
        else:
            self.badge_lbl.setText("Opsiyonel")
            self.badge_lbl.setProperty("class", "PillBadge PillMuted")
        title_row.addWidget(self.badge_lbl)
        title_row.addStretch()
        text_layout.addLayout(title_row)

        if item.description:
            self.desc_lbl = QLabel(item.description)
            self.desc_lbl.setStyleSheet("color: #94a3b8; font-size: 12px; line-height: 1.4;")
            text_layout.addWidget(self.desc_lbl)

        layout.addLayout(text_layout, 1)
        self._update_appearance()

    def _update_appearance(self):
        if self.item.is_checked:
            self.check_circle.setText("✓")
            self.check_circle.setStyleSheet("""
                background-color: #10b981;
                color: #ffffff;
                border-radius: 13px;
                font-weight: bold;
                font-size: 13px;
            """)
            self.setStyleSheet("""
                QFrame {
                    background-color: rgba(16, 185, 129, 0.08);
                    border: 1px solid rgba(16, 185, 129, 0.35);
                    border-radius: 10px;
                }
            """)
            self.title_lbl.setStyleSheet("font-size: 14px; font-weight: 500; color: #94a3b8;")
        else:
            self.check_circle.setText("")
            self.check_circle.setStyleSheet("""
                background-color: #0b1120;
                border: 2px solid #475569;
                border-radius: 13px;
            """)
            self.setStyleSheet("""
                QFrame {
                    background-color: #0f172a;
                    border: 1px solid #1e293b;
                    border-radius: 10px;
                }
                QFrame:hover {
                    background-color: #141f36;
                    border-color: #3b82f6;
                }
            """)
            self.title_lbl.setStyleSheet("font-size: 14px; font-weight: 600; color: #f8fafc;")

    def mousePressEvent(self, event):
        self.item.is_checked = not self.item.is_checked
        self._update_appearance()
        self.toggled.emit(self.item.is_checked)
        super().mousePressEvent(event)

    def set_checked(self, checked: bool):
        self.item.is_checked = checked
        self._update_appearance()

    def is_checked(self) -> bool:
        return self.item.is_checked


class ChecklistWidget(QWidget):
    """Tüm kontrol listesini barındıran scroll edilebilir reaktif bileşen."""
    checklist_updated = Signal()

    def __init__(self, items: List[EquipmentItem], parent=None):
        super().__init__(parent)
        self.items = items
        self.item_widgets: List[ChecklistItemWidget] = []

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumHeight(280)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(12)

        # Üst Bilgi ve Hızlı İşlem Barı
        top_bar = QHBoxLayout()
        self.counter_lbl = QLabel(self)
        self.counter_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #60a5fa;")
        top_bar.addWidget(self.counter_lbl)
        top_bar.addStretch()

        select_all_btn = TouchButton("Tümünü Seç", variant="ghost")
        select_all_btn.setFixedHeight(32)
        select_all_btn.setStyleSheet("font-size: 12px; padding: 2px 12px; min-height: 30px;")
        select_all_btn.clicked.connect(self.select_all)
        top_bar.addWidget(select_all_btn)

        clear_all_btn = TouchButton("Temizle", variant="ghost")
        clear_all_btn.setFixedHeight(32)
        clear_all_btn.setStyleSheet("font-size: 12px; padding: 2px 12px; min-height: 30px;")
        clear_all_btn.clicked.connect(self.clear_all)
        top_bar.addWidget(clear_all_btn)

        main_layout.addLayout(top_bar)

        # Scroll Alanı (Geniş ve rahat görünüm)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        scroll.setMinimumHeight(220)

        container = QWidget()
        self.list_layout = QVBoxLayout(container)
        self.list_layout.setContentsMargins(0, 2, 4, 2)
        self.list_layout.setSpacing(10)

        for item in self.items:
            w = ChecklistItemWidget(item)
            w.toggled.connect(self._on_item_toggled)
            self.item_widgets.append(w)
            self.list_layout.addWidget(w)

        self.list_layout.addStretch()
        scroll.setWidget(container)
        main_layout.addWidget(scroll, 1)

        self._update_counter()

    def _on_item_toggled(self, checked: bool):
        self._update_counter()
        self.checklist_updated.emit()

    def _update_counter(self):
        total = len(self.items)
        checked = sum(1 for w in self.item_widgets if w.is_checked())
        mandatory_total = sum(1 for w in self.item_widgets if w.item.is_mandatory)
        mandatory_checked = sum(1 for w in self.item_widgets if w.item.is_mandatory and w.is_checked())

        if mandatory_checked == mandatory_total and mandatory_total > 0:
            badge_text = "<span style='color:#34d399;'>✓ Zorunlu Ekipmanlar Hazır</span>"
        else:
            badge_text = f"<span style='color:#fbbf24;'>{mandatory_checked}/{mandatory_total} Zorunlu Malzeme</span>"

        self.counter_lbl.setText(f"Seçilen: <b>{checked}/{total}</b> &nbsp;|&nbsp; {badge_text}")

    def select_all(self):
        for w in self.item_widgets:
            w.set_checked(True)
        self._update_counter()
        self.checklist_updated.emit()

    def clear_all(self):
        for w in self.item_widgets:
            w.set_checked(False)
        self._update_counter()
        self.checklist_updated.emit()

    def are_all_mandatory_checked(self) -> bool:
        return all(w.is_checked() for w in self.item_widgets if w.item.is_mandatory)
