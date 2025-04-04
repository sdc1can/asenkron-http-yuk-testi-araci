import asyncio
import aiohttp
import time
import logging
import statistics
import sys
import json
from collections import defaultdict
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Union, NamedTuple
import random # User-Agent ve URL seçimi için
import os # Dosya yolu işlemleri için
import ssl # SSL context oluşturmak için (opsiyonel, aiohttp None/False ile halleder)

# --- Logger Kurulumu ---
# Uygulama genelinde kullanılacak logger nesnesi
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG) # Tüm seviyeleri yakala (dosya için DEBUG, konsol için INFO)

# Konsol Handler: Kullanıcıya genel bilgileri ve hataları gösterir
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO) # Sadece INFO ve üzeri seviyeleri konsola yaz
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')
console_handler.setFormatter(console_formatter)
log.addHandler(console_handler)

# Dosya Handler: Detaylı loglama için (main içinde ayarlanacak)
file_handler = None

# --- Gizlilik Odaklı İyileştirmeler ---
# Yaygın tarayıcı User-Agent stringleri listesi
COMMON_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.3 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/110.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.3 Mobile/15E148 Safari/604.1"
]

def get_user_agent_preference() -> Optional[str]:
    """Kullanıcıdan hangi User-Agent başlığının kullanılacağını sorar."""
    print("\n--- User-Agent Ayarları ---")
    print("Hedef sunucuya gönderilecek User-Agent başlığını yapılandırın.")
    print("Bu başlık, bu test aracını sunucuya tanıtabilir.")
    print("Gizliliği artırmak için genel bir tarayıcı UA'sı seçebilir veya hiç göndermeyebilirsiniz.")

    options = {
        '1': "Rastgele Genel Tarayıcı UA'sı (Önerilen)",
        '2': f"aiohttp Varsayılanı (örn: aiohttp/{aiohttp.__version__} - Aracı belli eder)",
        '3': "User-Agent Başlığını Gönderme",
        '4': "Özel User-Agent Gir"
    }
    default_option = '1'

    while True:
        print("\nLütfen bir seçenek belirleyin:")
        for key, value in options.items():
            print(f"  {key}. {value}")

        choice = get_input("Seçiminiz", default=default_option)

        if choice == '1':
            selected_ua = random.choice(COMMON_USER_AGENTS)
            log.info(f"Rastgele seçilen User-Agent kullanılacak: {selected_ua}")
            return selected_ua
        elif choice == '2':
            log.info("Varsayılan aiohttp User-Agent kullanılacak.")
            return None # Varsayılan davranış için None döndürülür
        elif choice == '3':
            log.info("User-Agent başlığı gönderilmeyecek.")
            return "" # Başlığın gönderilmemesi için boş string döndürülür
        elif choice == '4':
            custom_ua = get_input("Kullanılacak özel User-Agent değerini girin:")
            if custom_ua:
                log.info(f"Özel User-Agent kullanılacak: {custom_ua}")
                return custom_ua
            else:
                print("Hata: Özel User-Agent boş olamaz. Lütfen tekrar deneyin.")
        else:
            print("Hata: Geçersiz seçim. Lütfen listeden bir numara girin.")


def mask_sensitive_data(data: Union[str, Dict, Any]) -> str:
    """Loglamada hassas olabilecek veriyi (örn. JSON gövdesi) maskeler."""
    if isinstance(data, dict):
        # İçeriği loglamak yerine sadece tipini belirtir
        return "{...JSON Verisi...}"
    elif isinstance(data, str):
        # Çok uzun metinleri kısaltarak log boyutunu yönetir
        if len(data) > 100:
            return data[:50] + "... (kısaltıldı)"
        # TODO: Gelecekte 'password', 'token' gibi anahtar kelimeleri arayıp maskeleme eklenebilir.
        return data
    else:
        # Diğer veri tipleri için sadece tipini loglar
        return f"<{type(data).__name__} Verisi>"

# --- Yardımcı İnput Fonksiyonları ---
def get_input(prompt: str, default: Optional[str] = None) -> str:
    """Kullanıcıdan girdi alır, varsayılan değeri destekler ve girdinin kenar boşluklarını temizler."""
    if default:
        prompt_text = f"{prompt} [{default}]: "
    else:
        prompt_text = f"{prompt}: "

    value = input(prompt_text).strip()
    # Kullanıcı bir değer girmezse ve varsayılan varsa, varsayılanı döndür.
    # Yoksa kullanıcının girdiği değeri (boşsa boş string) döndür.
    return value if value else default if default is not None else ""


def get_positive_integer_input(prompt: str, default: Optional[int] = None) -> int:
    """Kullanıcıdan pozitif bir tamsayı alır, hata kontrolü ve varsayılan değer desteği sağlar."""
    default_str = str(default) if default is not None else None
    while True:
        try:
            value_str = get_input(prompt, default_str)
            if not value_str:
                # Kullanıcı boş girdi ve varsayılan değer var ise onu kullan
                if default is not None:
                    return default
                else: # Varsayılan yoksa ve boşsa hata ver
                    print("Hata: Bu alan boş bırakılamaz.")
                    continue

            value = int(value_str)
            if value > 0:
                return value
            else:
                print("Hata: Lütfen 0'dan büyük bir tamsayı girin.")
        except ValueError:
            print("Hata: Geçersiz giriş. Lütfen bir tamsayı girin.")
        except Exception as e: # Beklenmedik hatalar için
            print(f"Beklenmeyen bir hata oluştu: {e}")


def get_positive_float_input(prompt: str, default: Optional[float] = None) -> float:
    """Kullanıcıdan pozitif bir ondalık sayı veya sıfır alır, hata kontrolü ve varsayılan değer desteği sağlar."""
    default_str = str(default) if default is not None else None
    while True:
        try:
            value_str = get_input(prompt, default_str)
            if not value_str:
                if default is not None:
                    return default
                else:
                    print("Hata: Bu alan boş bırakılamaz.")
                    continue

            value = float(value_str)
            # Rate limit için 0'a izin verilir (limitsiz anlamına gelir)
            # Timeout için 0'dan büyük olmalı (ya da pozitif olmalı) - Bunu get_positive_integer_input'tan aldık, float'a çevirdik
            if value >= 0:
                 # Zaman aşımı 0 olmamalı, düzeltme:
                 if "zaman aşımı" in prompt.lower() and value == 0:
                      print("Hata: Zaman aşımı 0 olamaz. Lütfen pozitif bir değer girin.")
                      continue
                 return value
            else:
                 print("Hata: Lütfen pozitif bir sayı veya 0 girin (zaman aşımı hariç).")
        except ValueError:
            print("Hata: Geçersiz giriş. Lütfen bir sayı girin (örn: 10.5 veya 0).")
        except Exception as e:
            print(f"Beklenmeyen bir hata oluştu: {e}")


def get_yes_no_input(prompt: str, default_yes: bool = False) -> bool:
    """Kullanıcıdan Evet/Hayır (E/H) cevabı alır, varsayılan cevap belirleme imkanı sunar."""
    default_char = 'E' if default_yes else 'H'
    while True:
        answer = get_input(f"{prompt} (E/H)", default=default_char).upper()
        if answer == 'E':
            return True
        elif answer == 'H':
            return False
        else:
            print("Hata: Lütfen sadece 'E' (Evet) veya 'H' (Hayır) girin.")

# --- Test Konfigürasyonu ---
class TestConfig(NamedTuple):
    """Testin tüm parametrelerini içeren yapı."""
    target_url: Optional[str] # Tek URL modu için kullanılır (url_file varsa None olabilir)
    url_file: Optional[str]   # URL listesi dosyası modu için kullanılır (tek URL varsa None olabilir)
    http_method: str          # Kullanılacak HTTP metodu (GET, POST, vb.)
    concurrency: int          # Eş zamanlı çalışacak worker (istekçi) sayısı
    duration: Optional[int]   # Testin süresi (saniye) (total_requests varsa None)
    total_requests: Optional[int] # Gönderilecek toplam istek sayısı (duration varsa None)
    timeout_seconds: float    # Her bir isteğin zaman aşımı süresi (saniye)
    user_agent_preference: Optional[str] # Kullanıcının User-Agent tercihi (None, "", veya UA string'i)
    custom_headers: Dict[str, str] # Gönderilecek ek HTTP başlıkları
    request_data: Optional[Union[str, Dict]] # Gönderilecek istek gövdesi (varsa)
    is_json_data: bool        # İstek gövdesi JSON formatında mı?
    log_filename: Optional[str] # Detaylı logların yazılacağı dosya adı (varsa)
    target_rps: float         # Hedeflenen toplam Saniye Başına İstek (RPS) (0 = limitsiz)
    verify_ssl: bool          # SSL/TLS sertifikalarının doğrulanıp doğrulanmayacağı
    assertions: Dict[str, float] # Test sonu kontrolleri (örn: max ortalama gecikme, max hata oranı)

# --- İstatistik Toplama Sınıfı ---
class StatsCollector:
    """HTTP isteklerinin sonuçlarını (başarı, hata, süre) toplar, saklar ve özetler."""
    def __init__(self):
        self.start_time: float = time.monotonic() # İstatistik toplamanın başladığı an
        self.requests_sent: int = 0           # Toplam gönderilen istek sayısı
        self.requests_successful: int = 0     # Başarılı (2xx, 3xx) dönen istek sayısı
        self.requests_failed: int = 0         # Başarısız (hata veya 4xx, 5xx) istek sayısı
        self.response_times: List[float] = [] # Başarılı isteklerin yanıt süreleri (saniye)
        self.status_codes: Dict[int, int] = defaultdict(int) # Alınan HTTP durum kodları ve sayıları
        self.errors: Dict[str, int] = defaultdict(int) # Oluşan hata türleri (örn. TimeoutError) ve sayıları
        self._lock = asyncio.Lock()           # Eş zamanlı erişimde veri tutarlılığını sağlamak için kilit
        # TestRunner tarafından test bittiğinde ayarlanacak olan gerçek test süresi
        self.actual_test_duration: float = 0.0

    async def add_result(self, status_code: Optional[int], response_time: float, error: Optional[str]):
        """Bir isteğin sonucunu (durum kodu, süre, hata) asenkron olarak kaydeder."""
        async with self._lock: # Kilit alarak sayaçları güvenli bir şekilde artır
            self.requests_sent += 1
            if error:
                # Eğer bir hata mesajı varsa (örn. timeout, bağlantı hatası, SSL hatası)
                self.requests_failed += 1
                # Hatanın genel türünü al (örn. 'TimeoutError', 'ConnectionError', 'SSLError')
                error_type = error.split(':')[0]
                # SSLError'ları daha belirgin hale getirelim
                if "SSL" in error or "certificate verify failed" in error:
                    error_type = "SSLError" # Genel SSL hatası olarak grupla
                self.errors[error_type] += 1
                log.debug(f"İstek hatası kaydedildi: {error}")
            elif status_code is not None:
                # Eğer durum kodu alındıysa
                self.status_codes[status_code] += 1
                if 200 <= status_code < 400:
                    # 2xx (Başarılı) veya 3xx (Yönlendirme) durum kodları başarılı sayılır
                    self.requests_successful += 1
                    # Sadece başarılı isteklerin yanıt sürelerini kaydet
                    self.response_times.append(response_time)
                else:
                    # 4xx (İstemci Hatası) veya 5xx (Sunucu Hatası) durum kodları başarısız sayılır
                    self.requests_failed += 1
                    log.debug(f"Başarısız durum kodu alındı: {status_code}")

    def calculate_summary(self) -> Dict[str, Any]:
        """Toplanan verilere dayanarak özet istatistikleri hesaplar ve döndürür."""
        # Gerçek test süresini kullan (TestRunner tarafından ayarlanır)
        total_duration = self.actual_test_duration if self.actual_test_duration > 0 else (time.monotonic() - self.start_time)
        rps = self.requests_sent / total_duration if total_duration > 0 else 0
        failure_rate = (self.requests_failed / self.requests_sent * 100) if self.requests_sent > 0 else 0.0

        summary = {
            "actual_test_duration": total_duration,
            "total_requests_sent": self.requests_sent,
            "successful_requests": self.requests_successful,
            "failed_requests": self.requests_failed,
            "requests_per_second": rps,
            "failure_rate_percent": failure_rate, # Assertion kontrolü için kullanılır
            "status_code_distribution": dict(self.status_codes), # defaultdict'u normal dict'e çevir
            "error_distribution": dict(self.errors)             # defaultdict'u normal dict'e çevir
        }

        if self.response_times:
            # Başarılı istek varsa yanıt süresi istatistiklerini hesapla
            summary["average_response_time"] = statistics.mean(self.response_times)
            summary["min_response_time"] = min(self.response_times)
            summary["max_response_time"] = max(self.response_times)
            try:
                # Medyan hesaplamak için en az 2 veri noktası gerekir
                if len(self.response_times) > 1:
                   summary["median_response_time"] = statistics.median(self.response_times)
                # Yüzdelikler hesaplamak için daha fazla veri gerekebilir
                # Örnek: 95. yüzdelik (en az 10-20 veri noktası önerilir)
                # if len(self.response_times) >= 20:
                #     summary["95th_percentile_response_time"] = statistics.quantiles(self.response_times, n=100)[94]
            except statistics.StatisticsError:
                # Hesaplama sırasında hata olursa (örn. tek veri ile median) atla
                pass
        else:
            # Başarılı istek yoksa, yanıt süresi metriklerini 0 olarak ayarla
            summary["average_response_time"] = 0.0
            summary["min_response_time"] = 0.0
            summary["max_response_time"] = 0.0
            summary["median_response_time"] = 0.0

        return summary

    async def get_current_progress(self) -> Tuple[int, int, float]:
        """Test sırasında anlık ilerleme verilerini (gönderilen, hatalı, anlık RPS) döndürür."""
        async with self._lock:
            current_duration = time.monotonic() - self.start_time
            current_rps = self.requests_sent / current_duration if current_duration > 0 else 0
            return self.requests_sent, self.requests_failed, current_rps

# --- HTTP İstek Fonksiyonu ---
async def make_request(
    session: aiohttp.ClientSession,
    method: str,
    url: str,
    headers: Optional[Dict[str, str]], # Gönderilecek başlıklar (UA içerebilir veya None/"" olabilir)
    request_body: Optional[Union[str, Dict[str, Any]]], # Gönderilecek veri (varsa)
    is_json: bool, # Gönderilen veri JSON formatında mı?
    timeout: float, # İstek başına zaman aşımı süresi (saniye)
    verify_ssl: bool, # SSL sertifikası doğrulanacak mı?
    stats: StatsCollector # İstatistikleri kaydetmek için StatsCollector nesnesi
) -> Tuple[float, Optional[int], Optional[str]]: # (süre, durum_kodu, hata_mesajı) döndürür
    """
    Belirtilen parametrelerle tek bir HTTP isteği yapar, sonucunu (başarı/hata/süre)
    StatsCollector'a kaydeder ve sonucu (süre, durum kodu, hata mesajı) döndürür.
    """
    start_req_time = time.monotonic() # İstek başlangıç zamanı
    status_code: Optional[int] = None # İstek sonucu alınan durum kodu
    error_msg: Optional[str] = None   # İstek sırasında oluşan hata mesajı (varsa)
    response_time: float = 0.0        # İsteğin tamamlanma süresi

    # Gönderilecek başlıkları hazırla:
    request_headers = headers.copy() if headers is not None else {}

    # User-Agent yönetimi:
    if request_headers.get('User-Agent') == "":
        request_headers.pop('User-Agent', None)

    # aiohttp istek parametrelerini hazırla
    request_kwargs = {
        "headers": request_headers if request_headers else None,
        "timeout": aiohttp.ClientTimeout(total=timeout),
        # SSL doğrulamasını yapılandırmadan gelen değere göre ayarla
        # True ise None (varsayılan doğrulama), False ise False (doğrulama yok)
        "ssl": None if verify_ssl else False
    }

    # İstek gövdesini (varsa) ekle
    if request_body:
        if is_json and isinstance(request_body, dict):
            request_kwargs["json"] = request_body
        else:
            request_kwargs["data"] = request_body

    # HTTP isteğini yap ve olası hataları yakala
    try:
        # SSL doğrulama kapalıysa ve URL HTTPS ise bir uyarı loglayalım (her istekte değil, belki bir kere başta?)
        # Şimdilik burada loglayabiliriz ama çok fazla log üretebilir.
        # if not verify_ssl and url.startswith("https://"):
        #     log.debug(f"HTTPS isteği ({url}) SSL doğrulaması KAPALI olarak yapılıyor.")

        async with session.request(method, url, **request_kwargs) as response:
            status_code = response.status
            await response.read() # Yanıtı tüket
    except aiohttp.ClientConnectorSSLError as e:
         # SSL ile ilgili spesifik hatalar (örn. sertifika doğrulama hatası)
         error_msg = f"SSLError: Güvenli bağlantı hatası - {e}"
         # Durum kodu bu durumda olmaz, hata mesajı yeterli.
    except aiohttp.ClientConnectorError as e:
        # Bağlantı kurulamadı (örn. DNS çözme hatası, sunucu kapalı)
        error_msg = f"ConnectionError: Bağlantı hatası - {e}"
    except asyncio.TimeoutError:
        # Belirtilen `timeout` süresi içinde yanıt alınamadı
        error_msg = f"TimeoutError: İstek {timeout:.1f} saniyede zaman aşımına uğradı."
    except aiohttp.ClientResponseError as e:
        # Sunucudan bir hata yanıtı alındı (örn. 404 Not Found, 500 Internal Server Error)
        error_msg = f"ClientResponseError: Sunucu hatası - Durum {e.status}: {e.message}"
        status_code = e.status # Hata nesnesinden durum kodunu alıp kaydederiz
    except aiohttp.ClientError as e:
        # aiohttp kütüphanesinden kaynaklanan diğer genel istemci hataları
        error_msg = f"ClientError: {type(e).__name__}: {e}"
    except Exception as e:
        # Kodun beklemediği diğer tüm hatalar (programlama hatası vb.)
        error_msg = f"UnexpectedError: Beklenmedik hata - {type(e).__name__}: {e}"
        log.exception(f"make_request içinde beklenmedik hata ({url}):")
    finally:
        # İstek başarıyla tamamlansa da, hata alsa da süre hesaplanır
        response_time = time.monotonic() - start_req_time
        # Sonuç (durum kodu veya hata) istatistik toplayıcıya kaydedilir
        await stats.add_result(status_code, response_time, error_msg)
        # DEBUG seviyesinde her isteğin detaylı sonucunu logla
        log.debug(
            f"{method} {url} - Durum: {status_code if status_code else 'HATA'} "
            f"- Süre: {response_time:.4f}s "
            f"- Hata: {error_msg if error_msg else 'Yok'}"
        )

    # Hesaplanan süre, alınan durum kodu ve hata mesajını döndür
    return response_time, status_code, error_msg

# --- Test Yürütücü Sınıfı ---
class TestRunner:
    """Testin yapılandırılmasını, eş zamanlı yürütülmesini ve sonuçların raporlanmasını yönetir."""

    def __init__(self, config: TestConfig):
        self.config: TestConfig = config              # Test parametreleri
        self.stats: StatsCollector = StatsCollector() # İstatistik toplayıcı nesnesi
        self.stop_event: asyncio.Event = asyncio.Event() # Testi durdurma sinyali
        self.url_list: List[str] = []                 # Hedef URL'lerin listesi
        self.target_delay_per_worker: float = 0.0     # Rate limiting için worker başına bekleme süresi (saniye)

        # URL'leri yükle (dosyadan veya tek URL'den)
        if config.url_file:
            try:
                # Göreceli yolları da ele almak için dosya yolunu normalize et
                normalized_path = os.path.abspath(config.url_file)
                with open(normalized_path, 'r', encoding='utf-8') as f:
                    # Dosyadaki her satırı oku, boşlukları temizle, boş olmayan ve http ile başlayanları al
                    self.url_list = [line.strip() for line in f if line.strip() and line.startswith(("http://", "https://"))]
                if not self.url_list:
                    raise ValueError(f"URL dosyası '{normalized_path}' boş veya geçerli URL içermiyor.")
                log.info(f"{len(self.url_list)} URL '{normalized_path}' dosyasından başarıyla yüklendi.")
            except FileNotFoundError:
                log.error(f"Hata: Belirtilen URL dosyası bulunamadı: {normalized_path}")
                raise # Programın başlamadan hatayla bitmesini sağla
            except Exception as e:
                log.error(f"Hata: URL dosyası okunurken bir sorun oluştu ({normalized_path}): {e}")
                raise # Programın başlamadan hatayla bitmesini sağla
        elif config.target_url:
            # Eğer tek URL verildiyse, onu tek elemanlı bir liste yap
            self.url_list = [config.target_url]
            log.info(f"Tek hedef URL kullanılacak: {config.target_url}")
        else:
            # Bu durumun oluşmaması gerekir (main fonksiyonunda kontrol edilir)
            raise ValueError("Hata: Ne hedef URL ne de URL dosyası belirtilmedi!")

        # Rate limiting için worker başına düşen hedef gecikmeyi hesapla
        if config.target_rps > 0 and config.concurrency > 0:
            try:
                rps_per_worker = config.target_rps / config.concurrency
                self.target_delay_per_worker = 1.0 / rps_per_worker
                log.info(f"Rate Limit Aktif: Hedef {config.target_rps:.2f} RPS ({config.concurrency} worker ile worker başına ~{rps_per_worker:.2f} RPS => ~{self.target_delay_per_worker:.4f}s gecikme)")
            except ZeroDivisionError:
                 log.warning("Concurrency 0 olduğu için rate limiting hesaplanamadı/devre dışı.")
                 self.target_delay_per_worker = 0.0
        else:
            log.info("Rate Limit Aktif Değil (Hedef RPS 0 veya belirtilmemiş). İstekler mümkün olduğunca hızlı gönderilecek.")


    async def _worker(self, worker_id: int, session: aiohttp.ClientSession):
        """Tek bir worker'ın (eş zamanlı istek göndericinin) ana görev döngüsü."""
        log.debug(f"Worker {worker_id} başlatıldı.")
        while not self.stop_event.is_set(): # Durdurma sinyali gelene kadar çalış
            start_cycle_time = time.monotonic() # Rate limiting için döngü başlangıç zamanı

            if not self.url_list: # Ekstra güvenlik kontrolü
                log.error(f"Worker {worker_id} için URL listesi boş! Worker durduruluyor.")
                break
            target_url = random.choice(self.url_list) # URL listesinden rastgele bir URL seç

            # İstek başlıklarını hazırla
            final_headers = self.config.custom_headers.copy()
            ua_already_set_manually = any(k.lower() == 'user-agent' for k in self.config.custom_headers)

            if not ua_already_set_manually:
                ua_pref = self.config.user_agent_preference
                actual_ua_to_send = None

                if ua_pref is None: pass # aiohttp varsayılanı
                elif ua_pref == "": pass # Gönderilmeyecek (make_request halleder)
                # Rastgele seçildiyse (main'de tek seçildi), onu kullan
                elif self.config.user_agent_preference in COMMON_USER_AGENTS:
                     actual_ua_to_send = self.config.user_agent_preference
                     # Alternatif: Her istekte farklı UA: actual_ua_to_send = random.choice(COMMON_USER_AGENTS)
                else: # Özel girilen UA
                     actual_ua_to_send = ua_pref

                if actual_ua_to_send:
                    final_headers['User-Agent'] = actual_ua_to_send
                elif ua_pref == "":
                     final_headers['User-Agent'] = "" # make_request'in anlaması için

            try:
                # Asıl HTTP isteğini yap (verify_ssl bilgisini de geçirerek)
                await make_request(
                    session,
                    self.config.http_method,
                    target_url,
                    final_headers,
                    self.config.request_data,
                    self.config.is_json_data,
                    self.config.timeout_seconds,
                    self.config.verify_ssl, # SSL doğrulama ayarını ilet
                    self.stats
                )

                # Rate Limiting Uygulaması
                if self.target_delay_per_worker > 0:
                    elapsed_time = time.monotonic() - start_cycle_time
                    sleep_duration = self.target_delay_per_worker - elapsed_time
                    if sleep_duration > 0:
                        await asyncio.sleep(sleep_duration)

            except Exception as e:
                 log.error(f"Worker {worker_id} döngüsünde beklenmedik hata: {e}")
                 await asyncio.sleep(0.1) # Hata durumunda kısa bekleme

            # Rate limiting yoksa event loop'a kontrolü geri ver
            if self.target_delay_per_worker <= 0:
                  await asyncio.sleep(0)

        log.debug(f"Worker {worker_id} durduruldu.")

    async def _progress_reporter(self, interval: int = 1):
        """Belirlenen aralıklarla anlık test ilerlemesini konsola yazdırır."""
        last_sent_count = 0
        while not self.stop_event.is_set():
            try:
                await asyncio.wait_for(self.stop_event.wait(), timeout=interval)
                break # Stop event geldi
            except asyncio.TimeoutError:
                # Interval doldu, raporla
                sent, failed, rps = await self.stats.get_current_progress()
                if sent > last_sent_count or last_sent_count == 0:
                    failure_rate = (failed / sent * 100) if sent > 0 else 0.0
                    rps_target_str = f"(Hedef: {self.config.target_rps:.1f} RPS)" if self.config.target_rps > 0 else "(Limitsiz)"
                    print(
                        f"\rİlerleme: {sent} istek ({failed} hatalı, Hata: {failure_rate:.1f}%), "
                        f"Anlık RPS: {rps:.2f} {rps_target_str}      ", # Ekstra boşluklar temizler
                        end=""
                    )
                    sys.stdout.flush()
                    last_sent_count = sent
            except Exception as e:
                log.error(f"Progress reporter içinde hata oluştu: {e}")
                break # Raporlayıcıyı durdur

        print("\r" + " " * 80 + "\r", end="") # Son satırı temizle
        print() # Yeni satır
        log.debug("Progress reporter durduruldu.")


    def _check_assertions(self, summary: Dict[str, Any]) -> Tuple[Dict[str, bool], bool]:
        """Tanımlanan test sonu kontrollerini (assertion'ları) yapar ve sonuçları döndürür."""
        results = {}
        passed_all = True
        print("\n--- Assertion Kontrolü ---")
        if not self.config.assertions:
            print("-> Hiç assertion tanımlanmamış.")
            return {}, True

        # Max Ortalama Yanıt Süresi Kontrolü
        max_latency = self.config.assertions.get('max_avg_latency')
        if max_latency is not None:
            actual_latency = summary.get('average_response_time')
            if actual_latency is not None and actual_latency >= 0.0:
                passed = actual_latency <= max_latency
                results['max_avg_latency'] = passed
                print(f" -> Max Ortalama Yanıt Süresi <= {max_latency:.3f}s: {'GEÇTİ' if passed else 'KALDI'} (Gerçekleşen: {actual_latency:.3f}s)")
                if not passed: passed_all = False
            else:
                results['max_avg_latency'] = False
                print(f" -> Max Ortalama Yanıt Süresi <= {max_latency:.3f}s: HESAPLANAMADI (Başarılı istek yok veya özet eksik)")
                passed_all = False


        # Max Başarısızlık Oranı Kontrolü
        max_failure = self.config.assertions.get('max_failure_rate')
        if max_failure is not None:
            actual_failure = summary.get('failure_rate_percent')
            if actual_failure is not None and actual_failure >= 0.0:
                passed = actual_failure <= max_failure
                results['max_failure_rate'] = passed
                print(f" -> Max Başarısızlık Oranı <= {max_failure:.1f}%: {'GEÇTİ' if passed else 'KALDI'} (Gerçekleşen: {actual_failure:.1f}%)")
                if not passed: passed_all = False
            else:
                results['max_failure_rate'] = False
                print(f" -> Max Başarısızlık Oranı <= {max_failure:.1f}%: HESAPLANAMADI (İstek gönderilemedi veya özet eksik)")
                passed_all = False

        print(f"\n Assertion Sonucu: {'TÜMÜ BAŞARIYLA GEÇTİ' if passed_all else 'BAZI KONTROLLER BAŞARISIZ OLDU'}")
        return results, passed_all


    def _print_summary(self, summary: Dict[str, Any], assertion_results: Dict[str, bool]):
        """Hesaplanan test özeti istatistiklerini ve assertion sonuçlarını konsola detaylı olarak yazdırır."""
        print("\n--- Test Sonuçları Özeti ---")
        print(f"* Toplam Çalışma Süresi: {summary.get('actual_test_duration', 0.0):.2f} saniye")
        print(f"* Toplam Gönderilen İstek: {summary.get('total_requests_sent', 0)}")
        print(f"* Başarılı İstek (2xx, 3xx): {summary.get('successful_requests', 0)}")
        print(f"* Başarısız İstek (Hata veya 4xx, 5xx): {summary.get('failed_requests', 0)}")
        print(f"* Başarısızlık Oranı: {summary.get('failure_rate_percent', 0.0):.2f}%")

        if summary.get('actual_test_duration', 0.0) > 0:
            actual_rps = summary.get('requests_per_second', 0.0)
            rps_target_str = f"(Hedef: {self.config.target_rps:.1f} RPS)" if self.config.target_rps > 0 else "(Limitsiz)"
            print(f"* Ortalama Saniye Başına İstek (RPS): {actual_rps:.2f} {rps_target_str}")
        else:
            print("* Sıfır sürede RPS hesaplanamadı.")

        if summary.get('successful_requests', 0) > 0:
            print("\n* Başarılı İsteklerin Yanıt Süreleri:")
            print(f"  - Ortalama: {summary.get('average_response_time', 0.0):.4f} saniye")
            print(f"  - Minimum: {summary.get('min_response_time', 0.0):.4f} saniye")
            print(f"  - Maksimum: {summary.get('max_response_time', 0.0):.4f} saniye")
            if 'median_response_time' in summary and summary['median_response_time'] > 0: # Medyan hesaplandıysa ve 0 değilse
                print(f"  - Medyan: {summary['median_response_time']:.4f} saniye")
        elif summary.get('total_requests_sent', 0) > 0:
            print("\n* Hiç başarılı istek tamamlanmadı, yanıt süresi istatistikleri hesaplanamadı.")

        print("\n* Durum Kodu Dağılımı:")
        status_dist = summary.get('status_code_distribution', {})
        if status_dist:
            for code, count in sorted(status_dist.items()):
                print(f"  - HTTP {code}: {count} istek")
        elif summary.get('total_requests_sent', 0) > 0 and not summary.get('error_distribution', {}):
             print("  - Durum kodu alınamadı (muhtemelen tümü başarısız oldu ancak hata tipi kaydedilmedi?).")
        elif not summary.get('error_distribution', {}):
             print("  - Hiçbir HTTP yanıtı alınamadı veya istek gönderilemedi.")


        print("\n* Hata Dağılımı (Bağlantı, Zaman Aşımı, SSL vb.):")
        error_dist = summary.get('error_distribution', {})
        if error_dist:
            for error, count in sorted(error_dist.items()):
                print(f"  - {error}: {count} kez")
        elif summary.get('failed_requests', 0) > 0 and not status_dist:
             print(f"  - {summary.get('failed_requests', 0)} başarısız istek var ancak detaylı hata tipi kaydedilmedi.")
        elif summary.get('failed_requests', 0) == 0 and not error_dist:
             print("  - Bu türde hata kaydedilmedi.")


        print("\n--- Gizlilik ve Yapılandırma Notları ---")
        url_source = f"URL Dosyası: {self.config.url_file}" if self.config.url_file else f"Tek URL: {self.config.target_url}"
        print(f"- URL Kaynağı: {url_source}")

        ua_display = "Belirtilmedi/Özel Header İçinde"
        ua_in_custom_header = any(k.lower() == 'user-agent' for k in self.config.custom_headers)
        if not ua_in_custom_header:
            ua_pref = self.config.user_agent_preference
            if ua_pref is None: ua_display = f"aiohttp Varsayılanı (örn: aiohttp/{aiohttp.__version__})"
            elif ua_pref == "": ua_display = "Gönderilmedi"
            elif self.config.user_agent_preference in COMMON_USER_AGENTS: ua_display = f"Rastgele Seçilen ({ua_pref[:30]}...)"
            else: ua_display = f"Özel Girilen ({ua_pref[:30]}...)"

        print(f"- Kullanılan User-Agent Ayarı: {ua_display}")
        print("- İstekler sizin genel IP adresiniz üzerinden yapıldı.")

        # SSL Durumunu Göster
        ssl_status = "AKTİF (Sertifikalar Doğrulanıyor)" if self.config.verify_ssl else "DEVRE DIŞI (Sertifikalar DOĞRULANMIYOR - Güvenlik Riski!)"
        print(f"- SSL/TLS Sertifika Doğrulaması: {ssl_status}")

        print("- DNS sorguları sisteminizin varsayılan çözümleyicisine gönderildi (ISP tarafından izlenebilir).")
        if self.config.log_filename:
            print(f"- Detaylı DEBUG seviyesi loglar '{self.config.log_filename}' dosyasına kaydedildi.")


    async def run(self):
        """Testi başlatır, worker'ları çalıştırır, süreyi/istek sayısını yönetir ve sonuçları raporlar."""

        log.info("--- Test Başlatılıyor ---")
        log.info(f"URL Kaynağı: {'Dosya: ' + self.config.url_file if self.config.url_file else 'Tek URL: ' + self.config.target_url}")
        log.info(f"HTTP Metodu: {self.config.http_method}")
        log.info(f"Eşzamanlılık Seviyesi (Worker): {self.config.concurrency}")
        if self.config.duration: log.info(f"Test Süresi: {self.config.duration} saniye")
        if self.config.total_requests: log.info(f"Toplam İstek Sayısı Hedefi: {self.config.total_requests}")
        if self.config.target_rps > 0: log.info(f"Hedeflenen RPS: {self.config.target_rps:.2f} (Rate Limit Aktif)")
        else: log.info("Hedeflenen RPS: Limitsiz (Rate Limit Aktif Değil)")
        log.info(f"İstek Zaman Aşımı: {self.config.timeout_seconds} saniye")

        # SSL Durumunu Logla
        ssl_log_status = "Aktif" if self.config.verify_ssl else "Devre Dışı"
        log.info(f"SSL Sertifika Doğrulaması: {ssl_log_status}")
        if not self.config.verify_ssl:
             log.warning("GÜVENLİK UYARISI: SSL/TLS Sertifika Doğrulaması DEVRE DIŞI!")

        # User-Agent loglaması
        ua_log_msg = "Belirtilmedi/Özel Header İçinde"
        ua_in_custom_header = any(k.lower() == 'user-agent' for k in self.config.custom_headers)
        if not ua_in_custom_header:
            ua_pref = self.config.user_agent_preference
            if ua_pref is None: ua_log_msg = "aiohttp Varsayılanı"
            elif ua_pref == "": ua_log_msg = "Gönderilmeyecek"
            elif self.config.user_agent_preference in COMMON_USER_AGENTS: ua_log_msg = "Rastgele Genel Tarayıcı"
            else: ua_log_msg = f"Özel: {ua_pref}"
        log.info(f"User-Agent Ayarı: {ua_log_msg}")

        log.info(f"Özel Başlıklar: {self.config.custom_headers if self.config.custom_headers else '(Yok)'}")

        if self.config.request_data:
            log.info(f"İstek Gövde Türü: {'JSON' if self.config.is_json_data else 'Metin/Diğer'}")
            log.info("İstek Gövdesi: Evet (İçerik INFO'da gösterilmez)")
            log.debug(f"Gönderilecek Veri (Maskelenmiş): {mask_sensitive_data(self.config.request_data)}")
        else:
            log.info("İstek Gövdesi: Hayır")
        log.info(f"Assertions: {self.config.assertions if self.config.assertions else '(Yok)'}")


        # aiohttp için TCPConnector ayarları
        # SSL doğrulamasını yapılandırmaya göre ayarla
        # verify_ssl True ise None (varsayılan context), False ise False (doğrulama yok)
        connector = aiohttp.TCPConnector(
            limit=None,
            limit_per_host=0,
            enable_cleanup_closed=True,
            ssl=None if self.config.verify_ssl else False # Burası önemli
        )

        start_run_time = time.monotonic() # Gerçek testin başladığı an
        async with aiohttp.ClientSession(connector=connector) as session:
            worker_tasks = []
            for i in range(self.config.concurrency):
                task = asyncio.create_task(self._worker(worker_id=i + 1, session=session))
                worker_tasks.append(task)

            progress_task = asyncio.create_task(self._progress_reporter())

            test_completed_normally = False
            try:
                if self.config.duration:
                    log.info(f"Test {self.config.duration} saniye boyunca çalışacak...")
                    await asyncio.sleep(self.config.duration)
                    log.info(f"\nBelirlenen test süresi ({self.config.duration}s) doldu.")
                    test_completed_normally = True
                elif self.config.total_requests:
                    log.info(f"Toplam {self.config.total_requests} istek gönderilene kadar çalışılacak...")
                    while self.stats.requests_sent < self.config.total_requests:
                        await asyncio.sleep(0.05)
                        if self.stop_event.is_set(): # Manuel durdurma
                            log.info("\nDurdurma sinyali algılandı (muhtemelen manuel iptal).")
                            break
                    if self.stats.requests_sent >= self.config.total_requests:
                         log.info(f"\nToplam {self.config.total_requests} istek gönderme hedefine ulaşıldı.")
                         test_completed_normally = True
                else:
                     log.error("Kritik Hata: Ne test süresi ne de toplam istek sayısı tanımlanmamış!")
                     self.stop_event.set()

            except asyncio.CancelledError:
                log.info("\nTest ana görevi dışarıdan iptal edildi (muhtemelen Ctrl+C).")
            finally:
                actual_duration = time.monotonic() - start_run_time
                self.stats.actual_test_duration = actual_duration

                if not self.stop_event.is_set():
                    log.info("Normal bitiş veya zaman aşımı. Durdurma sinyali worker'lara gönderiliyor...")
                    self.stop_event.set()

                print("\rGörevlerin tamamlanması bekleniyor..." + " " * 50)
                log.debug("stop_event ayarlandı. Progress reporter ve worker task'larının bitmesi bekleniyor.")

                # İlerleme raporlayıcının durmasını bekle
                try:
                    await asyncio.wait_for(progress_task, timeout=2)
                    log.debug("Progress reporter task başarıyla tamamlandı.")
                except asyncio.TimeoutError:
                    log.warning("Progress reporter task zaman aşımında durduruldu (2s).")
                    progress_task.cancel()
                except asyncio.CancelledError:
                    log.debug("Progress reporter task zaten iptal edilmişti.")

                # Worker görevlerinin durmasını bekle
                log.debug(f"{len(worker_tasks)} worker task'ının iptali isteniyor ve tamamlanması bekleniyor...")
                for task in worker_tasks:
                     if not task.done(): task.cancel()

                results = await asyncio.gather(*worker_tasks, return_exceptions=True)
                log.debug("Tüm worker task'ları 'gather' ile beklendi.")

                cancelled_count = sum(1 for r in results if isinstance(r, asyncio.CancelledError))
                other_errors = [r for r in results if isinstance(r, Exception) and not isinstance(r, asyncio.CancelledError)]
                successful_completions = len(results) - cancelled_count - len(other_errors)
                log.info(f"{successful_completions} worker görevi normal tamamlandı, {cancelled_count} iptal edildi.")
                if other_errors:
                    log.warning(f"Worker görevlerinden {len(other_errors)} tanesi beklenmedik bir hata ile sonuçlandı.")
                    for i, err in enumerate(other_errors): log.debug(f"  Worker Hata Detayı {i+1}: {err}")

                print("\r" + " " * 80 + "\r", end="") # Konsolu temizle
                log.info(f"Testin toplam efektif çalışma süresi: {actual_duration:.2f} saniye.")

        # --- Sonuçları Raporla ---
        summary = self.stats.calculate_summary()
        assertion_results, all_assertions_passed = self._check_assertions(summary)
        self._print_summary(summary, assertion_results)

        if not all_assertions_passed and self.config.assertions:
            log.warning("Test tamamlandı ancak bazı assertion kontrolleri BAŞARISIZ oldu.")


async def main():
    """Scriptin ana giriş noktası. Kullanıcıdan parametreleri alır, TestConfig'i oluşturur ve TestRunner'ı başlatır."""
    print("--- Asenkron HTTP Yük Testi Aracı ---")
    print("UYARI: Bu araç, istekleri doğrudan sizin IP adresinizden gönderir.")
    print("       Yüksek hacimli testler hedef sunucuda veya ağınızda sorunlara yol açabilir.")
    print("       Tam anonimlik veya kaynak IP gizleme için sistem düzeyinde VPN/Tor kullanın.")
    print("-" * 40)

    print("Lütfen test parametrelerini girin (Varsayılan değerler köşeli parantez içinde belirtilmiştir):")

    # 1. Hedef URL veya URL Dosyası
    target_url: Optional[str] = None
    url_file: Optional[str] = None
    while True:
        url_input_mode = get_input("\nTest hedefi: Tek URL mi ('U') yoksa URL listesi dosyası mı ('F')?", default='U').upper()
        if url_input_mode == 'U':
            while True:
                target_url = get_input("Hedef URL (örn: https://example.com)")
                if target_url.startswith(("http://", "https://")):
                    if target_url.startswith("http://"):
                        log.warning("Güvenli olmayan HTTP protokolü kullanılıyor. Mümkünse HTTPS tercih edin.")
                    break
                else:
                    print("Hata: Geçersiz URL formatı. URL 'http://' veya 'https://' ile başlamalıdır.")
            break # Ana URL seçim döngüsünden çık
        elif url_input_mode == 'F':
            while True:
                url_file_input = get_input("URL listesini içeren dosyanın tam yolu")
                if not url_file_input:
                    print("Hata: Dosya yolu boş olamaz.")
                    continue
                normalized_path = os.path.abspath(url_file_input)
                if os.path.isfile(normalized_path) and os.access(normalized_path, os.R_OK):
                       url_file = normalized_path
                       print(f" -> Kullanılacak dosya: {url_file}")
                       break
                else:
                       print(f"Hata: Dosya bulunamadı veya okuma izni yok: {normalized_path}")
            break # Ana URL seçim döngüsünden çık
        else:
            print("Hata: Geçersiz seçim. Lütfen 'U' veya 'F' girin.")

    # 2. HTTP Metodu
    http_method = get_input("\nHTTP Metodu (GET, POST, PUT, DELETE vb.)", default="GET").upper()
    allowed_methods = {"GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "PATCH"}
    if http_method not in allowed_methods:
        log.warning(f"'{http_method}' standart bir HTTP metodu olarak tanınmıyor, ancak yine de denenecek.")

    # 3. Eşzamanlılık
    concurrency = get_positive_integer_input("\nEş zamanlı istek sayısı (worker/kullanıcı sayısı)", default=50)

    # 4. Test Modu (Süre veya İstek Sayısı)
    duration: Optional[int] = None
    total_requests: Optional[int] = None
    while True:
        mode = get_input("\nTest modu: Belirli bir 'S'üre mi yoksa belirli 'I'stek sayısı mı?", default='S').upper()
        if mode == 'S':
            duration = get_positive_integer_input("Test süresi (saniye)", default=10)
            break
        elif mode == 'I':
            total_requests = get_positive_integer_input("Toplam gönderilecek istek sayısı", default=1000)
            break
        else:
            print("Hata: Geçersiz mod. Lütfen 'S' veya 'I' girin.")

    # Rate Limit (Hedef RPS)
    target_rps = get_positive_float_input("\nHedeflenen saniye başına istek (RPS) (0 = limitsiz)", default=0.0)

    # 5. Zaman Aşımı
    timeout_seconds = get_positive_float_input("\nHer bir istek için zaman aşımı süresi (saniye)", default=10.0)

    # YENİ: SSL Doğrulama Ayarı
    print("\n--- SSL/TLS Ayarları ---")
    print("HTTPS bağlantıları için sunucunun SSL/TLS sertifikasının doğrulanıp doğrulanmayacağını seçin.")
    print("Doğrulamayı kapatmak ('H') güvenlik riski oluşturur ve yalnızca test ortamlarında,")
    print("kendi kendine imzalanmış (self-signed) veya geçersiz sertifikalara sahip sunuculara")
    print("karşı test yaparken kullanılmalıdır.")
    verify_ssl_choice = get_yes_no_input("SSL sertifika doğrulamasını etkinleştirmek ister misiniz? (E=Evet, Güvenli / H=Hayır, Güvensiz)", default_yes=True) # Varsayılan olarak güvenli (doğrulama açık)


    # 6. User-Agent (get_user_agent_preference fonksiyonu çağrılır)
    user_agent_preference = get_user_agent_preference() # None, "", veya seçilen/girilen UA döndürür


    # 7. Özel Başlıklar
    custom_headers: Dict[str, str] = {}
    print("\n--- Özel HTTP Başlıkları (Headers) ---")
    print("İsteğe ek özel başlıklar ekleyebilirsiniz (örn: 'Authorization: Bearer token').")
    print("UYARI: 'Cookie', 'Authorization' gibi hassas bilgileri log dosyasında görünür hale getirebilir.")
    if get_yes_no_input("Özel başlık eklemek ister misiniz?", default_yes=False):
        print("Başlıkları 'İsim: Değer' formatında girin (bitirmek için boş satır girin):")
        while True:
            header_line = input(" Header: ").strip()
            if not header_line: break
            try:
                name, value = header_line.split(":", 1)
                name_stripped = name.strip()
                value_stripped = value.strip()
                if not name_stripped:
                    print("Hata: Başlık ismi boş olamaz.")
                    continue
                if name_stripped.lower() == 'user-agent':
                    log.warning("User-Agent başlığı önceki adımda zaten ayarlandı/tercih edildi.")
                    log.warning(f"Burada girdiğiniz değer ('{value_stripped[:30]}...') önceki seçimi geçersiz kılacak.")
                custom_headers[name_stripped] = value_stripped
                print(f"  -> Eklendi: '{name_stripped}': '{value_stripped[:50]}{'...' if len(value_stripped)>50 else ''}'")
            except ValueError:
                 print("Hata: Geçersiz format. 'İsim: Değer' şeklinde girin (örn: Accept: application/json).")
    if not custom_headers:
        print("-> Ek özel başlık eklenmedi.")


    # 8. İstek Gövdesi (Request Body/Data)
    request_data: Optional[Union[str, Dict]] = None
    is_json_data: bool = False
    needs_data_methods = {"POST", "PUT", "PATCH"}
    if http_method in needs_data_methods:
        print(f"\n--- İstek Gövdesi ({http_method}) ---")
        print(f"'{http_method}' metodu genellikle bir istek gövdesi (veri) ile kullanılır.")
        print("UYARI: Gönderilecek veri hassas bilgiler içeriyorsa dikkatli olun (loglanabilir).")
        if get_yes_no_input(f"'{http_method}' isteği için bir gövde (veri) eklemek ister misiniz?", default_yes=False):
            is_json_data = get_yes_no_input("Veri JSON formatında mı?", default_yes=True)
            print("Lütfen gönderilecek veriyi girin (Genellikle tek satır veya kopyala/yapıştır):")
            data_input = get_input(" Veri:")

            if data_input:
                if is_json_data:
                    try:
                        request_data = json.loads(data_input)
                        print(" -> JSON verisi başarıyla ayrıştırıldı.")
                        log.debug(f"Kullanıcıdan alınan JSON verisi (maskelenmiş): {mask_sensitive_data(request_data)}")
                    except json.JSONDecodeError as json_err:
                        print(f"HATA: Girilen veri geçerli bir JSON değil! ({json_err})")
                        if get_yes_no_input("Veriyi düz metin olarak göndermek ister misiniz?", default_yes=False):
                             is_json_data = False
                             request_data = data_input
                             print(" -> Veri düz metin olarak ayarlandı.")
                             log.debug(f"Kullanıcıdan alınan düz metin verisi: {mask_sensitive_data(request_data)}")
                        else:
                             print(" -> Veri eklenmedi.")
                             request_data = None
                else:
                    request_data = data_input
                    print(" -> Düz metin verisi ayarlandı.")
                    log.debug(f"Kullanıcıdan alınan düz metin verisi: {mask_sensitive_data(request_data)}")
            else:
                print(" -> Boş veri girildi, istek gövdesi gönderilmeyecek.")

    if request_data and is_json_data and 'content-type' not in {k.lower() for k in custom_headers}:
        custom_headers['Content-Type'] = 'application/json'
        log.info("JSON verisi gönderileceği için 'Content-Type: application/json' başlığı otomatik eklendi.")

    # 9. Log Dosyası
    log_filename: Optional[str] = None
    print("\n--- Detaylı Loglama Ayarları ---")
    if get_yes_no_input("Tüm istek detaylarını (DEBUG seviyesi) bir dosyaya kaydetmek ister misiniz?", default_yes=False):
        default_log_name = f"http_load_test_{datetime.now():%Y%m%d_%H%M%S}.log"
        log_filename_input = get_input("Log dosyasının adı", default=default_log_name)
        log_filename = log_filename_input if log_filename_input else default_log_name


    # 10. Assertions (Test Sonu Kontrolleri)
    assertions: Dict[str, float] = {}
    print("\n--- Assertion Ayarları (Test Sonu Başarı Kriterleri) ---")
    if get_yes_no_input("Test sonunda otomatik kontrol edilecek başarı kriterleri (assertion) tanımlamak ister misiniz?", default_yes=False):
        print(" Desteklenen Assertion Tipleri:")
        print("   latency: Maksimum kabul edilebilir ortalama yanıt süresi (saniye).")
        print("   failure: Maksimum kabul edilebilir başarısızlık oranı (yüzde).")
        while True:
            assertion_type = get_input(" Assertion tipi girin ('latency', 'failure') veya bitirmek için boş bırakın:").lower().strip()
            if not assertion_type: break

            if assertion_type == 'latency':
                value = get_positive_float_input(" Max Ortalama Yanıt Süresi (saniye) girin", default=1.0)
                assertions['max_avg_latency'] = value
                print(f"  -> Eklendi: Ortalama Yanıt Süresi <= {value:.3f}s")
            elif assertion_type == 'failure':
                value = get_positive_float_input(" Max Başarısızlık Oranı (%) girin (örn: 5.0)", default=5.0)
                if value > 100:
                    print(" Hata: Başarısızlık oranı %100'den büyük olamaz.")
                    continue
                assertions['max_failure_rate'] = value
                print(f"  -> Eklendi: Başarısızlık Oranı <= {value:.1f}%")
            else:
                 print(" Hata: Geçersiz assertion tipi. Lütfen 'latency' veya 'failure' girin ya da boş bırakın.")


    # --- Log Dosyasını Ayarla (Eğer istendiyse) ---
    global file_handler
    if log_filename:
        try:
            file_handler = logging.FileHandler(log_filename, mode='w', encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(name)s:%(funcName)s:%(lineno)d] - %(message)s')
            file_handler.setFormatter(file_formatter)
            log.addHandler(file_handler)
            log.info(f"Detaylı DEBUG logları '{log_filename}' dosyasına yazılacak.")
        except Exception as e:
            log.error(f"Log dosyası ('{log_filename}') oluşturulurken/açılırken hata oluştu: {e}. Loglama sadece konsola yapılacak.")
            file_handler = None

    # --- Test Konfigürasyonunu Oluştur ---
    try:
        config = TestConfig(
            target_url=target_url,
            url_file=url_file,
            http_method=http_method,
            concurrency=concurrency,
            duration=duration,
            total_requests=total_requests,
            timeout_seconds=timeout_seconds,
            verify_ssl=verify_ssl_choice, # SSL tercihini ekle
            user_agent_preference=user_agent_preference,
            custom_headers=custom_headers,
            request_data=request_data,
            is_json_data=is_json_data,
            log_filename=log_filename,
            target_rps=target_rps,
            assertions=assertions
        )
    except Exception as config_err:
         log.exception(f"Test yapılandırması oluşturulurken hata oluştu: {config_err}")
         print(f"\nHATA: Test yapılandırması oluşturulamadı - {config_err}")
         return

    # --- Test Runner'ı Oluştur ve Çalıştır ---
    try:
        print("\n" + "="*40)
        print(" Test Ayarları Tamamlandı. Test Başlatılıyor...")
        print("="*40)
        runner = TestRunner(config)
        await runner.run()
        print("\n" + "="*40)
        print(" Test Tamamlandı.")
        print("="*40)

    except ValueError as ve: # TestRunner __init__
        log.error(f"Test başlatılamadı (Yapılandırma Hatası): {ve}")
        print(f"\nHATA: Test başlatılamadı - {ve}")
    except FileNotFoundError as fnfe: # TestRunner __init__
        log.error(f"Test başlatılamadı (Dosya Hatası): {fnfe}")
        print(f"\nHATA: Test başlatılamadı - {fnfe}")
    except Exception as e:
        log.exception(f"Test sırasında beklenmedik bir ana hata oluştu: {e}")
        print(f"\nKRİTİK HATA: Test sırasında beklenmedik bir sorun oluştu. Detaylar log dosyasında (eğer aktifse) veya konsolda olabilir.")
        print(f" Hata Detayı: {e}")


# --- Script Başlangıç Noktası ---
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("\nKullanıcı tarafından iptal edildi (Ctrl+C algılandı). Program sonlandırılıyor.")
        print("\nTest kullanıcı tarafından iptal edildi.")
    except Exception as top_level_err:
        log.exception(f"Programın en üst seviyesinde kritik bir hata oluştu: {top_level_err}")
        print(f"\nBEKLENMEDİK KRİTİK HATA: Program başlatılamadı veya beklenmedik şekilde sonlandı.", file=sys.stderr)
        print(f" Hata: {top_level_err}", file=sys.stderr)
    finally:
        # Log dosyasını kapatma (önemli)
        if file_handler:
            is_attached = file_handler in log.handlers
            is_stream_open = hasattr(file_handler, 'stream') and file_handler.stream and not file_handler.stream.closed

            if is_attached or is_stream_open:
                log.debug("Program sonlanırken log dosyası kapatılıyor.")
                try:
                    if is_stream_open:
                         file_handler.close() # Önce dosyayı kapat
                    if is_attached:
                         log.removeHandler(file_handler) # Sonra handler'ı kaldır
                except Exception as close_err:
                    print(f"Program sonlanırken log dosyası kapatılırken bir hata oluştu: {close_err}", file=sys.stderr)

        print("\nHTTP Yük Testi Aracı sonlandırıldı.")
