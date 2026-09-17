"""
FieldOps Assistant - Dokunmatik Uyumlu Büyük Buton Bileşeni
"""

from __future__ import annotations
from PySide6.QtCore import QSize
from PySide6.QtWidgets import QPushButton


class TouchButton(QPushButton):
    """Saha tabletleri ve eldivenli kullanımlar için optimize edilmiş buton."""

    def __init__(self, text: str = "", variant: str = "default", parent=None):
        super().__init__(text, parent)
        self.setMinimumHeight(48)
        self.set_variant(variant)

    def set_variant(self, variant: str) -> None:
        """Buton varyantını ayarlar: primary, success, danger, warning, secondary/default."""
        class_map = {
            "primary": "PrimaryButton",
            "success": "SuccessButton",
            "danger": "DangerButton",
            "warning": "WarningButton",
            "ghost": "GhostButton",
            "delete": "DeleteButton",
        }
        class_name = class_map.get(variant, "")
        self.setProperty("class", class_name)
        self.style().unpolish(self)
        self.style().polish(self)

