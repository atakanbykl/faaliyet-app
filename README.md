# FieldOps Assistant - Saha Operasyon & Konfigürasyon Yöneticisi

FieldOps Assistant; saha görevlerinde kurum içi yazılımın lokasyon bazlı konfigürasyonlarını yönetmek, saha personelini adım adım yönlendirmek ve faaliyet aşamalarındaki otomatik işleri (bağlantı, konfigürasyon yükleme, 20-30 GB log toplama, sağlık kontrolleri ve ofiste görsel konfigürasyon kıyaslama) yürütmek üzere geliştirilmiş taşınabilir bir masaüstü uygulamasıdır.

---

## 🚀 Öne Çıkan Yetenekler

1. **Bağımsız ve Taşınabilir (Portable)**:
   - Sabit sürücü harflerine veya yollara bağlı değildir.
   - Doğrudan USB bellek üzerinden (exFAT önerilir) çalıştırılabilir.
   - İstenirse USB'den Windows veya Linux bilgisayarın yerel diskine kopyalanıp çalıştırılabilir.
   - Yerel diskte çalışıldığında, faaliyet sonundaki toplanan log ve raporları takılı olan USB belleğe tek tıkla geri senkronize eder.

2. **Çift Modlu Çalıştırma Motoru (Local / SSH)**:
   - **Windows Destek Bilgisayarı Modu**: Cihaza SSH ve SFTP üzerinden bağlanarak uzaktan komut yürütür, yazılım paketler ve log çeker.
   - **Linux Doğrudan Yerel Mod**: Uygulama doğrudan ana Linux makinesinde çalıştırıldığında sıfır ağ gecikmesiyle yerel terminal ve dosya sistemi üzerinden işlem yapar.

3. **20-30 GB Yüksek Hacimli Log Yönetimi**:
   - Hedef cihazda çok çekirdekli (`tar` / `pigz`) sıkıştırma yaparak boyutu küçültür.
   - Parçalı ve akışlı aktarım (streaming transfer) ile kilitlenmeden aktarır.
   - SHA-256 sağlama toplamı (checksum) ile veri bütünlüğünü garanti eder.

4. **3 Aşamalı Operasyonel Akış (SOP)**:
   - **Aşama 1 (Yola Çıkış / Ön Hazırlık)**: Lokasyon seçimi, yedek yazılım paketlerinin otomatik taranması (bulunamazsa harici dosya seçici ile ekleme), konfigürasyon kontrolü ve ekipman kontrol listesi.
   - **Aşama 2 (Faaliyet Başlangıcı)**: Cihaz bağlantı doğrulaması, sahadaki kurulu yazılımın sürüm denetimi, operatör onaylı sürüm güncelleme/dağıtımı, operatör onaylı konfigürasyon enjeksiyonu.
   - **Aşama 3 (Faaliyet Sonu & Raporlama)**: Toplanma kontrolleri, 20-30 GB log paketleme, sahadaki aktif konfigürasyon snapshot'ı, USB senkronizasyonu ve **Yan Yana Görsel Kıyaslama (Diff Tool)** ile değişen ayarları ana referans profile tek tıkla aktarma.

5. **Tablet & Dokunmatik Ekran Ergonomisi**:
   - Minimum 48-52px dokunmatik hedefler.
   - Eldivenli ve dokunmatik saha kullanımına uygun yüksek kontrastlı tema.

---

## 📂 Dizin Yapısı

```
fieldops_assistant/
├── FieldOps_Windows.bat        # Windows için başlatıcı (çift tıkla açılır)
├── FieldOps_Linux.sh           # Linux x86_64 için başlatıcı
├── app/
│   ├── main.py                 # Başlangıç noktası
│   ├── core/                   # Dinamik yollar, modeller, profiller, diff motoru
│   │   ├── app_paths.py        # USB tespiti ve bağımsız dizin çözümleme
│   │   ├── models.py           # Lokasyon, yazılım ve görev modelleri
│   │   ├── profile_manager.py  # YAML lokasyon profilleri ve baseline güncelleyici
│   │   ├── asset_manager.py    # Yazılım paketleri otomatik/harici seçici
│   │   ├── diff_engine.py      # Görsel ve metinsel fark analizi
│   │   └── mission_context.py  # Görev oturumu ve kayıt defteri
│   ├── adapters/               # Yerel ve uzak çalıştırma motorları
│   │   ├── base_adapter.py     # Ortak arayüz
│   │   ├── local_adapter.py    # Linux yerel subprocess ve tar işlemleri
│   │   └── ssh_adapter.py      # Paramiko SSH/SFTP uzaktan yönetim
│   └── gui/                    # PySide6 arayüzü
│       ├── main_window.py      # Ana pencere ve 3 aşamalı sihirbaz
│       ├── styles.py           # Dokunmatik ve tablet uyumlu QSS teması
│       ├── widgets/            # Büyük butonlar, kontrol listesi, konsol, diff diyaloğu
│       └── wizards/            # 1, 2 ve 3. aşama ekranları
├── data/                       # Çalışma verileri (USB ile taşınan ortak alan)
│   ├── profiles/               # Lokasyon YAML tanımları
│   ├── packages/               # Lokasyonlara ait yedek yazılım binary/paketleri
│   └── missions/               # Sahada toplanan loglar ve görev özetleri
├── packaging/
│   ├── build_windows.py        # Windows tek tıkla PyInstaller derleme scripti
│   └── build_linux.sh          # Linux PyInstaller derleme scripti
└── tests/
    └── test_core.py            # Çekirdek modül testleri
```

---

## 🛠 Çalıştırma Talimatları

### Windows Ortamında:
- Çift tıklayarak: `FieldOps_Windows.bat`
- Veya terminalden:
  ```bash
  python app/main.py
  ```

### Linux Ortamında:
- Çift tıklayarak veya terminalden:
  ```bash
  chmod +x FieldOps_Linux.sh
  ./FieldOps_Linux.sh
  ```

---

## 📦 Kurulumsuz (.exe) Paketleme (Windows)

USB içerisine python kurulu olmayan bilgisayarlarda çalışması için tek tıkla paketlemek için:
```bash
python packaging/build_windows.py
```
Derleme sonucunda `bin/windows/fieldops.exe` oluşturulacak ve `FieldOps_Windows.bat` doğrudan bu binary'yi çalıştıracaktır.

