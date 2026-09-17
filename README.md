# FieldOps Assistant - Saha Operasyon & Konfigürasyon Yöneticisi

FieldOps Assistant; saha görevlerinde kurum içi yazılım ve donanımların lokasyon bazlı konfigürasyonlarını yönetmek, saha personelini adım adım yönlendirmek, çift modlu (Windows SSH / Linux Doğrudan Yerel) güvenli bağlantı sağlamak, 20-30 GB operasyon loglarını yerinde sıkıştırarak toplamak ve ofiste görsel konfigürasyon kıyaslama (Diff Tool) ve tek tıkla baseline güncellemesi yapmak üzere geliştirilmiş taşınabilir bir masaüstü uygulamasıdır.

---

## 📚 Dokümantasyon & Detaylı Rehberler
- **[walkthrough.md](file:///walkthrough.md)**: Projenin mimari yapısı, geliştirilen tüm yetenekler, dizin standartları ve test sonuçları.
- **[docs/OPERATOR_GUIDE.md](file:///docs/OPERATOR_GUIDE.md)**: Sahada görev yapan personel için adım adım operasyon ve acil durum rehberi.

---

## 🚀 Öne Çıkan Yetenekler

1. **Taşınabilir & Çift Modlu Çalıştırma Motoru**:
   - **Windows Destek Bilgisayarı Modu**: Cihaza SSH ve SFTP üzerinden bağlanarak uzaktan komut yürütür, yazılım paketler ve log çeker.
   - **Linux Doğrudan Yerel Mod**: Uygulama doğrudan ana Linux makinesinde çalıştırıldığında sıfır ağ gecikmesiyle yerel terminal ve dosya sistemi üzerinden işlem yapar.
   - **Akıllı Platform Algılama**: Çalışılan işletim sistemini algılayarak Aşama 2 bağlantı modunu otomatik ön seçer.

2. **Yazılım & Versiyon Havuzu (`softwares/`)**:
   - `softwares/<uygulama>/<versiyon>/` klasör hiyerarşisi taranarak ana ve yardımcı araçlar listelenir.
   - **Boş Versiyon Uyarısı**: İçi boş olan sürüm klasörleri sarı `⚠️ Paket Yok` rozetiyle uyarılır.
   - **Açılır / Kapanır (Collapsible)**: Varsayılan olarak daraltılmış şık bir şerit halinde durur, tıklandığında genişler.
   - **Tek Tıkla Klasörü Aç**: Versiyon klasörleri doğrudan dosya gezgininde açılabilir.

3. **Görsel Lokasyon Profil Editörü (`+ Yeni` ve `✏️ Düzenle`)**:
   - YAML dosyalarına elle müdahaleye gerek kalmadan hedef saha profilleri (IP, port, cihaz bilgisi, yazılımlar, malzemeler ve referans konfigürasyon) görsel modal üzerinden yönetilir.

4. **Acil Durum Force Geçişi (`Zorunlu Ekipmanı Yoksay`)**:
   - Zorunlu işaretli saha malzemelerinin eksik olduğu acil saha koşullarında, operatörün onay vererek sürece devam etmesini sağlar.

5. **20-30 GB Yüksek Hacimli Log Yönetimi**:
   - Hedef cihazda çok çekirdekli (`tar` / `pigz`) sıkıştırma yaparak log boyutunu küçültür.
   - SHA-256 sağlama toplamı (checksum) ile veri bütünlüğünü garanti eder.

6. **Görsel Konfigürasyon Kıyaslama (Diff Engine)**:
   - Sahadan çekilen aktif konfigürasyon ile ofisteki referans konfigürasyonu yan yana görsel olarak karşılaştırır. Değişiklikler tek tıkla referans profile aktarılabilir.

---

## 📂 Dizin Yapısı

```
faaliyet-app/
├── FieldOps_Windows.bat        # Windows için tek tıkla başlatıcı
├── FieldOps_Linux.sh           # Linux x86_64 için başlatıcı
├── requirements.txt            # Python kütüphane bağımlılıkları
├── walkthrough.md              # Mimari, yetenekler ve doğrulama raporu
├── README.md                   # Bu dosya
├── docs/
│   └── OPERATOR_GUIDE.md       # Saha operatörü kullanım kılavuzu
├── app/
│   ├── main.py                 # Uygulama başlangıç noktası
│   ├── core/                   # Dinamik yollar, modeller, profiller, diff motoru
│   ├── adapters/               # Yerel (Linux) ve Uzak (SSH) adaptörleri
│   └── gui/                    # Modern PySide6 koyu tema arayüzü
├── data/
│   ├── profiles/               # Lokasyon YAML tanımları
│   └── missions/               # Sahada toplanan loglar ve görev özetleri
├── softwares/                  # Yazılım ve versiyon hiyerarşisi
└── tests/
    └── test_core.py            # Çekirdek test paketi
```

---

## 🛠 Yeni Bir Ortamda Kurulum ve Çalıştırma

### Bağımlılıkların Kurulumu:
```bash
pip install -r requirements.txt
```

### Windows Ortamında:
- `FieldOps_Windows.bat` dosyasına çift tıklayın (veya terminalden `python app/main.py`).

### Linux Ortamında:
- Terminalden:
   ```bash
   chmod +x FieldOps_Linux.sh
   ./FieldOps_Linux.sh
   ```

### Testleri Çalıştırma:
```bash
python tests/test_core.py
```
