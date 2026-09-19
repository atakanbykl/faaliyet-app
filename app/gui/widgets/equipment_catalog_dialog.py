"""
FieldOps Assistant - Saha Ekipmanları Kataloğu ve Havuz Seçim Modalı (EquipmentCatalogDialog)
Hafızada saklanan ekipmanları listeler, aranıp seçilmesini sağlar,
havuza yeni ekipman tanımlanmasına ve havuzdan ekipman çıkarılmasına imkan tanır.
"""

from __future__ import annotations
import uuid
from typing import List, Optional, Set

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QCheckBox, QComboBox, QScrollArea, QFrame, QWidget,
    QMessageBox, QSizePolicy
)

from app.core.equipment_manager import EquipmentCatalogItem, EquipmentCatalogManager
from app.core.models import EquipmentItem
from app.gui.widgets.touch_button import TouchButton


class EquipmentCatalogDialog(QDialog):
    """Saha ekipman havuzunu görüntüleme, arama, seçme ve yönetme modalı."""

    def __init__(
        self,
        equipment_manager: EquipmentCatalogManager,
        existing_item_names: Optional[List[str]] = None,
        parent=None
    ):
        super().__init__(parent)
        self.equipment_manager = equipment_manager
        self.existing_names: Set[str] = {
            n.strip().lower() for n in (existing_item_names or []) if n.strip()
        }
        self.selected_items: List[EquipmentItem] = []
        self._checkbox_map = {}  # item_name_lower -> (QCheckBox, EquipmentCatalogItem)

        self.setWindowTitle("Saha Ekipmanları Havuzu & Hızlı Ekle")
        self.resize(780, 680)
        self.setMinimumSize(640, 500)
        self._setup_ui()
        self._refresh_list()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 18, 20, 18)
        main_layout.setSpacing(12)

        # 1. Başlık Banner
        header = QFrame()
        header.setProperty("class", "ModernCard")
        h_box = QHBoxLayout(header)
        h_box.setContentsMargins(16, 12, 16, 12)
        h_box.setSpacing(12)

        icon_lbl = QLabel("🎒")
        icon_lbl.setStyleSheet("font-size: 26px;")
        h_box.addWidget(icon_lbl)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title_lbl = QLabel("Saha Ekipmanları Havuzu & Hızlı Ekleme")
        title_lbl.setStyleSheet("font-size: 16px; font-weight: 700; color: #f8fafc;")
        title_col.addWidget(title_lbl)

        sub_lbl = QLabel(
            "Hafızadaki hazır saha ekipmanlarını seçip bu profile aktarabilir, "
            "havuza yeni malzeme tanımlayabilir veya istemediklerinizi silebilirsiniz."
        )
        sub_lbl.setStyleSheet("color: #94a3b8; font-size: 12px;")
        title_col.addWidget(sub_lbl)
        h_box.addLayout(title_col)
        h_box.addStretch()
        main_layout.addWidget(header)

        # 2. Kaydırılabilir Ana Gövde
        self.body_scroll = QScrollArea()
        self.body_scroll.setWidgetResizable(True)
        self.body_scroll.setFrameShape(QFrame.NoFrame)
        self.body_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.body_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_content)
        self.scroll_layout.setContentsMargins(0, 4, 8, 4)
        self.scroll_layout.setSpacing(12)

        # 3. Arama ve Filtreleme Kartı
        filter_card = QFrame()
        filter_card.setProperty("class", "ElevatedCard")
        filter_layout = QVBoxLayout(filter_card)
        filter_layout.setContentsMargins(14, 12, 14, 12)
        filter_layout.setSpacing(10)

        f_row = QHBoxLayout()
        f_row.setSpacing(10)

        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("🔍 Ekipman ara... (İsim, açıklama veya kategori)")
        self.txt_search.setStyleSheet("min-height: 36px; font-size: 13px;")
        self.txt_search.textChanged.connect(self._refresh_list)
        f_row.addWidget(self.txt_search, 2)

        self.combo_category = QComboBox()
        self.combo_category.setFixedHeight(36)
        self.combo_category.setStyleSheet("min-height: 36px; font-size: 12.5px; padding: 4px 10px;")
        self._update_category_combo()
        self.combo_category.currentIndexChanged.connect(self._refresh_list)
        f_row.addWidget(self.combo_category, 1)

        btn_select_all = TouchButton("Tümünü Seç", variant="ghost")
        btn_select_all.setFixedHeight(36)
        btn_select_all.setStyleSheet("min-height: 34px; padding: 2px 10px; font-size: 12px;")
        btn_select_all.clicked.connect(self._select_all_visible)
        f_row.addWidget(btn_select_all)

        btn_clear_sel = TouchButton("Temizle", variant="ghost")
        btn_clear_sel.setFixedHeight(36)
        btn_clear_sel.setStyleSheet("min-height: 34px; padding: 2px 10px; font-size: 12px;")
        btn_clear_sel.clicked.connect(self._clear_all_selection)
        f_row.addWidget(btn_clear_sel)

        filter_layout.addLayout(f_row)
        self.scroll_layout.addWidget(filter_card)

        # 4. Havuzdaki Malzemeler Listesi Konteyneri
        self.list_container = QFrame()
        self.list_container.setProperty("class", "ElevatedCard")
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(14, 12, 14, 12)
        self.list_layout.setSpacing(8)

        lbl_list_title = QLabel("📦 Hafızada Kayıtlı Ekipmanlar:")
        lbl_list_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #60a5fa;")
        self.list_layout.addWidget(lbl_list_title)

        self.items_box_layout = QVBoxLayout()
        self.items_box_layout.setSpacing(6)
        self.list_layout.addLayout(self.items_box_layout)

        self.scroll_layout.addWidget(self.list_container)

        # 5. Yeni Ekipman Tanımlama Kartı (Havuza Kalıcı Ekle)
        new_card = QFrame()
        new_card.setProperty("class", "ElevatedCard")
        new_card_layout = QVBoxLayout(new_card)
        new_card_layout.setContentsMargins(14, 12, 14, 12)
        new_card_layout.setSpacing(10)

        lbl_new_title = QLabel("➕ Havuza Yeni Ekipman Tanımla:")
        lbl_new_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #34d399;")
        new_card_layout.addWidget(lbl_new_title)

        form_row1 = QHBoxLayout()
        form_row1.setSpacing(10)

        self.txt_new_name = QLineEdit()
        self.txt_new_name.setPlaceholderText("Malzeme Adı (Örn: Konsol Kablosu RJ45-DB9)")
        self.txt_new_name.setStyleSheet("min-height: 34px;")
        form_row1.addWidget(self.txt_new_name, 2)

        self.txt_new_desc = QLineEdit()
        self.txt_new_desc.setPlaceholderText("Açıklama (Opsiyonel)")
        self.txt_new_desc.setStyleSheet("min-height: 34px;")
        form_row1.addWidget(self.txt_new_desc, 2)

        new_card_layout.addLayout(form_row1)

        form_row2 = QHBoxLayout()
        form_row2.setSpacing(10)

        lbl_cat = QLabel("Kategori:")
        lbl_cat.setStyleSheet("color: #94a3b8; font-size: 12px;")
        form_row2.addWidget(lbl_cat)

        self.combo_new_cat = QComboBox()
        self.combo_new_cat.setEditable(True)
        self.combo_new_cat.addItems([
            "Kablo & Bağlantı",
            "Güç & Enerji",
            "İş Güvenliği & KKD",
            "Donanım & Test",
            "Genel"
        ])
        self.combo_new_cat.setFixedHeight(34)
        self.combo_new_cat.setStyleSheet("min-height: 32px;")
        form_row2.addWidget(self.combo_new_cat, 1)

        btn_save_new = TouchButton("💾 Havuza Kaydet & Seç", variant="primary")
        btn_save_new.setFixedHeight(34)
        btn_save_new.setStyleSheet("min-height: 32px; padding: 2px 14px; font-weight: 700; font-size: 12px;")
        btn_save_new.clicked.connect(self._add_new_to_catalog)
        form_row2.addWidget(btn_save_new)

        new_card_layout.addLayout(form_row2)
        self.scroll_layout.addWidget(new_card)
        self.scroll_layout.addStretch(1)

        self.body_scroll.setWidget(scroll_content)
        main_layout.addWidget(self.body_scroll, 1)

        # 6. Alt Aksiyon Barı (Sabit)
        bottom_bar = QHBoxLayout()
        bottom_bar.setSpacing(12)

        self.lbl_selected_info = QLabel("0 malzeme seçildi")
        self.lbl_selected_info.setStyleSheet("color: #38bdf8; font-size: 12.5px; font-weight: 600;")
        bottom_bar.addWidget(self.lbl_selected_info)
        bottom_bar.addStretch()

        btn_cancel = TouchButton("Vazgeç", variant="ghost")
        btn_cancel.setFixedHeight(38)
        btn_cancel.setStyleSheet("min-height: 36px; padding: 2px 18px; font-size: 13px;")
        btn_cancel.clicked.connect(self.reject)
        bottom_bar.addWidget(btn_cancel)

        self.btn_apply = TouchButton("✓ Seçilenleri Profile Ekle", variant="primary")
        self.btn_apply.setFixedHeight(38)
        self.btn_apply.setStyleSheet("min-height: 36px; padding: 2px 22px; font-size: 13px; font-weight: 700;")
        self.btn_apply.clicked.connect(self._apply_selection)
        bottom_bar.addWidget(self.btn_apply)

        main_layout.addLayout(bottom_bar)

    def _update_category_combo(self):
        current = self.combo_category.currentText()
        self.combo_category.blockSignals(True)
        self.combo_category.clear()
        cats = self.equipment_manager.get_categories()
        self.combo_category.addItems(cats)
        idx = self.combo_category.findText(current)
        if idx >= 0:
            self.combo_category.setCurrentIndex(idx)
        else:
            self.combo_category.setCurrentIndex(0)
        self.combo_category.blockSignals(False)

    def _refresh_list(self):
        # Önceki seçimleri hatırla
        previously_selected = {
            k for k, (chk, _) in self._checkbox_map.items() if chk.isChecked()
        }

        # Mevcut widget'ları temizle
        while self.items_box_layout.count():
            w = self.items_box_layout.takeAt(0).widget()
            if w:
                w.deleteLater()
        self._checkbox_map.clear()

        query = self.txt_search.text().strip()
        cat = self.combo_category.currentText()
        items = self.equipment_manager.get_items(search_query=query, category=cat)

        if not items:
            empty_lbl = QLabel("Kriterlere uygun ekipman bulunamadı.")
            empty_lbl.setStyleSheet("color: #94a3b8; font-size: 12px; padding: 16px;")
            empty_lbl.setAlignment(Qt.AlignCenter)
            self.items_box_layout.addWidget(empty_lbl)
            self._update_selected_count()
            return

        for item in items:
            row_frame = QFrame()
            row_frame.setStyleSheet("""
                QFrame {
                    background-color: #0b1120;
                    border: 1px solid #1e293b;
                    border-radius: 8px;
                    padding: 2px 4px;
                }
                QFrame:hover {
                    border-color: #3b82f6;
                    background-color: #0d1527;
                }
            """)
            r_layout = QHBoxLayout(row_frame)
            r_layout.setContentsMargins(10, 8, 10, 8)
            r_layout.setSpacing(10)

            # Seçim kutusu
            chk = QCheckBox()
            key = item.name.lower()
            if key in previously_selected:
                chk.setChecked(True)
            chk.stateChanged.connect(self._update_selected_count)
            self._checkbox_map[key] = (chk, item)
            r_layout.addWidget(chk)

            # İsim ve Açıklama
            info_col = QVBoxLayout()
            info_col.setSpacing(2)

            name_row = QHBoxLayout()
            name_row.setSpacing(8)
            lbl_name = QLabel(f"<b>{item.name}</b>")
            lbl_name.setStyleSheet("font-size: 13px; color: #f8fafc;")
            name_row.addWidget(lbl_name)

            # Kategori Rozeti
            cat_badge = QLabel(item.category)
            cat_badge.setStyleSheet("""
                background-color: #1e293b;
                color: #94a3b8;
                border-radius: 4px;
                padding: 1px 6px;
                font-size: 11px;
            """)
            name_row.addWidget(cat_badge)

            # Zaten ekli mi rozeti
            if key in self.existing_names:
                exist_badge = QLabel("✓ Profilde Ekli")
                exist_badge.setStyleSheet("""
                    background-color: #064e3b;
                    color: #34d399;
                    border-radius: 4px;
                    padding: 1px 6px;
                    font-size: 11px;
                    font-weight: 600;
                """)
                name_row.addWidget(exist_badge)

            name_row.addStretch()
            info_col.addLayout(name_row)

            if item.description:
                lbl_desc = QLabel(item.description)
                lbl_desc.setStyleSheet("color: #94a3b8; font-size: 11.5px;")
                info_col.addWidget(lbl_desc)

            r_layout.addLayout(info_col, 1)

            # Hızlı Tekli Ekle Butonu
            btn_quick_add = TouchButton("➕ Ekle", variant="ghost")
            btn_quick_add.setFixedHeight(28)
            btn_quick_add.setStyleSheet("min-height: 26px; padding: 2px 10px; font-size: 11.5px;")
            btn_quick_add.setToolTip("Yalnızca bu malzemeyi anında profile ekle")
            btn_quick_add.clicked.connect(lambda _, it=item: self._add_single_item(it))
            r_layout.addWidget(btn_quick_add)

            # Havuzdan Kalıcı Sil Butonu
            btn_del_cat = TouchButton("🗑", variant="delete")
            btn_del_cat.setFixedSize(28, 28)
            btn_del_cat.setToolTip("Bu malzemeyi havuzdan kalıcı olarak sil")
            btn_del_cat.clicked.connect(lambda _, it=item: self._remove_from_catalog(it))
            r_layout.addWidget(btn_del_cat)

            self.items_box_layout.addWidget(row_frame)

        self._update_selected_count()

    def _select_all_visible(self):
        for chk, _ in self._checkbox_map.values():
            chk.setChecked(True)
        self._update_selected_count()

    def _clear_all_selection(self):
        for chk, _ in self._checkbox_map.values():
            chk.setChecked(False)
        self._update_selected_count()

    def _update_selected_count(self):
        count = sum(1 for chk, _ in self._checkbox_map.values() if chk.isChecked())
        self.lbl_selected_info.setText(f"{count} malzeme seçildi")
        self.btn_apply.setText(f"✓ Seçilenleri Profile Ekle ({count})")
        self.btn_apply.setEnabled(count > 0)

    def _add_single_item(self, item: EquipmentCatalogItem):
        """Tek bir malzemeyi anında seçip profile ekleyerek modalı onaylar."""
        self.selected_items = [
            EquipmentItem(
                id=f"eq_{uuid.uuid4().hex[:6]}",
                name=item.name,
                description=item.description,
                is_mandatory=True,
                is_checked=False
            )
        ]
        self.accept()

    def _add_new_to_catalog(self):
        """Kullanıcının formdan girdiği yeni ekipmanı havuza kaydeder."""
        name = self.txt_new_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Eksik Bilgi", "Lütfen malzeme adını giriniz.")
            self.txt_new_name.setFocus()
            return

        desc = self.txt_new_desc.text().strip()
        cat = self.combo_new_cat.currentText().strip() or "Genel"

        self.equipment_manager.add_item(
            name=name,
            description=desc,
            category=cat
        )

        # Formu temizle
        self.txt_new_name.clear()
        self.txt_new_desc.clear()

        # Kategorileri ve listeyi tazele
        self._update_category_combo()
        self._refresh_list()

        # Yeni eklenen malzemeyi otomatik seçili hale getir
        key = name.lower()
        if key in self._checkbox_map:
            chk, _ = self._checkbox_map[key]
            chk.setChecked(True)
            self._update_selected_count()

    def _remove_from_catalog(self, item: EquipmentCatalogItem):
        """Malzemeyi havuzdan siler."""
        res = QMessageBox.question(
            self,
            "Hafızadan Sil",
            f"'{item.name}' malzemesini kalıcı ekipman havuzundan silmek istediğinizden emin misiniz?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if res == QMessageBox.Yes:
            self.equipment_manager.remove_item(item.name)
            self._update_category_combo()
            self._refresh_list()

    def _apply_selection(self):
        """Seçili tüm ekipmanları toplayıp modalı kapatır."""
        self.selected_items = []
        for chk, item in self._checkbox_map.values():
            if chk.isChecked():
                self.selected_items.append(
                    EquipmentItem(
                        id=f"eq_{uuid.uuid4().hex[:6]}",
                        name=item.name,
                        description=item.description,
                        is_mandatory=True,
                        is_checked=False
                    )
                )
        self.accept()

    def get_selected_items(self) -> List[EquipmentItem]:
        """Eklenen ekipmanlar listesini döndürür."""
        return self.selected_items

