"""
FieldOps Assistant - Modern Terminal & Canlı Log Görüntüleyici
macOS tarzı pencere noktaları, pürüzsüz Cascadia/Consolas fontu ve yumuşak renk vurguları.
"""

from __future__ import annotations
from datetime import datetime
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel, QFrame
)

from app.gui.widgets.touch_button import TouchButton


class LiveConsoleWidget(QFrame):
    """Gerçek zamanlı komut çıktısı ve log izleme penceresi (Modern Terminal Görünümü)."""

    def __init__(self, title: str = "Terminal & Saha Log Akışı", parent=None):
        super().__init__(parent)
        self.setProperty("class", "ModernCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        # Üst Terminal Başlık Barı (macOS noktaları)
        top_bar = QHBoxLayout()
        top_bar.setSpacing(8)

        dot_layout = QHBoxLayout()
        dot_layout.setSpacing(6)
        for color in ["#ef4444", "#f59e0b", "#10b981"]:
            dot = QLabel()
            dot.setFixedSize(10, 10)
            dot.setStyleSheet(f"background-color: {color}; border-radius: 5px;")
            dot_layout.addWidget(dot)
        top_bar.addLayout(dot_layout)

        title_lbl = QLabel(f"&nbsp; {title}")
        title_lbl.setStyleSheet("color: #94a3b8; font-size: 13px; font-weight: 600;")
        top_bar.addWidget(title_lbl)
        top_bar.addStretch()

        clear_btn = TouchButton("Temizle", variant="ghost")
        clear_btn.setFixedHeight(28)
        clear_btn.setStyleSheet("font-size: 11px; padding: 2px 10px; min-height: 26px;")
        clear_btn.clicked.connect(self.clear)
        top_bar.addWidget(clear_btn)

        layout.addLayout(top_bar)

        # Metin alanı
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setProperty("class", "ModernConsole")
        layout.addWidget(self.text_edit)

    def append_log(self, text: str, level: str = "info"):
        now = datetime.now().strftime("%H:%M:%S")
        color_map = {
            "info": "#34d399",     # Zümrüt nane
            "warn": "#fbbf24",     # Kehribar
            "error": "#f87171",    # Mercan
            "system": "#60a5fa",   # Gök mavisi
            "dim": "#64748b",      # Muted slate
        }
        color = color_map.get(level, "#cbd5e1")
        formatted = f"<span style='color:#64748b;'>[{now}]</span> <span style='color:{color}; font-weight:500;'>{text}</span>"
        self.text_edit.append(formatted)

        cursor = self.text_edit.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.text_edit.setTextCursor(cursor)

    def clear(self):
        self.text_edit.clear()
