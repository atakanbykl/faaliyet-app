# FieldOps Assistant - Proje Tamamlama, Mimari ve Operasyon Rehberi (Walkthrough)

FieldOps Assistant; saha görevlerinde kurum içi yazılım ve donanımların lokasyon bazlı konfigürasyonlarını yönetmek, saha personelini adım adım yönlendirmek, çift modlu (Windows SSH / Linux Yerel) güvenli bağlantı sağlamak, 20-30 GB logları yerinde sıkıştırıp toplamak ve ofis ortamında görsel konfigürasyon kıyaslama (Diff Tool) ve baseline güncellemesi yapmak üzere geliştirilmiş taşınabilir bir masaüstü uygulamasıdır.

---

## 🎯 Gerçekleştirilen Başlıca Yetenekler ve Mimari

### 1. Ergonomik Ana Ekran (Launchpad) & Dikey Kaydırma Düzeni (`welcome_stage.py`)
- **İçerik Yüksekliğine Sabitlenmiş Kontrol Merkezi Başlığı (`WelcomeHeader`)**:
  - Başlığın pencere boyutuna (`window size`) göre dikeyde gereksiz yere aşağı yukarı esnemesi engellendi.
  - Yükseklik tam olarak içerisindeki metin ve rozetin doğal boyutuna (`64px`) `setSizePolicy(Expanding, Fixed)` ve `setFixedHeight(header.sizeHint().height())` ile sabitlendi.
  - Sayfa düzeninin en altına `addStretch(1)` eklenerek pencere büyütüldüğünde veya kart daraltıldığında oluşan tüm fazlalık alan en alta itilir; başlık ve üst kartlar sayfanın en tepesinde (`y=10`) sabit kalır.
- **Tekil Dikey Kaydırma Alanı (`QScrollArea`)**:
  - Üstteki sabit başlık barı (*FieldOps Assistant / Lokasyon / OS Rozeti / Stepper*) dışında kalan ana karşılama ekranının tamamı tek bir `page_scroll_area` içine alındı.
  - **Sıfır Yatay Kayma**: Yatay kaydırma çubuğu kesin olarak kapatıldı (`ScrollBarAlwaysOff`); arayüz yalnızca yukarı ve aşağı pürüzsüzce kayar.
- **Genişletilmiş Üst Kartlar (345px Yükseklik - %50 / %50 Yan Yana)**:
  - **Sol Kart**: 🚀 *Yeni Faaliyet Başlat* (Hedef lokasyon seçimi, `+ Yeni` / `✏️ Düzenle`, operatör girişi ve 38px yüksekliğinde belirgin `Görevi Başlat ➔` butonu).
  - **Sağ Kart**: 📂 *Kayıtlı Faaliyetler* (Önceki oturum kartları, devam etme ve logolu silme butonları; 3 görevi kaydırma çubuğu olmadan tam boy gösterebilen 345px alan).
- **Kusursuz Koyu Scrollbar & Kaydırma Alanları (`Fusion` & `get_dark_palette`)**:
  - Windows'un yerel açık renkli (beyaz/açık gri) kaydırma çubukları ve viewport arka planları tamamen ortadan kaldırıldı.
  - Uygulama çapında `Fusion` masaüstü motoru ve obsidian palet (`#080c14`, `#0b1120`, `#334155`) devreye alındı.
  - İnce (8px), modern yuvarlatılmış hap formunda (`border-radius: 4px`), hover durumunda mavi (`#60a5fa`), sürüklendiğinde birincil mavi (`#2563eb`) ile vurgulanan tutarlı ve zarif koyu scrollbar entegrasyonu tamamlandı.

---

### 2. Uygulama ve Versiyon Ağacı (`softwares/<uygulama>/<versiyon>/`)
- **Klasör Formatı**:
  - `softwares/` altındaki 1. seviye klasör o uygulamanın adı (`app_name`).
  - 2. seviye klasörler ise o uygulamaya ait versiyonlardır (`v2.4.0`, `v1.0.0` vb.).
- **Ağaç Hiyerarşisi**:
  - Her bir yazılım (örn: `📁 radar_control`, `📁 yardimci_araclar`), bağımsız geniş bir uygulama kartı olarak sergilenir.
  - Uygulama başlığında yazılım adı, disk yolu (`softwares/<uygulama>/`), sürüm sayı rozeti ve doğrudan o uygulamanın klasörünü açma butonu yer alır.
  - Uygulamanın altında, sol kılavuz çizgisi (`├── `, `└── `) ile girintilendirilmiş versiyon satırları sergilenir.
- **Boş Versiyon Klasörlerinin Belirgin Uyarısı (`⚠️ İçi Boş` / `⚠️ Paket Yok`)**:
  - Versiyon klasörü oluşturulmuş ancak içine henüz bir `.tar.gz` veya `.zip` arşivi bırakılmamışsa:
    - Kesikli sarı/amber kenarlık ve uyarı arka planı.
    - **`⚠️`** uyarı ikonu ve **`⚠️ Paket Yok`** sarı durum rozeti.
    - Açıklamasında *"⚠️ İçi Boş — Bu versiyon klasöründe kurulabilir paket dosyası bulunmuyor"* uyarısı.
- **Hazır Versiyonların Gösterimi (`✓ Hazır`)**:
  - İçinde kuruluma hazır paket bulunan versiyonlar: paket dosya adı (`radar_control_v2.4.0_x86_64.tar.gz`), formatlı dosya boyutu (`4.4 KB`), son değiştirilme tarihi, dosya yolu ve yeşil **`✓ Hazır`** rozetiyle tek bir satırda ferahça listelenir.
- **Tek Tıkla Versiyon Klasörünü Açma Butonu (`📂 Klasörü Aç`)**:
  - Tam genişlik sayesinde her bir versiyon satırının sağında belirgin bir `📂 Klasörü Aç` butonu yer alır. Tıklandığında doğrudan ilgili versiyon klasörü açılır; operatör paketi anında içine sürükleyip bırakabilir.
  - Kartın üst başlığındaki `📂 Klasörü Aç` butonu ise ana `softwares/` kök dizinini açar.
  - Klasöre dosya atıldıktan sonra `🔄 Yenile` tıklandığında arayüz anında güncellenir.

---

### 3. Akıllı İşletim Sistemi Algılama ve Otomatik Mod Seçimi
- **Platform Algılama Rozeti**:
  - Uygulama çalıştığı işletim sistemini (`Windows`, `Linux`, `Darwin`) otomatik algılar.
  - Sağ üst köşede şık bir rozet ile belirtir:
    - Windows'ta: `💻 Windows Host (Uzak SSH Destek Bilgisayarı)`
    - Linux'ta: `🐧 Linux Host (Doğrudan Yerel Sistem)`
- **Aşama 2 Ön Seçimi**:
  - Aşama 2'ye geçildiğinde bağlantı modu çalışılan platforma göre önden seçili gelir:
    - Windows ortamındaysa: **Uzak Cihaz (SSH / Ağ)** modu otomatik seçilir.
    - Linux ortamındaysa: **Doğrudan Bu Cihazda (Yerel)** modu otomatik seçilir.
  - İstendiğinde radyo butonları üzerinden elle serbestçe değiştirilebilir.

---

### 4. Saha Ekipmanları Acil Durum Force Geçişi & Sadeleştirilmiş Aşama 1 Düzeni
- **Aşama 1 Ekipman Kontrolleri**:
  - Lokasyon profilinde zorunlu (`required: true`) işaretli saha ekipmanları eksik olduğunda standart olarak "Aşama 2'ye Geç" butonu kilitlidir.
  - Saha personeli acil durumlarda veya ekipmanı alternatif yollarla sağladığında mağdur olmamak adına **`⚠️ Zorunlu Ekipmanı Yoksay (Acil Geçiş)`** butonunu kullanabilir.
- **Yalın ve Dengeli İki Sütunlu Görünüm**:
  - Lokasyon profili ve operatör adı zaten ana karşılama ekranında (Launchpad) seçildiği ve üst barda sürekli gösterildiği için, Aşama 1'deki mükerrer `loc_card` paneli kaldırılarak alan israfı ve dikey sıkışma tamamen ortadan kaldırıldı.
  - Aşama 1 artık %50 - %50 dengeli iki ferah kolondan oluşur:
    - **Sol Kolon**: Hedefe aktarılacak konfigürasyon şablonu ve gerekli yazılım paketlerinin otomatik taranıp listelendiği `pkg_card`.
    - **Sağ Kolon**: İnteraktif saha ekipman ve malzeme kontrol listesi (`equip_card`).
  - Seçili lokasyon, operatör ve hedef cihaz bilgisi Aşama 1'in üst başlık alanında dinamik bir alt satır olarak zarif bir biçimde sunulur.

---

### 5. Görsel Lokasyon Profil Editörü (`ProfileEditorDialog`) & Yazılım Ekleme Modalı (`AddSoftwareDialog`)
- **Yeni Lokasyon Tanımlama (`+ Yeni`)**: Kullanıcı hiçbir YAML dosyasına elle dokunmadan ana ekrandaki `+ Yeni` butonuyla sıfırdan yeni bir hedef saha profili oluşturabilir.
- **Var Olan Lokasyonu Düzenleme (`✏️ Düzenle`)**: Seçili lokasyonun tüm parametrelerini görsel modal üzerinden güncelleyebilir.
- **Hafızadaki Yazılımları Listeleme & Otomatik Doldurma (`AddSoftwareDialog`)**:
  - Profil düzenleme ekranının "Yazılım Paketleri" sekmesinde `+ Yeni Paket Ekle...` butonuna tıklandığında açılan pencerede Welcome Page'de (`softwares/` dizini) tespit edilen tüm uygulamalar ve versiyonlar dosya boyutu ve hazır olma durumuyla listelenir.
  - Taranan listeden veya açılır kutudan bir yazılım seçildiğinde; Paket Adı, Sürüm, Arşiv Dosya Adı, Hedef Kurulum Yolu (`/opt/<app>`), Systemd Servis Adı ve Versiyon Komutu otomatik doldurulur.
  - **Kesintisiz Manuel Düzenleme & Elle Giriş**: `✏️ Formu Temizle (Manuel Giriş)` butonuyla veya doğrudan formdaki alanlar üzerinden dileyen operatör tamamen elle özel bir paket yazabilir. Otomatik doldurulan her alan istendiğinde elle serbestçe değiştirilebilir.
  - Düzenleme sekmesinde ayrıca doğrudan boş kart açmak için `✏️ Hızlı Boş Kart` ve her kart üzerinde `📦 Hafızadan Doldur...` butonu yer alır.
  - **Ergonomik Dikey Kaydırma Düzeni (`QScrollArea`)**: Farklı ekran çözünürlüklerinde form alanlarının ve paket listesinin birbirine girmesini engellemek için tüm pencere gövdesi akıcı bir dikey kaydırma alanı (`body_scroll`) içine alınmıştır. Alt aksiyon butonları (`Vazgeç` / `✓ Paketi Ekle`) pencerenin tabanına sabitlenmiş olup her an erişilebilirdir.
- **Kalıcı Saha Ekipmanları Havuzu & Hızlı Ekleme (`EquipmentCatalogManager` & `EquipmentCatalogDialog`)**:
  - **Kalıcı Ekipman Havuzu (`data/equipment_catalog.json`)**: Saha operasyonlarında kullanılan kablolar, adaptörler, ölçüm cihazları ve KKD ekipmanları kategorili ve kalıcı bir JSON havuzunda saklanır. Havuzda yalnızca malzeme adı, açıklama ve kategori tutulur; malzemenin zorunlu olup olmadığı havuzda tutulmaz.
  - **Hızlı ve Çoklu Seçim Modalı (`EquipmentCatalogDialog`)**: "🎒 Saha Ekipmanları" sekmesindeki `📦 Hafızadan Malzeme Ekle...` butonu ile açılan pencerede arama, kategori filtresi, tekli (`➕ Ekle`) ve toplu (`✓ Seçilenleri Profile Ekle`) malzeme aktarımı yapılabilir. Bu ekranda zorunluluk rozetleri veya seçimleri gösterilmez.
  - **Havuza Ekleme ve Çıkarma**: Operatör havuz modalından yeni malzeme tanımlayıp kalıcı olarak kaydedebilir (`💾 Havuza Kaydet & Seç`) veya listedeki `🗑` butonuyla havuzdan silebilir.
  - **Faaliyet Bazında Elle Zorunluluk Seçimi**: Ekipmanın zorunlu (`is_mandatory`) olup olmadığı yalnızca faaliyet profili planlanırken "Saha Ekipmanları" listesindeki onay kutusundan elle belirlenir; havuz veritabanına zorunluluk kaydedilmez.
  - **Manuel Girişlerin Otomatik Hafızaya Alınması**: Profil kaydedildiğinde, kullanıcının `✏️ Boş Satır Ekle` ile elle girdiği veya değiştirdiği yeni malzemelerin isim ve açıklamaları otomatik olarak `EquipmentCatalogManager` tarafından havuz veritabanına tescil edilir ve gelecekteki tüm profillerde anında seçilebilir hale gelir.
- **4 Sekmeli Zengin Arayüz**: Genel & Cihaz Ayarları, Yazılım Paketleri, Saha Ekipmanları ve Referans Konfigürasyon editörü.

---

### 6. Çift Modlu Çalıştırma Adaptörü (`BaseExecutionAdapter`)
- **Windows Destek Bilgisayarı Modu (`SSHExecutionAdapter`)**: Paramiko ile uzaktaki Linux cihaza bağlanır, SFTP ile dosya aktarır ve uzaktan kabuk komutları yürütür.
- **Linux Doğrudan Yerel Mod (`LocalExecutionAdapter`)**: Uygulama doğrudan hedef Linux makinesinde çalıştırıldığında `subprocess` ve yerel dosya I/O ile en yüksek hızda çalışır.

---

### 7. 3 Aşamalı Saha İş Akışı (SOP)
- **Aşama 1 (Ön Kontroller & Hazırlık)**: Malzeme kontrol listesi, zorunlu malzemeler için acil durum force geçiş opsiyonu, yazılım ve konfigürasyon hazır olma denetimi.
- **Aşama 2 (Bağlantı & Enjeksiyon)**: İşletim sistemine göre otomatik mod seçimi (Windows -> Uzak SSH, Linux -> Doğrudan Yerel), sürüm denetimi ve kurulum.
- **Aşama 3 (Kapanış & Log Toplama)**: 20-30 GB logların yerinde sıkıştırılarak çekilmesi, görsel konfigürasyon kıyaslama (Diff Engine) ve tek tıkla baseline güncelleme.

---

## 📁 Dizin ve Dosya Yapısı

```
faaliyet-app/
├── FieldOps_Windows.bat        # Windows için tek tıkla başlatıcı
├── FieldOps_Linux.sh           # Linux x86_64 için başlatıcı
├── requirements.txt            # Python kütüphane bağımlılıkları
├── walkthrough.md              # Bu dosya (tüm mimari ve operasyon rehberi)
├── README.md                   # Proje tanıtım ve genel özet dokümanı
├── docs/                       # Detaylı operasyon ve kullanıcı kılavuzları
│   └── OPERATOR_GUIDE.md       # Saha operatörü adım adım kullanım rehberi
├── app/
│   ├── main.py                 # Uygulama başlangıç noktası
│   ├── core/                   # Dinamik yollar, modeller, profiller, diff motoru
│   │   ├── app_paths.py        # USB tespiti ve bağımsız dizin çözümleme
│   │   ├── models.py           # Lokasyon, yazılım ve görev modelleri
│   │   ├── profile_manager.py  # YAML lokasyon profilleri ve baseline güncelleyici
│   │   ├── asset_manager.py    # softwares/ ağaç tarayıcı ve paket kontrolü
│   │   ├── diff_engine.py      # Görsel ve metinsel fark analizi
│   │   └── mission_context.py  # Görev oturumu ve kayıt defteri
│   ├── adapters/               # Yerel ve uzak çalıştırma motorları
│   │   ├── base_adapter.py     # Ortak adaptör arayüzü
│   │   ├── local_adapter.py    # Linux yerel subprocess ve tar işlemleri
│   │   └── ssh_adapter.py      # Paramiko SSH/SFTP uzaktan yönetim
│   └── gui/                    # PySide6 modern koyu tema arayüzü
│       ├── main_window.py      # Ana pencere ve üst bar
│       ├── styles.py           # Modern obsidian koyu tema (QSS)
│       ├── widgets/            # Büyük butonlar, kontrol listesi, kartlar
│       └── wizards/            # 1, 2 ve 3. aşama ve karşılama ekranı
│           ├── welcome_stage.py   # Launchpad (Yeni görev, kayıtlılar, yazılım havuzu)
│           ├── stage1_prep.py     # Ön kontroller & malzeme listesi
│           ├── stage2_deploy.py   # Bağlantı & paket/konfigürasyon enjeksiyonu
│           └── stage3_closure.py  # Log toplama & Diff motoru
├── data/
│   ├── profiles/               # Lokasyon YAML tanımları
│   └── missions/               # Sahada toplanan loglar ve görev özetleri
├── softwares/                  # Yazılım ve versiyon hiyerarşisi
│   ├── .gitkeep
│   ├── radar_control/          # Örnek uygulama
│   │   ├── v2.4.0/             # radar_control_v2.4.0_x86_64.tar.gz
│   │   └── v2.5.0/             # .gitkeep (Boş klasör uyarısı gösterimi için)
│   └── yardimci_araclar/       # Örnek yardımcı araçlar
│       ├── v1.0.0/             # saha_diagnostik_v1.0.0.tar.gz
│       └── v1.1.0/             # .gitkeep
└── tests/
    └── test_core.py            # Çekirdek modül testleri (6 test paketi)
```

---

## 🛠 Yeni Bir Ortamda Çalıştırma Kılavuzu

### 1. Sıfırdan Yeni Bir Windows Bilgisayarda:
1. Projeyi bir klasöre kopyalayın veya klonlayın.
2. Gerekli bağımlılıkları yükleyin: `pip install -r requirements.txt`
3. Uygulamayı başlatmak için `FieldOps_Windows.bat` dosyasına çift tıklayın (veya `python app\main.py`).

### 2. Sıfırdan Yeni Bir Linux Makinesinde:
1. Proje dizinine geçin ve bağımlılıkları yükleyin:
   ```bash
   pip install -r requirements.txt
   chmod +x FieldOps_Linux.sh
   ./FieldOps_Linux.sh
   ```

### 3. Taşınabilir USB Bellek Üzerinden Çalıştırma:
- Uygulama `AppPaths` mekanizması sayesinde diskteki sürücü harfine bağımlı değildir (`C:`, `D:`, `E:` veya `/media/usb`).
- Doğrudan USB bellek içerisinden başlatılabilir. Sahada toplanan görev logları `data/missions/` altında yerel diskte tutulsa dahi, görev tamamlandığında USB belleğe tek tıkla senkronize edilebilir.

---

## 🧪 Doğrulama ve Test Sonuçları

Tüm birim testleri ve GUI etkileşim doğrulamaları eksiksiz çalıştırılmıştır:
```
[OK] test_app_paths passed
[OK] test_profile_manager passed
[OK] test_software_asset_manager passed (Gruplandırılmış tarama ve boş klasör uyarı tespiti teyit edildi)
[OK] test_config_diff_engine passed
[OK] test_local_adapter_compression passed
[OK] test_mission_manager_saved_sessions passed
[OK] test_equipment_catalog_manager passed (Katalog yükleme, arama, ekleme, silme ve otomatik tescil)
All core tests passed successfully!

MainWindow loaded successfully.
Header sizeHint: 724 x 64 (İçerik yüksekliğine göre sabit ve net okunabilir)
Header height across window sizes (1024x768 -> 1920x1200): Sabit 64px (Dikey esneme engellendi)
Page Scroll Area present: True (Dikey Kaydırma Aktif)
Horizontal Scroll Policy: True (Yatay Kaydırma Kesinlikle Kapalı)
App groups rendered: 2 (radar_control, yardimci_araclar)
Collapsible Widget Verification: PASSED (Default daraltılmış, tıklayarak açılma ve buton izolasyonu doğrulandı)
EquipmentCatalogDialog Verification: PASSED (11 hazır ekipman, filtreleme, çoklu seçim ve havuza ekleme/çıkarma)
Auto-registration of manually typed equipment: PASSED (Profil kaydedildiğinde elle girilen malzeme havuza işlendi)
```

