"""
FieldOps Assistant - Görsel Konfigürasyon Kıyaslayıcı ve Birleştirici (Diff Dialog)
Sade, gözü yormayan renklerle referans ve sahadaki konfigürasyonu kıyaslar.
"""

from __future__ import annotations
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QFrame
)

from app.core.diff_engine import ConfigDiffEngine, DiffLine
from app.gui.widgets.touch_button import TouchButton


class ConfigDiffDialog(QDialog):
    """Görsel yan yana konfigürasyon kıyaslama penceresi."""
    merged_to_baseline = Signal(str)

    def __init__(
        self,
        profile_name: str,
        baseline_text: str,
        field_text: str,
        parent=None
    ):
        super().__init__(parent)
        self.profile_name = profile_name
        self.baseline_text = baseline_text
        self.field_text = field_text

        self.setWindowTitle(f"Konfigürasyon Kıyaslama - {profile_name}")
        self.resize(1100, 680)

        self._setup_ui()
        self._populate_diff()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(14)

        # Bilgi kartı
        info_frame = QFrame()
        info_frame.setProperty("class", "CardFrame")
        info_layout = QVBoxLayout(info_frame)
        info_layout.setSpacing(6)

        self.summary_lbl = QLabel(f"Lokasyon: {self.profile_name}  |  Kıyaslama Raporu")
        self.summary_lbl.setStyleSheet("font-size: 16px; font-weight: 700; color: #f8fafc;")
        info_layout.addWidget(self.summary_lbl)

        diff_desc = QLabel(
            "Sol taraf: Ofis veri tabanındaki referans konfigürasyon. "
            "Sağ taraf: Sahadaki aktif sistemden çekilen güncel değerler."
        )
        diff_desc.setStyleSheet("color: #94a3b8; font-size: 13px;")
        info_layout.addWidget(diff_desc)
        main_layout.addWidget(info_frame)

        # Kıyaslama Tablosu (Side-by-Side)
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "No (Ofis)", "Referans Konfigürasyon", "No (Saha)", "Sahadaki Güncel Değer"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #0f172a;
                gridline-color: #334155;
                font-family: 'Consolas', monospace;
                font-size: 13px;
                border: 1px solid #334155;
                border-radius: 8px;
            }
            QHeaderView::section {
                background-color: #1e293b;
                color: #e2e8f0;
                padding: 6px;
                border: 1px solid #334155;
                font-weight: 600;
            }
        """)
        main_layout.addWidget(self.table)

        # Alt İşlem Butonları
        bottom_bar = QHBoxLayout()

        self.merge_btn = TouchButton("✓ Sahadaki Değişiklikleri Ana Profile Aktar", variant="success")
        self.merge_btn.clicked.connect(self._on_merge_clicked)
        bottom_bar.addWidget(self.merge_btn)

        close_btn = TouchButton("Kapat (Değişiklik Yapma)", variant="secondary")
        close_btn.clicked.connect(self.reject)
        bottom_bar.addWidget(close_btn)

        main_layout.addLayout(bottom_bar)

    def _populate_diff(self):
        diff_lines, has_diff = ConfigDiffEngine.compare_configs(self.baseline_text, self.field_text)
        self.table.setRowCount(len(diff_lines))

        changes_count = sum(1 for d in diff_lines if d.change_type != "equal")

        if not has_diff:
            self.summary_lbl.setText(
                f"Lokasyon: {self.profile_name} — <span style='color:#34d399;'>✓ Fark bulunamadı, konfigürasyonlar aynı.</span>"
            )
            self.merge_btn.setEnabled(False)
        else:
            self.summary_lbl.setText(
                f"Lokasyon: {self.profile_name} — <span style='color:#fbbf24;'>⚠ {changes_count} satırda değişiklik tespit edildi.</span>"
            )

        for row, item in enumerate(diff_lines):
            item_left_no = QTableWidgetItem(str(item.line_num_left) if item.line_num_left else "")
            item_left_no.setTextAlignment(Qt.AlignCenter)
            item_left_txt = QTableWidgetItem(item.left_content)

            item_right_no = QTableWidgetItem(str(item.line_num_right) if item.line_num_right else "")
            item_right_no.setTextAlignment(Qt.AlignCenter)
            item_right_txt = QTableWidgetItem(item.right_content)

            # Gözü yormayan sakin diff renkleri
            if item.change_type == "replace":
                bg = "#451a03"  # Sakin amber
                fg = "#fde68a"
            elif item.change_type == "insert":
                bg = "#064e3b"  # Sakin zümrüt
                fg = "#a7f3d0"
            elif item.change_type == "delete":
                bg = "#450a0a"  # Sakin gül kurusu
                fg = "#fecaca"
            else:
                bg = "#0f172a"  # Nötr zemin
                fg = "#cbd5e1"

            row_color = QColor(bg)
            text_color = QColor(fg)

            for cell in (item_left_no, item_left_txt, item_right_no, item_right_txt):
                cell.setBackground(row_color)
                cell.setForeground(text_color)

            self.table.setItem(row, 0, item_left_no)
            self.table.setItem(row, 1, item_left_txt)
            self.table.setItem(row, 2, item_right_no)
            self.table.setItem(row, 3, item_right_txt)

    def _on_merge_clicked(self):
        reply = QMessageBox.question(
            self,
            "Ana Profili Güncelle",
            f"Sahadan çekilen bu güncel konfigürasyon, '{self.profile_name}' profilinin yeni ana referansı olarak kaydedilecek.\n\nOnaylıyor musunuz?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.merged_to_baseline.emit(self.field_text)
            QMessageBox.information(
                self,
                "Başarılı",
                "Ana profil güncellendi! Yeni saha görevlerinde bu konfigürasyon referans alınacaktır."
            )
            self.accept()
