# Asenkron HTTP Yük Testi Aracı

Bu araç, belirtilen hedef URL'e eş zamanlı olarak HTTP istekleri göndererek web uygulamalarınızın veya API'lerinizin performansını ve dayanıklılığını test etmenize olanak tanır. Kullanıcı dostu bir arayüze sahiptir ve çeşitli yapılandırma seçenekleri sunar.

## İçindekiler

1.  [Özellikler](#özellikler)
2.  [Gereksinimler](#gereksinimler)
3.  [Kurulum](#kurulum)
4.  [Kullanım](#kullanım)
5.  [Yapılandırma Seçenekleri](#yapılandırma-seçenekleri)
    * [Hedef URL(ler)](#hedef-urller)
    * [HTTP Metodu](#http-metodu)
    * [Performans Ayarları](#performans-ayarları)
    * [Gizlilik Ayarları](#gizlilik-ayarları)
    * [SSL/TLS Ayarları](#ssltls-ayarları)
    * [Özel Başlıklar](#özel-başlıklar)
    * [İstek Gövdesi](#istek-gövdesi)
    * [Loglama](#loglama)
    * [Assertion'lar (Test Sonu Kontrolleri)](#assertionlar-test-sonu-kontrolleri)
6.  [Gizlilik Odaklı İyileştirmeler](#gizlilik-odaklı-iyileştirmeler)
7.  [Önemli Notlar ve Uyarılar](#önemli-notlar-ve-uyarılar)
8.  [Assertion'lar (Test Sonu Kontrolleri) Hakkında Detaylı Bilgi](#assertionlar-test-sonu-kontrolleri-hakkında-detaylı-bilgi)
9.  [Loglama Hakkında Detaylı Bilgi](#loglama-hakkında-detaylı-bilgi)
10. [Katkıda Bulunma](#katkıda-bulunma)
11. [Lisans](#lisans)
12. [Yazar](#yazar)

## Özellikler

* **Asenkron Çalışma:** `asyncio` ve `aiohttp` kütüphaneleri sayesinde yüksek eş zamanlılıkta verimli testler gerçekleştirir.
* **Çeşitli HTTP Metotları:** GET, POST, PUT, DELETE, HEAD, OPTIONS ve PATCH metotlarını destekler.
* **Hedef URL Seçenekleri:** Tek bir URL veya bir dosyadan okunan URL listesi ile test yapabilme.
* **Performans Kontrolü:** Eş zamanlı worker sayısı, test süresi veya toplam istek sayısı belirleyebilme.
* **Rate Limiting:** İsteğe bağlı olarak saniye başına gönderilecek istek sayısını (RPS) sınırlayabilme.
* **Özelleştirilebilir İstekler:** Özel HTTP başlıkları ve istek gövdesi (JSON veya düz metin) gönderebilme.
* **Gizlilik Seçenekleri:** Farklı User-Agent başlıkları seçebilme veya hiç göndermeme seçeneği.
* **SSL/TLS Kontrolü:** SSL/TLS sertifika doğrulamasını etkinleştirme veya devre dışı bırakma seçeneği (dikkatli kullanılmalıdır).
* **Zaman Aşımı Ayarı:** Her bir istek için özel zaman aşımı süresi belirleyebilme.
* **Detaylı Loglama:** İsteğe bağlı olarak tüm istek detaylarını bir dosyaya kaydedebilme (DEBUG seviyesi).
* **Gerçek Zamanlı İlerleme:** Test sırasında gönderilen istek sayısı, hatalı istek sayısı ve anlık RPS gibi bilgileri konsolda görüntüleme.
* **Test Sonu Assertion'ları:** Ortalama yanıt süresi ve başarısızlık oranı gibi metrikler için otomatik kontrol kriterleri (assertion) tanımlayabilme.
* **Kapsamlı Raporlama:** Test sonunda özet istatistikleri (toplam süre, gönderilen istek, başarılı/başarısız sayıları, RPS, yanıt süreleri, durum kodu dağılımı, hatalar vb.) ve assertion sonuçlarını konsolda detaylı olarak görüntüleme.

## Gereksinimler

* Python 3.7 veya üzeri
* `aiohttp` kütüphanesi (genellikle script ilk çalıştırıldığında otomatik olarak indirilir)
* `asyncio` kütüphanesi (Python'un standart kütüphanesinin bir parçasıdır)
* `time`, `logging`, `statistics`, `sys`, `json`, `collections`, `datetime`, `typing`, `random`, `os`, `ssl` kütüphaneleri (Python'un standart kütüphanesinin bir parçasıdır)

## Kurulum

Bu script tek bir Python dosyasıdır. Herhangi bir özel kurulum gerektirmez. Scripti doğrudan çalıştırabilirsiniz.

## Kullanım

1.  Scripti bir terminal veya komut istemcisinde bulunduğu dizine gidin.
2.  Aşağıdaki komutu kullanarak scripti çalıştırın:

    ```bash
    python your_script_name.py
    ```

    (Burada `your_script_name.py` scriptin dosya adıdır).
3.  Script çalışmaya başladığında, size test parametrelerini sormak için bir dizi interaktif soru sunacaktır. İsteklerinize göre değerleri girin veya varsayılan değerleri kabul etmek için Enter tuşuna basın.
4.  Test tamamlandığında, sonuçlar ve özet istatistikler konsolda görüntülenecektir. İsteğe bağlı olarak bir log dosyası da oluşturulmuş olabilir.

## Yapılandırma Seçenekleri

Script, testinizi özelleştirmenize olanak tanıyan çeşitli yapılandırma seçenekleri sunar. İşte her bir seçeneğin açıklaması:

### Hedef URL(ler)

* **Test hedefi:** Testin tek bir URL'ye mi yoksa bir URL listesi içeren bir dosyaya mı yapılacağını seçmenizi ister.
    * **Tek URL ('U'):** Test etmek istediğiniz tek bir URL'yi girmenizi ister (örn: `https://example.com`). URL'nin `http://` veya `https://` ile başlaması gerektiğini unutmayın.
    * **URL listesi dosyası ('F'):** URL'lerin her satırda bir tane olacak şekilde listelendiği bir dosyanın tam yolunu girmenizi ister. Dosyanın okunabilir olduğundan emin olun. Sadece `http://` veya `https://` ile başlayan satırlar dikkate alınır.

### HTTP Metodu

* **HTTP Metodu (GET, POST, PUT, DELETE vb.):** Hedef URL'ye gönderilecek HTTP metodunu belirtmenizi ister. Varsayılan değer `GET`'tir. Diğer yaygın metotlar `POST`, `PUT`, `DELETE`, `HEAD`, `OPTIONS`, `PATCH`'tir.

### Performans Ayarları

* **Eş zamanlı istek sayısı (worker/kullanıcı sayısı):** Aynı anda kaç tane eş zamanlı HTTP isteği gönderileceğini belirler. Bu değer, sunucunuz üzerindeki yükü doğrudan etkiler. Varsayılan değer 50'dir.
* **Test modu:** Testin ne kadar süreyle çalışacağını (`S`üre) veya kaç tane toplam istek gönderileceğini (`I`stek sayısı) seçmenizi ister.
    * **Test süresi (saniye):** Testin kaç saniye boyunca çalışacağını belirtir. Varsayılan değer 10 saniyedir.
    * **Toplam gönderilecek istek sayısı:** Test boyunca toplamda kaç tane HTTP isteği gönderileceğini belirtir. Varsayılan değer 1000'dir.
* **Hedeflenen saniye başına istek (RPS) (0 = limitsiz):** Testin toplamda saniyede kaç istek göndermesini istediğinizi belirtir. `0` girerseniz, istekler mümkün olduğunca hızlı gönderilir (rate limiting devre dışı kalır). Pozitif bir değer girerseniz, araç belirtilen RPS'yi korumaya çalışacaktır.
* **Her bir istek için zaman aşımı süresi (saniye):** Her bir HTTP isteğinin yanıt alması için beklenecek maksimum süreyi saniye cinsinden belirtir. Bu süre aşılırsa, istek zaman aşımına uğramış olarak kabul edilir. Varsayılan değer 10.0 saniyedir.

### Gizlilik Ayarları

* **User-Agent Ayarları:** Hedef sunucuya gönderilecek User-Agent başlığını yapılandırmanızı sağlar. Bu başlık, tarayıcınızı veya bu test aracını sunucuya tanıtabilir. Gizliliği artırmak için genel bir tarayıcı UA'sı seçebilir veya hiç göndermeyebilirsiniz.
    * **Rastgele Genel Tarayıcı UA'sı (Önerilen):** Yaygın tarayıcı User-Agent stringlerinden rastgele birini seçerek gönderir. Bu, aracın kimliğini gizlemeye yardımcı olabilir.
    * **aiohttp Varsayılanı:** `aiohttp` kütüphanesinin varsayılan User-Agent başlığını (örn: `aiohttp/3.8.1`) kullanır. Bu, aracın kimliğini sunucuya açıkça belirtir.
    * **User-Agent Başlığını Gönderme:** Hiçbir User-Agent başlığı göndermez.
    * **Özel User-Agent Gir:** İstediğiniz özel bir User-Agent stringini girmenizi sağlar.

### SSL/TLS Ayarları

* **SSL sertifika doğrulamasını etkinleştirmek ister misiniz?** HTTPS bağlantıları için sunucunun SSL/TLS sertifikasının doğrulanıp doğrulanmayacağını seçmenizi ister.
    * **Evet (E):** SSL sertifikaları doğrulanır. Bu, güvenli bağlantılar için önerilen ayardır.
    * **Hayır (H):** SSL sertifikaları doğrulanmaz. Bu, güvenlik riski oluşturur ve yalnızca test ortamlarında, kendi kendine imzalanmış veya geçersiz sertifikalara sahip sunuculara karşı test yaparken kullanılmalıdır.

### Özel Başlıklar

* **Özel HTTP Başlıkları:** İsteğe ek özel başlıklar eklemenizi sağlar (örn: `Authorization: Bearer token`). Başlıkları `İsim: Değer` formatında girin. Birden fazla başlık eklemek için her birini ayrı ayrı girin ve bitirmek için boş bir satır bırakın.

### İstek Gövdesi

* **İstek Gövdesi:** `POST`, `PUT`, `PATCH` gibi metotlar için isteğe bir gövde (veri) eklemenizi sağlar.
    * **Veri JSON formatında mı?:** Gönderilecek verinin JSON formatında olup olmadığını belirtmenizi ister.
    * **Veri:** Gönderilecek veriyi girmenizi ister. JSON seçtiyseniz, geçerli bir JSON stringi girmeniz gerekir. Aksi takdirde, veri düz metin olarak gönderilir.

### Loglama

* **Tüm istek detaylarını (DEBUG seviyesi) bir dosyaya kaydetmek ister misiniz?:** Test sırasında gönderilen tüm isteklerin detaylı loglarını (DEBUG seviyesi) bir dosyaya kaydedip kaydetmeyeceğinizi seçmenizi ister.
    * **Log dosyasının adı:** Eğer loglama isterseniz, logların kaydedileceği dosyanın adını girmenizi ister. Varsayılan olarak `http_load_test_YYYYMMDD_HHMMSS.log` şeklinde bir dosya adı önerilir.

### Assertion'lar (Test Sonu Kontrolleri)

* **Test sonunda otomatik kontrol edilecek başarı kriterleri (assertion) tanımlamak ister misiniz?:** Test tamamlandıktan sonra otomatik olarak kontrol edilecek başarı kriterleri (assertion) tanımlayıp tanımlamayacağınızı seçmenizi ister.
    * **Assertion tipi girin ('latency', 'failure') veya bitirmek için boş bırakın:** Aşağıdaki assertion tiplerini seçebilirsiniz:
        * **latency:** Maksimum kabul edilebilir ortalama yanıt süresini (saniye) girmenizi ister.
        * **failure:** Maksimum kabul edilebilir başarısızlık oranını (yüzde) girmenizi ister.

## Gizlilik Odaklı İyileştirmeler

Bu araç, gizliliğinizi korumaya yardımcı olmak için aşağıdaki özellikleri içerir:

* **Rastgele User-Agent Seçimi:** Yaygın tarayıcı User-Agent başlıklarından rastgele birini kullanarak sunucuların aracın kimliğini belirlemesini zorlaştırabilirsiniz.
* **User-Agent Göndermeme Seçeneği:** İsteğe bağlı olarak hiçbir User-Agent başlığı göndermeyerek daha fazla gizlilik sağlayabilirsiniz.
* **Özel User-Agent Belirleme:** Kendi seçtiğiniz bir User-Agent başlığını kullanarak daha kontrollü bir kimlik sunabilirsiniz.
* **Hassas Veri Maskeleme:** Loglama sırasında istek gövdesi gibi potansiyel olarak hassas veriler maskelenir veya kısaltılır.

**Unutmayın:** Bu araç istekleri doğrudan sizin genel IP adresiniz üzerinden gönderir. Tam anonimlik için sistem düzeyinde bir VPN veya Tor gibi araçlar kullanmanız önerilir.

## Önemli Notlar ve Uyarılar

* **Yüksek Hacimli Testler:** Bu araç, hedef sunuculara ve ağınıza önemli ölçüde yük bindirebilir. Testleri dikkatli bir şekilde ve yalnızca yetkili olduğunuz sistemlerde gerçekleştirin. Yanlış yapılandırılmış veya çok yüksek eş zamanlılıkta yapılan testler, hedef sunucunun çökmesine veya ağ sorunlarına yol açabilir.
* **Sorumluluk:** Bu aracın kullanımından kaynaklanan herhangi bir olumsuz sonuçtan kullanıcı sorumludur.
* **Anonimlik:** Araç, User-Agent başlığı gibi bazı bilgileri gizlemenize yardımcı olsa da, istekler genel IP adresiniz üzerinden gönderilecektir. Tam anonimlik için ek önlemler almanız gerekebilir.
* **Loglama:** Özel başlıklar veya istek gövdesi gibi bilgileri loglarken dikkatli olun. Hassas bilgilerin log dosyalarında görünmesini istemeyebilirsiniz.

## Assertion'lar (Test Sonu Kontrolleri) Hakkında Detaylı Bilgi

Assertion'lar, test tamamlandıktan sonra belirli performans kriterlerinin karşılanıp karşılanmadığını otomatik olarak kontrol etmenizi sağlar. Şu anda desteklenen assertion tipleri şunlardır:

* **Ortalama Yanıt Süresi (`latency`):** Testin tüm başarılı istekleri için hesaplanan ortalama yanıt süresinin, belirlediğiniz maksimum süreyi (saniye) geçip geçmediğini kontrol eder.
* **Başarısızlık Oranı (`failure`):** Test sırasında oluşan başarısız isteklerin (hatalar veya 4xx/5xx durum kodları) toplam gönderilen isteklere oranının, belirlediğiniz maksimum yüzdeyi geçip geçmediğini kontrol eder.

Test sonunda, tanımladığınız assertion'ların sonuçları (geçti/kaldı) konsolda görüntülenecektir.

## Loglama Hakkında Detaylı Bilgi

Araç, iki seviyede loglama sunar:

* **Konsol Loglama (INFO seviyesi):** Testin genel ilerlemesi, önemli olaylar (başlangıç, bitiş, hatalar, özet sonuçlar) ve kullanıcıya yönelik bilgiler konsolda görüntülenir.
* **Dosya Loglama (DEBUG seviyesi - isteğe bağlı):** Eğer kullanıcı isterse, tüm isteklerin detaylı bilgileri (HTTP metodu, URL, başlıklar, durum kodu, yanıt süresi, hatalar vb.) bir log dosyasına kaydedilir. Bu loglar, test sırasında oluşan sorunları daha ayrıntılı bir şekilde incelemek için faydalı olabilir. Log dosyası, testin başlatıldığı dizinde oluşturulur (eğer tam bir yol belirtilmediyse).

## Lisans

Bu araç MIT Lisansı altında lisanslanmıştır. Daha fazla bilgi için lütfen [LICENSE](LICENSE) dosyasına bakın.
