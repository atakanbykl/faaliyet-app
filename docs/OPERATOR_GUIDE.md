# FieldOps Assistant - Saha Operatörü Kullanım Kılavuzu (Operator Guide)

Bu kılavuz, saha personelinin sahaya çıkıştan görev bitimine kadar **FieldOps Assistant** uygulamasını adım adım nasıl kullanacağını açıklamaktadır.

---

## 🧭 Hızlı Başlangıç

### Windows Bilgisayarda (Destek Laptopu):
1. `FieldOps_Windows.bat` dosyasına çift tıklayın.
2. Eğer ilk defa yeni bir bilgisayarda çalıştırıyorsanız, önce `setup_env.bat` dosyasını çalıştırarak gerekli kütüphanelerin otomatik yüklenmesini sağlayabilirsiniz.

### Linux Makinesinde (Doğrudan Cihaz):
1. Terminalde proje kök dizininde:
   ```bash
   chmod +x FieldOps_Linux.sh setup_env.sh
   ./FieldOps_Linux.sh
   ```

---

## 🖥️ 1. Ana Ekran: Saha Operasyon Kontrol Merkezi (Launchpad)

Uygulama açıldığında sizi karşılayan kontrol paneli 3 ana bölümden oluşur:

### A. Sol Kart: 🚀 Yeni Faaliyet Başlat
- **Hedef Lokasyon Seçimi**: Açılır listeden gideceğiniz saha istasyonunu seçin (örn: `Ankara Gölbaşı Radar Sahası`).
- **Önizleme Rozetleri**: Seçilen lokasyonun hedef IP adresi, gerekli yazılım sürümü ve zorunlu malzeme sayısı rozetlerde anında görünür.
- **Profil Yönetimi (`+ Yeni` ve `✏️ Düzenle`)**:
  - `+ Yeni`: Yeni bir radar istasyonu veya saha profilini hiçbir dosyayı elle düzenlemeden görsel form üzerinden tanımlamanızı sağlar.
  - `✏️ Düzenle`: Seçili lokasyonun IP adresini, gerekli yazılım paketlerini, malzeme listesini ve referans konfigürasyonunu doğrudan arayüzden güncellemenizi sağlar.
- **Operatör Adı**: Sahada işlemi yürüten personelin adını girin.
- **Görevi Başlat ➔**: 1. Aşamaya geçiş yapar.

### B. Sağ Kart: 📂 Kayıtlı Faaliyetler
- Önceki oturumlar tarih, operatör ve durum rozetiyle listelenir.
- İstediğiniz oturumun üzerine tıklayıp `Devam Et ➔` butonuyla kalınan aşamadan göreve devam edebilirsiniz.
- `🗑️` butonu ile tamamlanmış veya iptal edilen oturumları silebilirsiniz.

### C. Alt Bölüm: 💾 Hafızadaki Yazılımlar (`softwares/`)
- **Açılır / Kapanır (Collapsible)**: Varsayılan olarak kompakt bir şerit halinde durur. Üzerine tıklayarak veya `[▶ Genişlet]` butonuna basarak açabilirsiniz.
- **Ağaç Hiyerarşisi**: Uygulamalar ve altlarındaki versiyonlar hiyerarşik ağaç biçiminde listelenir (`softwares/<uygulama>/<versiyon>`).
- **Boş Klasör Uyarısı (`⚠️ Paket Yok`)**: Eğer versiyon klasörü açılmış ancak içine `.tar.gz` veya `.zip` arşivi bırakılmamışsa, sarı uyarı rozetiyle operatör uyarılır.
- **Tek Tıkla Klasörü Aç (`📂 Klasörü Aç`)**: Butona basıldığında ilgili klasör işletim sistemi dosya gezgininde açılır; paketi anında içine sürükleyip bırakabilir ve `🔄 Yenile` butonuna basabilirsiniz.

---

## 📋 2. Aşama 1: Ön Kontroller & Hazırlık

Yola çıkmadan önce ofis veya araçta yapılan hazırlık aşamasıdır:
1. **Saha Ekipmanları Kontrol Listesi**:
   - Listelenen malzemeleri (örn: Konsol kablosu, Multimetre, LAN kablosu) fiziki olarak kontrol edip onay kutularını işaretleyin.
   - Tüm zorunlu malzemeler işaretlenmeden normal şartlarda devam edilemez.
2. **⚠️ Acil Durum Force Geçişi (`Zorunlu Ekipmanı Yoksay`)**:
   - Eğer zorunlu bir malzeme sahada alternatif yollarla çözüldüyse veya acil durumda devam edilmesi gerekiyorsa, sağ alttaki `⚠️ Zorunlu Ekipmanı Yoksay (Acil Geçiş)` butonunu kullanarak onay verip Aşama 2'ye geçebilirsiniz.
3. **Yazılım ve Konfigürasyon Hazırlığı**:
   - İlgili lokasyona ait paketlerin taşınabilir bellekte mevcut olduğu teyit edilir.

---

## 🔌 3. Aşama 2: Cihaz Bağlantısı & Enjeksiyon

Sahaya ulaşıldığında hedef cihaza bağlanma ve yazılım/konfigürasyon yükleme aşamasıdır:
1. **Otomatik Platform Algılama**:
   - Windows ortamındaysanız bağlantı modu otomatik olarak **Uzak Cihaz (SSH / Ağ)** seçilir.
   - Linux hedef makinesindeyseniz doğrudan **Bu Cihazda (Yerel)** modu seçilir.
   - Gerekirse elle seçim yapılabilir.
2. **Bağlantıyı Doğrula**:
   - `Bağlantıyı Test Et` butonuna basarak cihaza erişim ve yetki denetimi yapılır.
3. **Sürüm Kontrolü & Kurulum**:
   - Cihazdaki mevcut aktif sürüm sorgulanır.
   - İhtiyaç duyulursa yeni yazılım paketi cihaza yüklenir ve kurulur.
4. **Konfigürasyon Enjeksiyonu**:
   - Lokasyon profiline ait referans konfigürasyon dosyası cihaza aktarılır ve doğrulanır.

---

## 📦 4. Aşama 3: Kapanış, Log Toplama & Görsel Diff

Faaliyet tamamlandığında ofise dönmeden önceki son aşamadır:
1. **20-30 GB Yüksek Hacimli Log Toplama**:
   - Cihazdaki ağır operasyon logları, hedef makinede çok çekirdekli olarak (`tar` / `pigz`) sıkıştırılır.
   - Parçalı aktarımla destek bilgisayarına çekilir ve SHA-256 sağlama toplamı doğrulanır.
2. **Aktif Konfigürasyon Snapshot'ı**:
   - Cihazın sahada çalışan son güncel konfigürasyonu çekilir.
3. **Görsel Konfigürasyon Kıyaslama (Diff Engine)**:
   - Ofisteki referans konfigürasyon ile sahadaki son konfigürasyon yan yana renkli diff ekranında gösterilir (Eklenenler yeşil, Değişenler sarı, Silinenler kırmızı).
   - Sahada yapılan geçerli ayar değişiklikleri tek tıkla (`Referans Profili Güncelle`) ana konfigürasyona baseline olarak kaydedilebilir.
4. **USB Senkronizasyonu**:
   - Yerel diskte çalışılmışsa, toplanan tüm log ve raporlar tek tıkla USB belleğe aktarılır.

