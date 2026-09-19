"""
FieldOps Assistant - Saha Ekipmanları Kataloğu ve Havuz Yöneticisi
Saha görevlerinde kullanılan araç gereç ve ekipmanların kalıcı JSON havuzunda tutulmasını,
yeni profillere hızlı eklenmesini ve elle girilen yeni ekipmanların otomatik hafızaya kaydedilmesini sağlar.
Ekipmanların zorunluluk durumu (is_mandatory) havuzda saklanmaz; yalnızca faaliyet planlanırken profil bazında belirlenir.
"""

from __future__ import annotations
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional

from app.core.app_paths import AppPaths
from app.core.models import EquipmentItem


@dataclass
class EquipmentCatalogItem:
    """Kalıcı ekipman kütüphanesinde saklanan malzeme tanımı."""
    name: str
    description: str = ""
    category: str = "Genel"  # "Kablo & Bağlantı", "Güç & Enerji", "İş Güvenliği & KKD", "Donanım & Test", "Genel"


DEFAULT_EQUIPMENT_CATALOG: List[dict] = [
    {
        "name": "Yedek Ethernet CAT6 Kablosu (15m)",
        "description": "Mavi korumalı blendajlı CAT6 ağ kablosu",
        "category": "Kablo & Bağlantı"
    },
    {
        "name": "USB-RS232 Seri Port Dönüştürücü",
        "description": "FTDI yongalı endüstriyel seri konsol adaptörü",
        "category": "Kablo & Bağlantı"
    },
    {
        "name": "Saha Multimetresi ve Probları",
        "description": "True-RMS dijital multimetre ve yüksek gerilim probları",
        "category": "Donanım & Test"
    },
    {
        "name": "24V Saha Güç Adaptörü & Akü",
        "description": "Endüstriyel DIN ray veya masaüstü yedek DC güç kaynağı",
        "category": "Güç & Enerji"
    },
    {
        "name": "Yansıtıcı Saha Yeleği & Baret",
        "description": "EN ISO 20471 standartlarında yüksek görünürlüklü KKD",
        "category": "İş Güvenliği & KKD"
    },
    {
        "name": "Manyetik Araç Üstü GPS Anteni",
        "description": "Aktif SMA konnektörlü yüksek kazançlı GPS/GNSS anteni",
        "category": "Donanım & Test"
    },
    {
        "name": "12V Araç Çakmaklık Güç Kablosu",
        "description": "3 metre sigortalı araç içi güç besleme ara kablosu",
        "category": "Güç & Enerji"
    },
    {
        "name": "4G Yedek SIM Kart",
        "description": "Statik IP tanımlı operatör saha veri hattı",
        "category": "Kablo & Bağlantı"
    },
    {
        "name": "Hassas Tornavida & Alyan Takımı",
        "description": "Yalıtımlı gövde açma ve montaj alyan seti",
        "category": "Donanım & Test"
    },
    {
        "name": "RJ45 - DB9 Dişi Konsol Kablosu",
        "description": "Yönlendirici ve switch konsol erişim ara kablosu",
        "category": "Kablo & Bağlantı"
    },
    {
        "name": "Termal Macun & İletken Temizleme Kiti",
        "description": "İşlemci ve soğutucu blok bakım kiti",
        "category": "Donanım & Test"
    }
]


class EquipmentCatalogManager:
    """Ekipman kataloğu dosyasını yöneten sınıf."""

    def __init__(self, catalog_file: Optional[Path] = None):
        self.catalog_file = catalog_file or (AppPaths.get_data_dir() / "equipment_catalog.json")
        self._items: Dict[str, EquipmentCatalogItem] = {}
        self.load()

    def load(self):
        """Kataloğu JSON dosyasından yükler; dosya yoksa varsayılanları oluşturur."""
        self._items.clear()
        if self.catalog_file.exists():
            try:
                with open(self.catalog_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    for entry in data:
                        if isinstance(entry, dict) and entry.get("name"):
                            item = EquipmentCatalogItem(
                                name=entry["name"].strip(),
                                description=entry.get("description", "").strip(),
                                category=entry.get("category", "Genel").strip() or "Genel"
                            )
                            self._items[item.name.lower()] = item
                return
            except Exception as e:
                print(f"[EquipmentCatalogManager] Katalog okuma hatası: {e}, varsayılanlar yüklenecek.")

        # Dosya yoksa veya bozuksa varsayılan listeyi yükle ve kaydet
        for entry in DEFAULT_EQUIPMENT_CATALOG:
            item = EquipmentCatalogItem(
                name=entry["name"],
                description=entry["description"],
                category=entry["category"]
            )
            self._items[item.name.lower()] = item
        self.save()

    def save(self):
        """Kataloğu JSON dosyasına kalıcı olarak yazar."""
        try:
            self.catalog_file.parent.mkdir(parents=True, exist_ok=True)
            data = [asdict(item) for item in self._items.values()]
            # İsim alfabetik sıralı olsun
            data.sort(key=lambda x: x["name"].lower())
            with open(self.catalog_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[EquipmentCatalogManager] Katalog kaydetme hatası: {e}")

    def get_items(self, search_query: str = "", category: str = "") -> List[EquipmentCatalogItem]:
        """Arama ve kategori filtresine göre sıralı ekipman listesi döndürür."""
        q = search_query.strip().lower()
        cat = category.strip().lower()
        results: List[EquipmentCatalogItem] = []

        for item in self._items.values():
            if cat and cat != "tümü" and item.category.lower() != cat:
                continue
            if q:
                match_name = q in item.name.lower()
                match_desc = q in item.description.lower()
                match_cat = q in item.category.lower()
                if not (match_name or match_desc or match_cat):
                    continue
            results.append(item)

        results.sort(key=lambda x: (x.category, x.name.lower()))
        return results

    def get_categories(self) -> List[str]:
        """Mevcut tüm kategorilerin tekil listesini döndürür."""
        cats = {item.category for item in self._items.values() if item.category}
        sorted_cats = sorted(list(cats))
        return ["Tümü"] + sorted_cats

    def add_item(
        self,
        name: str,
        description: str = "",
        category: str = "Genel"
    ) -> bool:
        """Havuza yeni ekipman ekler veya var olanı günceller."""
        clean_name = name.strip()
        if not clean_name:
            return False

        key = clean_name.lower()
        item = EquipmentCatalogItem(
            name=clean_name,
            description=description.strip(),
            category=category.strip() or "Genel"
        )
        self._items[key] = item
        self.save()
        return True

    def remove_item(self, name: str) -> bool:
        """Belirtilen isimdeki ekipmanı havuzdan siler."""
        key = name.strip().lower()
        if key in self._items:
            del self._items[key]
            self.save()
            return True
        return False

    def register_items(self, items: List[EquipmentItem]):
        """Elle girilmiş veya profilde bulunan ekipmanları hafızaya ekler.
        Var olanların ismini ezmez, yeni olanları havuza kaydeder.
        Ekipmanın zorunluluk durumu (is_mandatory) havuza kaydedilmez.
        """
        changed = False
        for it in items:
            name = it.name.strip()
            if not name:
                continue
            key = name.lower()
            if key not in self._items:
                self._items[key] = EquipmentCatalogItem(
                    name=name,
                    description=it.description.strip(),
                    category="Genel"
                )
                changed = True
            else:
                # Açıklama güncellenmişse ve eskisi boşsa zenginleştir
                existing = self._items[key]
                if it.description.strip() and not existing.description:
                    existing.description = it.description.strip()
                    changed = True

        if changed:
            self.save()
