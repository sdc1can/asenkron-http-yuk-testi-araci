# Asenkron HTTP Yük Testi Aracı

Bu Python betiği, web sunucularına veya API'lere yönelik basit ama etkili, asenkron bir HTTP yük testi aracıdır. `asyncio` ve `aiohttp` kütüphanelerini kullanarak yüksek eşzamanlılık seviyelerinde HTTP istekleri gönderebilir, performans metriklerini toplayabilir ve sonuçları özetleyebilir. Araç, kullanıcı dostu bir komut satırı arayüzü üzerinden interaktif olarak yapılandırılabilir.

**⚠️ UYARI:** Bu araç, testleri doğrudan **sizin genel IP adresiniz üzerinden** gerçekleştirir. Yüksek hacimli testler, hedef sunucuda veya kendi ağınızda performans sorunlarına, istenmeyen trafik olarak algılanmaya veya engellenmelere yol açabilir. **Sorumlu bir şekilde ve sadece izinli olduğunuz sistemlerde kullanın.** Tam anonimlik veya kaynak IP gizliliği için sistem düzeyinde VPN veya Tor gibi ek araçlar kullanmanız gerekebilir.

## ✨ Temel Özellikler

* **Asenkron İstekler:** `asyncio` ve `aiohttp` sayesinde binlerce isteği verimli bir şekilde eş zamanlı olarak gönderir.
* **Esnek Hedef Belirleme:** Tek bir URL'yi veya URL listesi içeren bir dosyayı hedef alabilir.
* **Kapsamlı Yapılandırma:**
    * HTTP Metodu (GET, POST, PUT, DELETE, vb.)
    * Eşzamanlılık Seviyesi (Worker/Kullanıcı Sayısı)
    * Test Süresi veya Toplam İstek Sayısı ile test bitişini belirleme.
    * Hedef RPS (Saniye Başına İstek) ile hız sınırlama (Rate Limiting).
    * İstek başına Zaman Aşımı (Timeout) süresi.
    * Özelleştirilebilir User-Agent başlığı (Gizlilik odaklı seçenekler dahil).
    * İsteğe özel HTTP başlıkları (Headers) ekleyebilme.
    * POST/PUT/PATCH gibi metodlar için istek gövdesi (Request Body) gönderebilme (JSON veya düz metin).
* **Detaylı İstatistikler:**
    * Toplam gönderilen, başarılı ve başarısız istek sayısı.
    * Gerçekleşen ortalama RPS (Requests Per Second).
    * Başarısızlık oranı (%).
    * Başarılı isteklerin yanıt süreleri (minimum, maksimum, ortalama, medyan).
    * Alınan HTTP durum kodlarının dağılımı.
    * Oluşan ağ/istemci hatalarının (örn. Timeout, Connection Error) dağılımı.
* **Anlık İlerleme Takibi:** Test çalışırken gönderilen istek sayısı, hata sayısı ve anlık RPS konsolda güncellenir.
* **Assertion Desteği:** Test sonunda belirli başarı kriterlerinin (örn. maksimum ortalama gecikme, maksimum hata oranı) otomatik kontrolü.
* **Gizlilik Odaklı Seçenekler:** User-Agent başlığını gizleme veya rastgele yaygın tarayıcı UA'ları kullanma imkanı.
* **Detaylı Loglama:** Konsola genel bilgileri (INFO) ve isteğe bağlı olarak bir dosyaya tüm detayları (DEBUG seviyesi) kaydeder.

## ⚙️ Gereksinimler

* **Python 3.7+** (Asyncio ve f-string özellikleri için önerilir)
* **aiohttp** kütüphanesi:
    ```bash
    pip install aiohttp
    ```

## 🚀 Kullanım

1.  Betiği bir `.py` dosyası olarak kaydedin (örn: `async_load_tester.py`).
2.  Terminal veya komut istemcisinden betiği çalıştırın:
    ```bash
    python async_load_tester.py
    ```
3.  Betik sizi interaktif olarak yönlendirerek aşağıdaki test parametrelerini soracaktır:

    * **Test Hedefi:**
        * `U`: Tek bir URL girmek için.
        * `F`: Her satırda bir URL bulunan bir dosyanın yolunu belirtmek için. Dosyadaki URL'ler `http://` veya `https://` ile başlamalıdır.
    * **HTTP Metodu:** Kullanılacak HTTP fiili (örn: `GET`, `POST`, `PUT`, `DELETE`). Varsayılan: `GET`.
    * **Eş Zamanlı İstek Sayısı:** Aynı anda çalışacak worker (sanal kullanıcı) sayısı. Varsayılan: `50`.
    * **Test Modu:**
        * `S`: Testin ne kadar süre (saniye cinsinden) çalışacağını belirtir. Varsayılan: 10 saniye.
        * `I`: Toplam kaç adet istek gönderileceğini belirtir. Varsayılan: 1000 istek.
    * **Hedeflenen RPS:** Saniye başına hedeflenen toplam istek sayısı. `0` girilirse hız limiti olmaz, mümkün olan en yüksek hızda çalışır. Varsayılan: `0.0`.
    * **Zaman Aşımı Süresi:** Her bir isteğin yanıt vermesi için beklenecek maksimum süre (saniye). Varsayılan: `10.0`.
    * **User-Agent Ayarları:** Sunucuya gönderilecek User-Agent başlığını seçin:
        * `1`: Yaygın tarayıcı UA'larından rastgele biri seçilir (Gizlilik için önerilir).
        * `2`: `aiohttp` kütüphanesinin varsayılan UA'sı kullanılır (Aracı belli edebilir).
        * `3`: User-Agent başlığı hiç gönderilmez.
        * `4`: Kendi özel User-Agent string'inizi girersiniz.
    * **Özel HTTP Başlıkları:** Eklemek isteyip istemediğiniz sorulur. Evet ise, `İsim: Değer` formatında (örn: `Authorization: Bearer token123`) başlıkları girin. Bitirmek için boş satır bırakın. (⚠️ Hassas bilgileri log dosyasında görünür kılabilir!)
    * **İstek Gövdesi:** Eğer `POST`, `PUT`, `PATCH` gibi bir metod seçtiyseniz, istek gövdesi eklemek isteyip istemediğiniz sorulur.
        * Evet ise, verinin JSON formatında olup olmadığı sorulur.
        * Ardından veriyi girmeniz istenir (Genellikle tek satır veya kopyala/yapıştır).
        * JSON seçilip geçerli JSON girilmezse, düz metin olarak gönderme seçeneği sunulur.
        * JSON veri gönderiliyorsa ve `Content-Type` başlığı özel olarak eklenmediyse, `Content-Type: application/json` otomatik olarak eklenir.
    * **Detaylı Loglama:** Tüm istek/yanıt detaylarını (DEBUG seviyesi) bir dosyaya kaydetmek isteyip istemediğiniz sorulur. Evet ise, log dosyası için bir isim belirleyebilirsiniz. Varsayılan: `http_load_test_YYYYMMDD_HHMMSS.log`.
    * **Assertion Ayarları:** Test sonunda otomatik kontrol edilecek başarı kriterleri tanımlamak isteyip istemediğiniz sorulur. Evet ise:
        * `latency`: Kabul edilebilir maksimum ortalama yanıt süresini (saniye) girin.
        * `failure`: Kabul edilebilir maksimum başarısızlık oranını (%) girin.

4.  Parametreler girildikten sonra test başlar ve ilerleme konsolda gösterilir.
5.  Test tamamlandığında (süre dolduğunda, hedeflenen istek sayısına ulaşıldığında veya Ctrl+C ile durdurulduğunda), detaylı bir özet raporu ve assertion sonuçları konsola yazdırılır.

## 📊 Çıktı Açıklaması

Test sonunda aşağıdaki bilgileri içeren bir özet raporu gösterilir:

* **Toplam Çalışma Süresi:** Testin ne kadar sürdüğü.
* **Toplam Gönderilen İstek:** Test boyunca gönderilen toplam istek sayısı.
* **Başarılı İstek (2xx, 3xx):** HTTP 2xx veya 3xx durum kodu ile dönen istek sayısı.
* **Başarısız İstek (Hata veya 4xx, 5xx):** Ağ hatası alan veya HTTP 4xx/5xx durum kodu ile dönen istek sayısı.
* **Başarısızlık Oranı:** Başarısız isteklerin toplam isteklere oranı (%).
* **Ortalama Saniye Başına İstek (RPS):** Test süresince ortalama olarak saniyede kaç istek yapıldığı. Varsa hedeflenen RPS de gösterilir.
* **Başarılı İsteklerin Yanıt Süreleri:** (Sadece başarılı istekler üzerinden hesaplanır)
    * Ortalama, Minimum, Maksimum, Medyan yanıt süreleri (saniye).
* **Durum Kodu Dağılımı:** Hangi HTTP durum kodundan kaçar tane alındığı (örn: `HTTP 200: 950 istek`, `HTTP 404: 50 istek`).
* **Hata Dağılımı:** Durum kodu alınamayan hataların türü ve sayısı (örn: `TimeoutError: 15 kez`, `ConnectionError: 5 kez`).
* **Assertion Kontrolü:** Tanımlanan her assertion için `GEÇTİ` veya `KALDI` durumu ve gerçekleşen değer.
* **Gizlilik ve Yapılandırma Notları:** Kullanılan URL kaynağı, User-Agent ayarı, IP adresi uyarısı, SSL/TLS uyarısı, DNS uyarısı ve log dosyasının konumu gibi bilgileri içerir.

## 📝 Loglama

* **Konsol (INFO):** Test başlangıcı, anlık ilerleme, uyarılar, hatalar ve test sonu özeti gibi temel bilgileri gösterir.
* **Dosya (DEBUG - İsteğe Bağlı):** Eğer etkinleştirildiyse, belirtilen dosyaya çok daha detaylı bilgi kaydedilir. Bu, her bir isteğin URL'si, metodu, gönderilen başlıklar (maskelenmiş hassas veri hariç), alınan durum kodu, yanıt süresi, oluşan hatalar ve betiğin iç işleyişine dair DEBUG mesajlarını içerir. Hata ayıklama için kullanışlıdır.

## 🔒 Gizlilik ve Güvenlik Hususları

* **IP Adresi:** İstekler sizin IP'nizden çıkar. Gizlilik için VPN/Tor kullanın.
* **User-Agent:** Varsayılan `aiohttp` UA'sı bu aracı tanıtabilir. Gizlilik için "Rastgele Genel Tarayıcı UA'sı" veya "Gönderme" seçeneklerini değerlendirin.
* **SSL/TLS Doğrulaması:** **DEVRE DIŞI BIRAKILMIŞTIR!** Bu, aradaki ağ trafiğini dinleyebilen bir saldırganın (Man-in-the-Middle) trafiği okumasına veya değiştirmesine olanak tanır. Sadece güvendiğiniz ağlarda ve test sistemlerinde kullanın. Gerçek dünya sistemlerine karşı test yaparken bu büyük bir risktir.
* **DNS Sorguları:** Sisteminizin varsayılan DNS çözümleyicisi kullanılır. Bu sorgular İnternet Servis Sağlayıcınız (ISP) veya DNS sağlayıcınız tarafından görülebilir.
* **Hassas Veri:** Özel başlıklara (`Authorization`, `Cookie`) veya istek gövdesine eklediğiniz hassas bilgiler (tokenlar, şifreler), özellikle DEBUG seviyesinde dosya loglaması etkinse, log dosyasına yazılabilir. Dikkatli olun!
* **Hedef Sunucu Etkisi:** Yüksek trafik göndermek hedef sunucuyu yavaşlatabilir veya hizmet dışı bırakabilir. Ağ kaynaklarınızı tüketebilir. **Sadece izinli olduğunuz ve sonuçlarını anladığınız sistemlerde kullanın.**
