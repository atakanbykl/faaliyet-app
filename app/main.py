"""
FieldOps Assistant - Uygulama Başlangıç Noktası (Main Entrypoint)
"""

from __future__ import annotations
import sys
from pathlib import Path

# Proje kök dizinini Python path'ine ekle
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from app.gui.main_window import MainWindow
from app.gui.styles import FIELD_DARK_THEME, get_dark_palette


def main():
    # Dokunmatik ekran ve yüksek DPI ekran desteği
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("FieldOps Assistant")
    app.setOrganizationName("FieldOps Team")

    # Windows yerel açık tema sızıntılarını önleyen Fusion motoru, koyu palet ve tema
    app.setStyle("Fusion")
    app.setPalette(get_dark_palette())
    app.setStyleSheet(FIELD_DARK_THEME)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

