"""
KOSTÜ Akademik Kadro Scraper (Tek Dosya)

Amaç:
- https://kocaelisaglik.edu.tr/akademik-kadro/ sayfasından
  unvan + ad soyad + fakülte/birim bilgilerini çekmek ve Excel'e yazmak.

Talimatlara göre sıfırdan yazılmış, tam çalışan script.
"""

# 1) Gereken kütüphaneler
import requests
from bs4 import BeautifulSoup
import pandas as pd

# lxml ve openpyxl import edilmez fakat parser/engine olarak kullanılır
# (BeautifulSoup için lxml, pandas.ExcelWriter için openpyxl otomatik kullanılır)

from typing import List, Dict


# Yardımcı: unvan anahtarları (doğrulama için)
TITLE_KEYWORDS = {
    "Prof. Dr.",
    "Doç. Dr.",
    "Dr. Öğr. Üyesi",
    "Öğr. Gör.",
    "Arş. Gör.",
}


# 2) Ana fonksiyon
def fetch_akademik_kadro() -> List[Dict[str, str]]:
    """
    Akademik kadro sayfasını indirir ve h4→h4→h5 üçlü bloklarını parse eder.

    Dönüş: [{"Unvan": ..., "Ad Soyad": ..., "Fakülte / Birim / Görev": ...}, ...]
    """

    url = "https://kocaelisaglik.edu.tr/akademik-kadro/"

    # Sayfayı indir (timeout ve raise_for_status zorunlu)
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    # UTF-8 ile yorumla
    resp.encoding = "utf-8"

    # BeautifulSoup ile lxml parser kullan
    soup = BeautifulSoup(resp.text, "lxml")

    # Önce div.entry-content içinde ara, yoksa tüm sayfada
    content = soup.select_one("div.entry-content") or soup

    # 3) Parse mantığı: h4 (unvan) → h4 (ad) → h5 (fakülte)
    elements = content.find_all(["h4", "h5"])  # sıralı liste

    records: List[Dict[str, str]] = []

    i = 0
    while i + 2 < len(elements):
        e1, e2, e3 = elements[i], elements[i + 1], elements[i + 2]

        # Üçlü blok kontrolü: h4 → h4 → h5
        if e1.name == "h4" and e2.name == "h4" and e3.name == "h5":
            title = e1.get_text(strip=True)
            name = e2.get_text(strip=True)
            faculty = e3.get_text(strip=True)

            # Basit filtreler
            if not name:
                i += 1
                continue

            # Sayfa başlıklarını atla
            if name.strip().lower() == "akademik kadro":
                i += 1
                continue

            # Opsiyonel mantıksal doğrulama: title gerçek bir unvan mı?
            # Talimata ek kontrol şartı yok ama kalite için faydalı
            if title not in TITLE_KEYWORDS:
                # Unvan listesinde değilse yine de kaydı ekleyelim; bazı pozisyonlar unvan gibi olabilir
                pass

            records.append({
                "Unvan": title,
                "Ad Soyad": name,
                "Fakülte / Birim / Görev": faculty,
            })

            # Üçlü blok işlendi, sonraki elemandan devam
            i += 3
            continue

        # Üçlü desen yoksa bir adım ilerle
        i += 1

    return records


def _to_dataframe(data: List[Dict[str, str]]) -> pd.DataFrame:
    """Veriyi DataFrame'e dönüştürür ve temizler."""
    # 4) Veri temizliği: sütunlar tam olarak şu isimlerle olsun
    df = pd.DataFrame(data, columns=[
        "Unvan",
        "Ad Soyad",
        "Fakülte / Birim / Görev",
    ])

    # Aynı kişi aynı fakültede tekrar çıkarsa benzersizleştir
    df = df.drop_duplicates(subset=["Ad Soyad", "Fakülte / Birim / Görev"]).reset_index(drop=True)
    return df


def _save_excel(df: pd.DataFrame, filename: str = "akademik_kadro.xlsx") -> None:
    """5) Excel çıktısı: index=False ve bilgi mesajı."""
    # openpyxl engine ile yazılır; paket kurulu olmalı
    df.to_excel(filename, index=False)
    print(f"Toplam {len(df)} satır yazıldı → {filename}")


# 6) main bloğu
if __name__ == "__main__":
    # Veriyi çek
    data = fetch_akademik_kadro()

    # İlk 5 kaydı göster
    print("Örnek ilk 5 kayıt:")
    for row in data[:5]:
        print(row)

    # DataFrame'e çevir
    df = _to_dataframe(data)

    # Excel'e kaydet
    _save_excel(df, "akademik_kadro.xlsx")

"""
KOSTÜ Akademik Kadro Web Scraper
Kocaeli Sağlık ve Teknoloji Üniversitesi
Akademik Kadro sayfasından öğretim üyesi bilgilerini çeker.
"""

import requests
from bs4 import BeautifulSoup
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class KostuScraper:
    """KOSTÜ akademik kadro scraper'ı"""
    
    BASE_URL = "https://kocaelisaglik.edu.tr/akademik-kadro/"
    
    TITLE_KEYWORDS = {
        'Prof. Dr.': 'Prof. Dr.',
        'Doç. Dr.': 'Doç. Dr.',
        'Dr. Öğr. Üyesi': 'Dr. Öğr. Üyesi',
        'Öğr. Gör.': 'Öğr. Gör.',
        'Arş. Gör.': 'Arş. Gör.',
    }
    
    def __init__(self, timeout: int = 30):
        """
        Scraper'ı başlat
        
        Args:
            timeout: İstek zaman sınırı (saniye)
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def scrape(self) -> tuple[List[Dict], Optional[str]]:
        """
        KOSTÜ akademik kadro sayfasından öğretim üyelerini scrape et
        
        Returns:
            (öğretim_üyeleri_listesi, hata_mesajı) tuple
        """
        try:
            logger.info(f"KOSTÜ akademik kadro sayfasından veriler çekiliyor: {self.BASE_URL}")
            
            response = self.session.get(self.BASE_URL, timeout=self.timeout)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.content, 'html.parser')
            teachers = self._extract_teachers(soup)
            
            logger.info(f"Başarıyla {len(teachers)} öğretim üyesi çekildi")
            return teachers, None
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Web sayfası yüklenirken hata: {str(e)}"
            logger.error(error_msg)
            return [], error_msg
        except Exception as e:
            error_msg = f"Scraping işleminde hata: {str(e)}"
            logger.error(error_msg)
            return [], error_msg
    
    def _extract_teachers(self, soup: BeautifulSoup) -> List[Dict]:
        """
        BeautifulSoup nesnesi içinden öğretim üyelerini çıkart
        
        HTML Yapısı:
        H4: Unvan (Prof. Dr., Dr. Öğr. Üyesi, vb.)
        H4: Ad Soyad
        H5: Fakülte/Pozisyon
        
        Args:
            soup: BeautifulSoup nesnesi
            
        Returns:
            Öğretim üyeleri listesi
        """
        teachers = []
        h4_elements = soup.find_all('h4')
        processed_teachers = set()
        
        # H4'leri çift olarak işle (ünvan + ad)
        i = 0
        while i < len(h4_elements) - 1:
            title_text = h4_elements[i].get_text(strip=True)
            name_text = h4_elements[i + 1].get_text(strip=True)
            
            # Eğer başı bir ünvan ise
            if title_text in self.TITLE_KEYWORDS:
                # İkinci kısım (sonraki H4) ünvan değil ve yeterli uzunlukta ise
                if name_text not in self.TITLE_KEYWORDS and len(name_text) >= 3:
                    # Duplicate check
                    if name_text not in processed_teachers:
                        # Sonraki H5'i bul
                        next_h5 = h4_elements[i + 1].find_next('h5')
                        faculty = next_h5.get_text(strip=True) if next_h5 else 'Belirtilmemiş'
                        
                        teacher = {
                            'title': title_text,
                            'name': name_text,
                            'faculty': faculty,
                        }
                        
                        teachers.append(teacher)
                        processed_teachers.add(name_text)
                        logger.debug(f"Çekilen: {name_text} ({title_text}) - {faculty}")
                        
                        # İki H4'ü atla
                        i += 2
                        continue
            
            i += 1
        
        return teachers
    
    def get_faculties_from_page(self, soup: BeautifulSoup) -> List[str]:
        """
        Sayfadan fakülte listesini çıkart
        
        Args:
            soup: BeautifulSoup nesnesi
            
        Returns:
            Fakülte adları listesi
        """
        faculties = set()
        h5_elements = soup.find_all('h5')
        
        for h5 in h5_elements:
            text = h5.get_text(strip=True)
            if 'Fakültesi' in text or 'Bölümü' in text or 'Yüksekokulu' in text:
                faculties.add(text)
        
        return list(faculties)


def scrape_kostu_teachers() -> tuple[List[Dict], Optional[str]]:
    """
    KOSTÜ akademik kadro sayfasından öğretim üyelerini scrape et (convenience function)
    
    Returns:
        (öğretim_üyeleri_listesi, hata_mesajı) tuple
    """
    scraper = KostuScraper()
    return scraper.scrape()
