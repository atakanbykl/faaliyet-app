"""
FieldOps Assistant - Modern, Akıcı ve Reaktif UI Teması (Linear & Raycast Dark Aesthetic)
Obsidian derin zemin, cam efektli (glassmorphism) hap rozetler, gradyan butonlar ve kusursuz tipografi.
"""

from __future__ import annotations
from PySide6.QtGui import QPalette, QColor

FIELD_DARK_THEME = """
/* ===================================================
   GENEL PENCERE VE ARKA PLAN (OBSIDIAN DARK)
   =================================================== */
QMainWindow, QWidget#CentralWidget, QWidget#RootWidget {
    background-color: #080c14; /* Derin obsidian uzay grisi */
    color: #f1f5f9;
    font-family: 'Segoe UI Variable Display', 'Segoe UI', 'Inter', -apple-system, sans-serif;
    font-size: 14px;
}

QWidget {
    color: #e2e8f0;
    font-family: 'Segoe UI Variable Display', 'Segoe UI', 'Inter', -apple-system, sans-serif;
    outline: none;
}

/* ===================================================
   MODERN KARTLAR VE ELEVATED SURFACES
   =================================================== */
QFrame.ModernCard {
    background-color: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 14px;
    padding: 18px;
}
QFrame.ModernCard:hover {
    border-color: #334155;
}

QFrame.ElevatedCard {
    background-color: #131d33;
    border: 1px solid #233352;
    border-radius: 12px;
}

/* Bölüm Başlıkları */
QLabel.SectionTitle {
    font-size: 17px;
    font-weight: 700;
    color: #f8fafc;
    letter-spacing: -0.3px;
}

QLabel.SectionSubtitle {
    font-size: 13px;
    color: #94a3b8;
    line-height: 1.4;
}

/* ===================================================
   MODERN DÜĞMELER (GRADIENT & GHOST BUTTONS)
   =================================================== */
QPushButton {
    background-color: #1e293b;
    color: #f8fafc;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 10px 20px;
    min-height: 44px;
    font-size: 14px;
    font-weight: 600;
    text-align: center;
}
QPushButton:hover {
    background-color: #27354f;
    border-color: #475569;
    color: #ffffff;
}
QPushButton:pressed {
    background-color: #131d33;
    border-color: #3b82f6;
}
QPushButton:disabled,
QPushButton.PrimaryButton:disabled,
QPushButton.SuccessButton:disabled,
QPushButton.WarningButton:disabled,
QPushButton.DangerButton:disabled,
QPushButton.GhostButton:disabled,
QPushButton.DeleteButton:disabled {
    background: #0f172a;
    background-color: #0f172a;
    color: #475569;
    border: 1px solid #1e293b;
}

QPushButton:disabled:hover,
QPushButton.PrimaryButton:disabled:hover,
QPushButton.SuccessButton:disabled:hover,
QPushButton.WarningButton:disabled:hover,
QPushButton.DangerButton:disabled:hover,
QPushButton.GhostButton:disabled:hover,
QPushButton.DeleteButton:disabled:hover {
    background: #0f172a;
    background-color: #0f172a;
    color: #475569;
    border: 1px solid #1e293b;
}

/* Birincil Aksiyon Butonu (Mavi - İndigo Modern Gradyan) */
QPushButton.PrimaryButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563eb, stop:1 #4f46e5);
    border: 1px solid #3b82f6;
    color: #ffffff;
    font-weight: 700;
}
QPushButton.PrimaryButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3b82f6, stop:1 #6366f1);
    border-color: #60a5fa;
}
QPushButton.PrimaryButton:pressed {
    background: #1d4ed8;
}

/* Başarı Butonu (Zümrüt Gradyan) */
QPushButton.SuccessButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #0d9488);
    border: 1px solid #10b981;
    color: #ffffff;
    font-weight: 700;
}
QPushButton.SuccessButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:1 #14b8a6);
    border-color: #34d399;
}
QPushButton.SuccessButton:pressed {
    background: #047857;
}

/* Uyarı Butonu (Kehribar) */
QPushButton.WarningButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #d97706, stop:1 #ea580c);
    border: 1px solid #f59e0b;
    color: #ffffff;
    font-weight: 700;
}
QPushButton.WarningButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #f59e0b, stop:1 #f97316);
    border-color: #fbbf24;
}

/* Tehlike Butonu (Kırmızı) */
QPushButton.DangerButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #dc2626, stop:1 #e11d48);
    border: 1px solid #ef4444;
    color: #ffffff;
    font-weight: 700;
}
QPushButton.DangerButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ef4444, stop:1 #f43f5e);
    border-color: #f87171;
}

/* Hayalet Buton (Ghost / Secondary) */
QPushButton.GhostButton {
    background-color: transparent;
    border: 1px solid #334155;
    color: #94a3b8;
}
QPushButton.GhostButton:hover {
    background-color: #1e293b;
    color: #f8fafc;
    border-color: #475569;
}

/* Silme / Çöp Kutusu Butonu (Kırmızı Vurgulu & Logolu Modern Buton) */
QPushButton.DeleteButton {
    background-color: transparent;
    border: 1px solid #334155;
    border-radius: 8px;
    color: #94a3b8;
    font-size: 15px;
    padding: 0px;
    min-height: 32px;
    max-height: 36px;
    min-width: 32px;
    max-width: 36px;
    text-align: center;
}
QPushButton.DeleteButton:hover {
    background-color: rgba(239, 68, 68, 0.15);
    border-color: #ef4444;
    color: #f87171;
}
QPushButton.DeleteButton:pressed {
    background-color: rgba(220, 38, 38, 0.3);
    border-color: #dc2626;
    color: #ffffff;
}

/* ===================================================
   FORM ELEMANLARI (INPUT & COMBOBOX)
   =================================================== */
QLineEdit, QComboBox {
    background-color: #0b1120;
    color: #f8fafc;
    border: 1px solid #1e293b;
    border-radius: 10px;
    padding: 10px 14px;
    min-height: 44px;
    font-size: 14px;
}
QLineEdit:hover, QComboBox:hover {
    border-color: #334155;
}
QLineEdit:focus, QComboBox:focus {
    border: 1px solid #3b82f6;
    background-color: #0d1527;
}

QComboBox::drop-down {
    border: none;
    width: 34px;
}
QComboBox QAbstractItemView {
    background-color: #0f172a;
    color: #f8fafc;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 6px;
}

/* ===================================================
   SEKMELER (QTabWidget & QTabBar)
   =================================================== */
QTabWidget::pane {
    border: 1px solid #1e293b;
    border-radius: 12px;
    background-color: #0f172a;
    padding: 14px;
    top: -1px;
}
QTabBar::tab {
    background-color: #0b1120;
    color: #94a3b8;
    border: 1px solid #1e293b;
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 10px 18px;
    margin-right: 4px;
    font-weight: 600;
    font-size: 13px;
}
QTabBar::tab:selected {
    background-color: #0f172a;
    color: #60a5fa;
    border-color: #334155;
    border-top: 2px solid #3b82f6;
}
QTabBar::tab:hover:!selected {
    background-color: #131d33;
    color: #f1f5f9;
}

/* ===================================================
   METİN ALANLARI VE SAYI KUTULARI
   =================================================== */
QPlainTextEdit, QTextEdit {
    background-color: #0b1120;
    color: #f8fafc;
    border: 1px solid #1e293b;
    border-radius: 10px;
    padding: 10px 14px;
    font-size: 13px;
}
QPlainTextEdit:focus, QTextEdit:focus {
    border: 1px solid #3b82f6;
    background-color: #0d1527;
}

QSpinBox {
    background-color: #0b1120;
    color: #f8fafc;
    border: 1px solid #1e293b;
    border-radius: 10px;
    padding: 6px 12px;
    min-height: 40px;
    font-size: 14px;
}
QSpinBox:focus {
    border: 1px solid #3b82f6;
}

/* ===================================================
   ONAY KUTULARI (QCheckBox)
   =================================================== */
QCheckBox {
    color: #e2e8f0;
    font-size: 13px;
    spacing: 8px;
}
QCheckBox::indicator {
    width: 20px;
    height: 20px;
    border: 1px solid #334155;
    border-radius: 5px;
    background-color: #0b1120;
}
QCheckBox::indicator:hover {
    border-color: #3b82f6;
}
QCheckBox::indicator:checked {
    background-color: #2563eb;
    border-color: #3b82f6;
}

/* ===================================================
   RADYO BUTONLARI (QRadioButton)
   =================================================== */
QRadioButton {
    color: #e2e8f0;
    font-size: 13px;
    font-weight: 500;
    spacing: 8px;
}
QRadioButton::indicator {
    width: 18px;
    height: 18px;
    border: 1px solid #334155;
    border-radius: 9px;
    background-color: #0b1120;
}
QRadioButton::indicator:hover {
    border-color: #3b82f6;
}
QRadioButton::indicator:checked {
    background-color: #2563eb;
    border-color: #60a5fa;
}

/* ===================================================
   MODERN HAP ROZETLER (PILL BADGES)
   =================================================== */
QLabel.PillBadge {
    border-radius: 12px;
    padding: 4px 12px;
    font-size: 12px;
    font-weight: 700;
}
QLabel.PillSuccess {
    background-color: rgba(16, 185, 129, 0.14);
    color: #34d399;
    border: 1px solid rgba(16, 185, 129, 0.3);
}
QLabel.PillWarning {
    background-color: rgba(245, 158, 11, 0.14);
    color: #fbbf24;
    border: 1px solid rgba(245, 158, 11, 0.3);
}
QLabel.PillDanger {
    background-color: rgba(239, 68, 68, 0.14);
    color: #f87171;
    border: 1px solid rgba(239, 68, 68, 0.3);
}
QLabel.PillInfo {
    background-color: rgba(59, 130, 246, 0.14);
    color: #60a5fa;
    border: 1px solid rgba(59, 130, 246, 0.3);
}
QLabel.PillMuted {
    background-color: rgba(148, 163, 184, 0.12);
    color: #94a3b8;
    border: 1px solid rgba(148, 163, 184, 0.25);
}

/* ===================================================
   İLERLEME ÇUBUĞU (PROGRESS BAR)
   =================================================== */
QProgressBar {
    background-color: #0b1120;
    border: 1px solid #1e293b;
    border-radius: 8px;
    height: 24px;
    text-align: center;
    color: #ffffff;
    font-weight: 700;
    font-size: 12px;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:1 #059669);
    border-radius: 7px;
}

/* ===================================================
   CANLI KONSOL (MAC / TERMINAL TARZI)
   =================================================== */
QTextEdit.ModernConsole {
    background-color: #06090f;
    color: #cbd5e1;
    font-family: 'Cascadia Code', 'Consolas', monospace;
    font-size: 13px;
    border: 1px solid #1e293b;
    border-radius: 10px;
    padding: 14px;
    line-height: 1.6;
}

/* ===================================================
   KUSURSUZ MODERN KOYU SCROLL ALANLARI VE SCROLLBAR
   =================================================== */
QScrollArea, QAbstractScrollArea {
    border: none;
    background-color: transparent;
    background: transparent;
}

QScrollArea > QWidget > QWidget {
    background-color: transparent;
    background: transparent;
}

QScrollArea > QWidget#qt_scrollarea_viewport,
QAbstractScrollArea > QWidget#qt_scrollarea_viewport {
    background-color: transparent;
    background: transparent;
}

QAbstractScrollArea::corner, QScrollBar::corner {
    background-color: transparent;
    border: none;
}

/* DİKEY SCROLLBAR (Modern Obsidian / Slate İnce & Tutarlı Çubuk) */
QScrollBar:vertical {
    background-color: rgba(11, 17, 32, 0.6);
    width: 8px;
    margin: 0px 0px 0px 0px;
    border: none;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background-color: #334155;
    min-height: 28px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background-color: #60a5fa;
}

QScrollBar::handle:vertical:pressed {
    background-color: #2563eb;
}

QScrollBar::add-line:vertical {
    border: none;
    background: none;
    height: 0px;
    subcontrol-position: bottom;
    subcontrol-origin: margin;
}

QScrollBar::sub-line:vertical {
    border: none;
    background: none;
    height: 0px;
    subcontrol-position: top;
    subcontrol-origin: margin;
}

QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
    border: none;
    background: none;
    width: 0px;
    height: 0px;
}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
    border: none;
}

/* YATAY SCROLLBAR */
QScrollBar:horizontal {
    background-color: rgba(11, 17, 32, 0.6);
    height: 8px;
    margin: 0px 0px 0px 0px;
    border: none;
    border-radius: 4px;
}

QScrollBar::handle:horizontal {
    background-color: #334155;
    min-width: 28px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #60a5fa;
}

QScrollBar::handle:horizontal:pressed {
    background-color: #2563eb;
}

QScrollBar::add-line:horizontal {
    border: none;
    background: none;
    width: 0px;
    subcontrol-position: right;
    subcontrol-origin: margin;
}

QScrollBar::sub-line:horizontal {
    border: none;
    background: none;
    width: 0px;
    subcontrol-position: left;
    subcontrol-origin: margin;
}

QScrollBar::left-arrow:horizontal, QScrollBar::right-arrow:horizontal {
    border: none;
    background: none;
    width: 0px;
    height: 0px;
}

QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: none;
    border: none;
}
"""


def get_dark_palette() -> QPalette:
    """Windows ve diğer sistemlerde yerel açık tema sızıntılarını önleyen küresel koyu palet."""
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#080c14"))
    palette.setColor(QPalette.WindowText, QColor("#f1f5f9"))
    palette.setColor(QPalette.Base, QColor("#0b1120"))
    palette.setColor(QPalette.AlternateBase, QColor("#0f172a"))
    palette.setColor(QPalette.ToolTipBase, QColor("#0f172a"))
    palette.setColor(QPalette.ToolTipText, QColor("#f8fafc"))
    palette.setColor(QPalette.Text, QColor("#f8fafc"))
    palette.setColor(QPalette.Button, QColor("#1e293b"))
    palette.setColor(QPalette.ButtonText, QColor("#f8fafc"))
    palette.setColor(QPalette.BrightText, QColor("#ef4444"))
    palette.setColor(QPalette.Link, QColor("#3b82f6"))
    palette.setColor(QPalette.Highlight, QColor("#2563eb"))
    palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    return palette
