"""
Excel İşleme Modülü
====================
Sınıf listesi Excel dosyalarını okuyup veritabanına aktarır.

Özellikler:
- Dosya adından ders kodunu otomatik çıkarma (YZM332, BLM111 vb.)
- Excel dosyalarını tarama ve yükleme
- Öğrenci ve Ders-Öğrenci ilişkisini yönetme
- Derslik Yakınlık tablosunu doldurma
- Hata yönetimi ve loglama
"""

import os
import re
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# Logging konfigürasyonu
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ExcelProcessor:
    """
    Excel dosyalarını işleyen ana sınıf.
    
    Ders kodlarını tanıması gereken format: YZM332, BLM111, MAT213 vb.
    Excel sütunları beklenen: Öğrenci Numarası, Öğrenci Adı
    """
    
    # Ders kodu regex deseni (3 harf + 3 rakam)
    COURSE_CODE_PATTERN = r'[A-Z]{2,4}\d{3}'
    
    # Olası sütun adları (case-insensitive)
    STUDENT_NUMBER_COLUMNS = ['öğrenci numarası', 'öğrenci no', 'numara', 'student_number', 'number', 'no']
    STUDENT_NAME_COLUMNS = ['öğrenci adı', 'adı soyadı', 'ad', 'student_name', 'name', 'adı']
    
    def __init__(self):
        """ExcelProcessor'ı başlat"""
        self.stats = {
            'files_scanned': 0,
            'files_imported': 0,
            'students_imported': 0,
            'courses_created': 0,
            'errors': 0
        }
    
    def extract_course_code_from_filename(self, filename: str) -> Optional[str]:
        """
        Dosya adından ders kodunu çıkar.
        
        Örnek: "YZM332_Algoritma.xlsx" -> "YZM332"
                "BLM111_VT.xlsx" -> "BLM111"
        
        Args:
            filename: Excel dosyasının adı
            
        Returns:
            Ders kodu veya None
        """
        # Küçük/büyük harf farkını azaltmak için büyük harfe çevir
        name_upper = filename.upper()

        # Dosya adında regex araması yap
        match = re.search(self.COURSE_CODE_PATTERN, name_upper)
        if match:
            course_code = match.group(0)
            logger.info(f"Dosya '{filename}' → Ders kodu: {course_code}")
            return course_code
        
        logger.warning(f"Dosya '{filename}' içinde ders kodu bulunamadı")
        return None
    
    def find_column_index(self, columns: List[str], target_columns: List[str]) -> Optional[int]:
        """
        Verilen hedef sütun adlarından birini bulup index döndür.
        
        Case-insensitive arama yapar ve Türkçe karakterleri normalize eder.
        
        Args:
            columns: DataFrame sütun adları
            target_columns: Aranacak sütun adları listesi
            
        Returns:
            Sütun indeksi veya None
        """
        import unicodedata
        
        def normalize(text):
            """Türkçe karakterleri normalize et"""
            # Boşlukları kaldır, lowercase yap
            text = str(text).strip().lower()
            # Türkçe karakterleri ASCII eşdeğerine dönüştür
            text = unicodedata.normalize('NFKD', text)
            text = text.encode('ascii', 'ignore').decode('ascii')
            return text
        
        # Normalize edilen columns dictionary'si oluştur
        normalized_columns = {}
        for idx, col in enumerate(columns):
            norm_col = normalize(col)
            if norm_col:  # Boş olmayanları ekle
                normalized_columns[norm_col] = idx
        
        # Hedef sütunları normalize et ve ara
        for target in target_columns:
            norm_target = normalize(target)
            if norm_target in normalized_columns:
                logger.debug(f"Sütun '{target}' bulundu (Index: {normalized_columns[norm_target]})")
                return normalized_columns[norm_target]
        
        # Kısmi eşleşme ara (örn: "numara" içinde "num" varsa)
        for target in target_columns:
            norm_target = normalize(target)
            if len(norm_target) > 2:  # En az 3 karakter
                for norm_col, idx in normalized_columns.items():
                    if norm_target in norm_col or norm_col in norm_target:
                        logger.debug(f"Kısmi eşleşme: '{target}' → '{columns[idx]}'")
                        return idx
        
        logger.debug(f"Aranılan sütunlar bulunamadı: {target_columns}")
        logger.debug(f"Mevcut sütunlar: {columns}")
        return None
    
    def validate_excel_format(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """
        Excel dosyasının geçerli format olup olmadığını kontrol et.
        
        Args:
            df: Pandas DataFrame
            
        Returns:
            (is_valid, message) tuple
        """
        if df.empty:
            return False, "Excel dosyası boş"
        
        # Öğrenci numarası sütununu bul
        student_num_idx = self.find_column_index(df.columns.tolist(), self.STUDENT_NUMBER_COLUMNS)
        if student_num_idx is None:
            cols = ", ".join(self.STUDENT_NUMBER_COLUMNS)
            return False, f"Zorunlu sütun bulunamadı: {cols}"
        
        # Öğrenci adı sütununu bul
        student_name_idx = self.find_column_index(df.columns.tolist(), self.STUDENT_NAME_COLUMNS)
        if student_name_idx is None:
            cols = ", ".join(self.STUDENT_NAME_COLUMNS)
            return False, f"Zorunlu sütun bulunamadı: {cols}"
        
        return True, "Format geçerli"
    
    def read_excel_file(self, filepath: str) -> Tuple[Optional[pd.DataFrame], str]:
        """
        Excel dosyasını oku (.xls ve .xlsx destekler).
        
        Args:
            filepath: Dosya yolu
            
        Returns:
            (DataFrame, error_message) tuple
        """
        try:
            # Dosya varlığını kontrol et
            if not os.path.exists(filepath):
                return None, f"Dosya bulunamadı: {filepath}"
            
            # Dosya uzantısını al
            file_ext = os.path.splitext(filepath)[1].lower()
            
            # Engine belirt (xlrd for .xls, openpyxl for .xlsx)
            engine = None
            if file_ext == '.xls':
                engine = 'xlrd'
            elif file_ext == '.xlsx':
                engine = 'openpyxl'
            else:
                return None, f"Desteklenmeyen dosya formatı: {file_ext}"
            
            # Excel dosyasını oku
            # .xls dosyaları header=None ile başla, başlık satırını bul
            df = pd.read_excel(filepath, engine=engine)
            
            # Eğer ilk satırlar başlık gibi görünmüyorsa (NaN sütunları çoksa)
            # header parametresini ayarla
            if df.columns.tolist()[0].startswith('Unnamed') or pd.isna(df.iloc[0]).sum() > len(df.columns) // 2:
                # İlk 10 satırı kontrol et ve başlığı bul
                df_test = pd.read_excel(filepath, engine=engine, header=None)
                for i in range(min(10, len(df_test))):
                    row_values = df_test.iloc[i].dropna()
                    if len(row_values) > 2:  # Potansiyel başlık satırı
                        # Kontrol et - bu satırda "Öğrenci" veya "numara" gibi anahtar kelimeler var mı?
                        row_str = str(df_test.iloc[i].tolist()).lower()
                        if any(keyword in row_str for keyword in ['öğrenci', 'numara', 'no', 'ad', 'name']):
                            # Bu satırı başlık olarak kullan
                            df = pd.read_excel(filepath, engine=engine, header=i)
                            break
            
            logger.info(f"✅ Dosya başarıyla okundu ({engine}): {filepath} ({len(df)} satır)")
            
            # Format doğrulaması yap
            is_valid, message = self.validate_excel_format(df)
            if not is_valid:
                return df, message
            
            return df, ""
            
        except FileNotFoundError:
            msg = f"Dosya bulunamadı: {filepath}"
            logger.error(msg)
            return None, msg
        except Exception as e:
            msg = f"Excel okuma hatası: {str(e)}"
            logger.error(msg)
            return None, msg
    
    def extract_student_data(self, df: pd.DataFrame) -> Tuple[List[Dict], str]:
        """
        DataFrame'den öğrenci verilerini çıkar.
        
        Args:
            df: Pandas DataFrame
            
        Returns:
            (öğrenci_listesi, error_message) tuple
        """
        try:
            # Geçerli format kontrolü
            is_valid, message = self.validate_excel_format(df)
            if not is_valid:
                return [], message
            
            students = []
            
            # Sütun indexlerini bul
            num_idx = self.find_column_index(df.columns.tolist(), self.STUDENT_NUMBER_COLUMNS)
            name_idx = self.find_column_index(df.columns.tolist(), self.STUDENT_NAME_COLUMNS)
            
            # Her satırı işle
            for idx, row in df.iterrows():
                try:
                    student_num = str(row.iloc[num_idx]).strip()
                    student_name = str(row.iloc[name_idx]).strip()
                    
                    # Boş satırları atla
                    if not student_num or student_num.lower() == 'nan':
                        continue
                    
                    students.append({
                        'number': student_num,
                        'name': student_name if student_name.lower() != 'nan' else ''
                    })
                except Exception as e:
                    logger.warning(f"Satır {idx + 1} işlenemedi: {str(e)}")
                    continue
            
            if not students:
                return [], "Hiçbir geçerli öğrenci kaydı bulunamadı"
            
            logger.info(f"{len(students)} öğrenci başarıyla çıkarıldı")
            return students, ""
            
        except Exception as e:
            msg = f"Öğrenci çıkarma hatası: {str(e)}"
            logger.error(msg)
            return [], msg
    
    def scan_excel_folder(self, folder_path: str) -> List[Dict]:
        """
        Belirtilen klasöründeki tüm Excel dosyalarını tara.
        
        Args:
            folder_path: Taranacak klasör yolu
            
        Returns:
            Excel dosyalarının bilgilerini içeren liste
        """
        files_info = []
        
        try:
            folder = Path(folder_path)
            if not folder.exists():
                logger.error(f"Klasör bulunamadı: {folder_path}")
                return []
            
            # .xlsx ve .xls dosyalarını bul
            excel_files = list(folder.glob('*.xlsx')) + list(folder.glob('*.xls'))
            
            logger.info(f"📁 {folder_path} klasöründe {len(excel_files)} Excel dosyası bulundu")
            
            for filepath in excel_files:
                filename = filepath.name
                course_code = self.extract_course_code_from_filename(filename)
                
                # Dosyayı oku ve sayacı güncelle
                df, error = self.read_excel_file(str(filepath))
                
                if df is not None and not error:
                    self.stats['files_scanned'] += 1
                    logger.info(f"✅ Başarılı: {filename} ({len(df)} satır)")
                    
                    files_info.append({
                        'filepath': str(filepath),
                        'filename': filename,
                        'course_code': course_code or 'N/A',
                        'row_count': len(df),
                        'valid': True,
                        'error': ''
                    })
                else:
                    error_msg = error or "Bilinmeyen hata"
                    logger.warning(f"❌ Başarısız: {filename} - {error_msg}")
                    self.stats['errors'] += 1
                    
                    files_info.append({
                        'filepath': str(filepath),
                        'filename': filename,
                        'course_code': course_code or 'N/A',
                        'row_count': 0,
                        'valid': False,
                        'error': error_msg
                    })
            
            logger.info(f"📊 Tarama tamamlandı: {self.stats['files_scanned']} başarılı, {self.stats['errors']} başarısız")
            return files_info
            
        except Exception as e:
            logger.error(f"Klasör tarama hatası: {str(e)}")
            return []
    
    def read_classroom_proximity_excel(self, filepath: str) -> Tuple[List[Dict], str]:
        """
        Derslik Yakınlık Excel dosyasını oku.
        
        Beklenen sütunlar: Ana Derslik, Yakın Derslik, Bitişik (True/False), Mesafe (optional)
        
        Args:
            filepath: DerslikYakınlık.xlsx dosyasının yolu
            
        Returns:
            (ilişkiler_listesi, error_message) tuple
        """
        import unicodedata
        
        def normalize_turkish(text):
            """Türkçe karakterleri normalize et"""
            text = str(text).strip().lower()
            # Türkçe karakterleri değiştir
            replacements = {
                'ı': 'i', 'ğ': 'g', 'ü': 'u', 'ş': 's', 'ö': 'o', 'ç': 'c',
                'İ': 'i', 'Ğ': 'g', 'Ü': 'u', 'Ş': 's', 'Ö': 'o', 'Ç': 'c'
            }
            for tr_char, en_char in replacements.items():
                text = text.replace(tr_char, en_char)
            return text
        
        try:
            # Uzantıya göre engine seç (.xls için xlrd, .xlsx için openpyxl)
            file_ext = os.path.splitext(filepath)[1].lower()
            engine = None
            if file_ext == '.xls':
                engine = 'xlrd'
            elif file_ext == '.xlsx':
                engine = 'openpyxl'
            
            df = pd.read_excel(filepath, engine=engine)
            
            if df.empty:
                return [], "Derslik Yakınlık dosyası boş"
            
            # Debug: Sütun adlarını log'a yaz
            logger.info(f"Excel sütunları: {df.columns.tolist()}")
            
            proximities = []
            
            # Sütun adlarını normalize et (döngü dışında bir kez)
            columns_normalized = {normalize_turkish(col): col for col in df.columns}
            logger.info(f"Normalize edilmiş sütunlar: {list(columns_normalized.keys())}")
            
            # Ana Derslik sütununu bul
            primary_col = None
            for key in ['ana derslik', 'anaderslik', 'ana', 'primary', 'main', 'derslik1', 'derslik 1', 'derslik', 'blok']:
                norm_key = normalize_turkish(key)
                if norm_key in columns_normalized:
                    primary_col = columns_normalized[norm_key]
                    logger.info(f"Ana derslik sütunu bulundu: '{primary_col}'")
                    break
                # Kısmi eşleşme
                for norm_col in columns_normalized.keys():
                    if norm_key in norm_col or norm_col in norm_key:
                        primary_col = columns_normalized[norm_col]
                        logger.info(f"Ana derslik sütunu kısmi eşleşme ile bulundu: '{primary_col}'")
                        break
                if primary_col:
                    break
            
            # Yakın Derslik sütununu bul
            nearby_col = None
            for key in ['yakin derslik', 'yakinderslik', 'yakin', 'nearby', 'close', 'derslik2', 'derslik 2']:
                norm_key = normalize_turkish(key)
                if norm_key in columns_normalized:
                    nearby_col = columns_normalized[norm_key]
                    logger.info(f"Yakın derslik sütunu bulundu: '{nearby_col}'")
                    break
                # Kısmi eşleşme
                for norm_col in columns_normalized.keys():
                    if norm_key in norm_col or norm_col in norm_key:
                        nearby_col = columns_normalized[norm_col]
                        logger.info(f"Yakın derslik sütunu kısmi eşleşme ile bulundu: '{nearby_col}'")
                        break
                if nearby_col:
                    break
            
            if not primary_col or not nearby_col:
                avail_cols = ', '.join(df.columns.tolist())
                return [], f"Zorunlu sütunlar bulunamadı. Mevcut sütunlar: {avail_cols}. Beklenen: 'Ana Derslik' ve 'Yakın Derslik' (veya benzeri)"
            
            # Bitişik sütununu bul
            adjacent_col = None
            for key in ['bitisik', 'adjacent', 'isadjacent', 'yanyana']:
                norm_key = normalize_turkish(key)
                if norm_key in columns_normalized:
                    adjacent_col = columns_normalized[norm_key]
                    break
            
            # Mesafe sütununu bul
            distance_col = None
            for key in ['mesafe', 'distance', 'uzaklik']:
                norm_key = normalize_turkish(key)
                if norm_key in columns_normalized:
                    distance_col = columns_normalized[norm_key]
                    break
            
            # Notlar sütununu bul
            notes_col = None
            for key in ['notlar', 'notes', 'aciklama', 'not']:
                norm_key = normalize_turkish(key)
                if norm_key in columns_normalized:
                    notes_col = columns_normalized[norm_key]
                    break
            
            # BLOK sütunu varsa kontrol et (BLOK varsa ana derslik için kullanılacak)
            blok_col = None
            for key in ['blok', 'block']:
                norm_key = normalize_turkish(key)
                if norm_key in columns_normalized:
                    blok_col = columns_normalized[norm_key]
                    logger.info(f"BLOK sütunu bulundu: '{blok_col}'")
                    break
            
            # Her satırı işle
            for idx, row in df.iterrows():
                try:
                    # BLOK sütunu varsa BLOK + DERSLİK birleştir
                    if blok_col and blok_col in df.columns:
                        blok_val = str(row[blok_col]).strip()
                        derslik_val = str(row[primary_col]).strip()
                        if blok_val.lower() != 'nan' and derslik_val.lower() != 'nan':
                            primary = f"{blok_val}{derslik_val}"
                        else:
                            primary = derslik_val
                    else:
                        primary = str(row[primary_col]).strip()
                    
                    nearby = str(row[nearby_col]).strip()
                    is_adjacent = False
                    distance = None
                    notes = ""
                    
                    if not primary or not nearby or primary.lower() == 'nan' or nearby.lower() == 'nan':
                        continue
                    
                    # Bitişik değerini al
                    if adjacent_col:
                        adj_val = row[adjacent_col]
                        if isinstance(adj_val, str):
                            is_adjacent = adj_val.lower() in ['true', '1', 'evet', 'yes', 'e']
                        elif isinstance(adj_val, bool):
                            is_adjacent = adj_val
                        elif pd.notna(adj_val):
                            try:
                                is_adjacent = bool(int(adj_val))
                            except:
                                pass
                    
                    # Mesafe değerini al
                    if distance_col:
                        try:
                            dist_val = row[distance_col]
                            if pd.notna(dist_val) and str(dist_val).lower() != 'nan':
                                distance = float(dist_val)
                        except:
                            pass
                    
                    # Notları al
                    if notes_col:
                        notes_val = row[notes_col]
                        if pd.notna(notes_val) and str(notes_val).lower() != 'nan':
                            notes = str(notes_val).strip()
                    
                    proximities.append({
                        'primary_classroom': primary,
                        'nearby_classroom': nearby,
                        'is_adjacent': bool(is_adjacent),
                        'distance': distance,
                        'notes': notes
                    })
                    
                except Exception as e:
                    logger.warning(f"Satır {idx + 1} işlenemedi: {str(e)}")
                    continue
            
            if not proximities:
                return [], "Hiçbir geçerli yakınlık kaydı bulunamadı. Lütfen Excel dosyasındaki veri satırlarını kontrol edin."
            
            logger.info(f"{len(proximities)} derslik ilişkisi çıkarıldı")
            return proximities, ""
            
        except Exception as e:
            msg = f"Derslik Yakınlık okuma hatası: {str(e)}"
            logger.error(msg)
            return [], msg
    
    def read_capacity_excel(self, filepath: str) -> Tuple[List[Dict], str]:
        """
        Kapasite Excel dosyasını oku.
        
        Beklenen sütünlar: Derslik (veya Derslik Adı) ve Kapasite
        Alternatif: Ders Kodu, Öğrenci Sayısı
        
        Args:
            filepath: Kapasite Excel dosyasının yolu
            
        Returns:
            (kapasite_listesi, error_message) tuple
        """
        import unicodedata
        
        def normalize_turkish(text):
            """Türkçe karakterleri normalize et"""
            text = str(text).strip().lower()
            replacements = {
                'ı': 'i', 'ğ': 'g', 'ü': 'u', 'ş': 's', 'ö': 'o', 'ç': 'c',
                'İ': 'i', 'Ğ': 'g', 'Ü': 'u', 'Ş': 's', 'Ö': 'o', 'Ç': 'c'
            }
            for tr_char, en_char in replacements.items():
                text = text.replace(tr_char, en_char)
            return text
        
        try:
            file_ext = os.path.splitext(filepath)[1].lower()
            engine = None
            if file_ext == '.xls':
                engine = 'xlrd'
            elif file_ext == '.xlsx':
                engine = 'openpyxl'
            
            df = pd.read_excel(filepath, engine=engine)
            
            if df.empty:
                return [], "Kapasite dosyası boş"
            
            logger.info(f"Kapasite Excel sütünları: {df.columns.tolist()}")
            
            capacities = []
            columns_normalized = {normalize_turkish(col): col for col in df.columns}
            logger.info(f"Normalize edilmiş sütünlar: {list(columns_normalized.keys())}")
            
            # Derslik sütünunu bul
            classroom_col = None
            for key in ['derslik', 'derslik adi', 'classroom', 'sinif', 'sınıf', 'oda']:
                norm_key = normalize_turkish(key)
                if norm_key in columns_normalized:
                    classroom_col = columns_normalized[norm_key]
                    logger.info(f"Derslik sütünu bulundu: '{classroom_col}'")
                    break
                for norm_col in columns_normalized.keys():
                    if norm_key in norm_col:
                        classroom_col = columns_normalized[norm_col]
                        logger.info(f"Derslik sütünu kısmi eşleşme ile bulundu: '{classroom_col}'")
                        break
                if classroom_col:
                    break
            
            # Kapasite sütünunu bul
            capacity_col = None
            for key in ['kapasite', 'capacity', 'kontenjan', 'kisi', 'ogrenci sayisi', 'student count']:
                norm_key = normalize_turkish(key)
                if norm_key in columns_normalized:
                    capacity_col = columns_normalized[norm_key]
                    logger.info(f"Kapasite sütünu bulundu: '{capacity_col}'")
                    break
                for norm_col in columns_normalized.keys():
                    if norm_key in norm_col:
                        capacity_col = columns_normalized[norm_col]
                        logger.info(f"Kapasite sütünu kısmi eşleşme ile bulundu: '{capacity_col}'")
                        break
                if capacity_col:
                    break
            
            # Ders Kodu sütünu (alternatif format)
            course_code_col = None
            for key in ['ders kodu', 'code', 'ders', 'course code']:
                norm_key = normalize_turkish(key)
                if norm_key in columns_normalized:
                    course_code_col = columns_normalized[norm_key]
                    logger.info(f"Ders kodu sütünu bulundu: '{course_code_col}'")
                    break
            
            if not (classroom_col or course_code_col) or not capacity_col:
                avail_cols = ', '.join(df.columns.tolist())
                return [], f"Zorunlu sütünlar bulunamadı. Mevcut: {avail_cols}. Beklenen: (Derslik veya Ders Kodu) + Kapasite"
            
            # Format belirleme: derslik mi, ders mi?
            is_classroom_format = classroom_col is not None
            
            for idx, row in df.iterrows():
                try:
                    if is_classroom_format:
                        name = str(row[classroom_col]).strip()
                        if not name or name.lower() == 'nan':
                            continue
                        
                        capacity = None
                        try:
                            cap_val = row[capacity_col]
                            if pd.notna(cap_val) and str(cap_val).lower() != 'nan':
                                capacity = int(float(cap_val))
                        except:
                            pass
                        
                        if capacity:
                            capacities.append({
                                'type': 'classroom',
                                'name': name,
                                'capacity': capacity
                            })
                    else:
                        # Ders formatı
                        code = str(row[course_code_col]).strip().upper()
                        if not code or code == 'NAN':
                            continue
                        
                        student_count = None
                        try:
                            count_val = row[capacity_col]
                            if pd.notna(count_val) and str(count_val).lower() != 'nan':
                                student_count = int(float(count_val))
                        except:
                            pass
                        
                        if student_count:
                            capacities.append({
                                'type': 'course',
                                'code': code,
                                'student_count': student_count
                            })
                    
                except Exception as e:
                    logger.warning(f"Satır {idx + 1} işlenemedi: {str(e)}")
                    continue
            
            if not capacities:
                return [], "Hiçbir geçerli kapasite kaydı bulunamadı."
            
            logger.info(f"{len(capacities)} kapasite kaydı çıkarıldı")
            return capacities, ""
            
        except Exception as e:
            msg = f"Kapasite okuma hatası: {str(e)}"
            logger.error(msg)
            return [], msg
    
    def get_statistics(self) -> Dict:
        """
        İşleme istatistiklerini döndür.
        
        Returns:
            İstatistik sözlüğü
        """
        return self.stats.copy()
    
    def reset_statistics(self):
        """İstatistikleri sıfırla"""
        self.stats = {
            'files_scanned': 0,
            'files_imported': 0,
            'students_imported': 0,
            'courses_created': 0,
            'errors': 0
        }


# Kolaylık fonksiyonları

def process_single_excel(filepath: str) -> Tuple[Optional[str], List[Dict], str]:
    """
    Tek bir Excel dosyasını işle ve ders kodı ile öğrenci listesini döndür.
    
    Args:
        filepath: Excel dosyasının yolu
        
    Returns:
        (ders_kodu, öğrenci_listesi, hata_mesajı) tuple
    """
    processor = ExcelProcessor()
    
    # Dosya adından ders kodunu çıkar
    filename = Path(filepath).name
    course_code = processor.extract_course_code_from_filename(filename)
    
    if not course_code:
        return None, [], f"Dosya '{filename}' adından ders kodu çıkarılamadı"
    
    # Excel dosyasını oku
    df, error = processor.read_excel_file(filepath)
    if error:
        return course_code, [], error
    
    # Öğrenci verilerini çıkar
    students, error = processor.extract_student_data(df)
    if error:
        return course_code, [], error
    
    return course_code, students, ""


def batch_process_folder(folder_path: str) -> Dict:
    """
    Belirtilen klasördeki tüm Excel dosyalarını toplu işle.
    
    Args:
        folder_path: Taranacak klasör yolu
        
    Returns:
        İşleme sonuçlarını içeren sözlük
    """
    processor = ExcelProcessor()
    files_info = processor.scan_excel_folder(folder_path)
    
    results = {
        'total_files': len(files_info),
        'valid_files': sum(1 for f in files_info if f['valid']),
        'invalid_files': sum(1 for f in files_info if not f['valid']),
        'files': files_info,
        'statistics': processor.get_statistics()
    }
    
    return results


# ==================== DB ENTEGRASYONU ====================

def import_classlists_to_db(folder_path: str, db, Course, Student, Enrollment) -> Dict:
    """
    Verilen klasördeki tüm Excel sınıf listelerini DB'ye aktar.
    """
    processor = ExcelProcessor()
    results = {
        'folder': folder_path,
        'files_total': 0,
        'files_processed': 0,
        'students_created': 0,
        'enrollments_created': 0,
        'courses_created': 0,
        'errors': []
    }

    folder = Path(folder_path)
    if not folder.exists():
        return {**results, 'error': f'Klasör bulunamadı: {folder_path}'}

    excel_files = list(folder.glob('*.xlsx')) + list(folder.glob('*.xls'))
    results['files_total'] = len(excel_files)

    for filepath in excel_files:
        filename = filepath.name
        course_code = processor.extract_course_code_from_filename(filename)
        try:
            df, error = processor.read_excel_file(str(filepath))
            if error:
                results['errors'].append({'file': filename, 'message': error})
                continue

            students, error = processor.extract_student_data(df)
            if error:
                results['errors'].append({'file': filename, 'message': error})
                continue

            course = None
            if course_code:
                course = db.session.query(Course).filter_by(code=course_code).first()
                if not course:
                    course = Course(code=course_code, name=course_code)
                    db.session.add(course)
                    db.session.flush()
                    results['courses_created'] += 1

            for s in students:
                stu = db.session.query(Student).filter_by(student_number=s['number']).first()
                if not stu:
                    stu = Student(student_number=s['number'], name=s.get('name') or '')
                    db.session.add(stu)
                    db.session.flush()
                    results['students_created'] += 1

                if course:
                    exists = db.session.query(Enrollment).filter_by(student_id=stu.id, course_id=course.id).first()
                    if not exists:
                        db.session.add(Enrollment(student_id=stu.id, course_id=course.id))
                        results['enrollments_created'] += 1

            if course:
                course.student_count = db.session.query(Enrollment).filter_by(course_id=course.id).count()

            db.session.commit()
            results['files_processed'] += 1

        except Exception as e:
            db.session.rollback()
            results['errors'].append({'file': filename, 'message': str(e)})

    return results


def import_proximity_to_db(filepath: str, db, Classroom, ClassroomProximity) -> Dict:
    """
    Derslik Yakınlık Excel'ini okuyup ClassroomProximity tablosuna aktar.
    """
    processor = ExcelProcessor()
    proximities, error = processor.read_classroom_proximity_excel(filepath)
    if error:
        return {'status': 'error', 'message': error}

    created = 0
    updated = 0
    for p in proximities:
        try:
            primary = db.session.query(Classroom).filter_by(name=p['primary_classroom']).first()
            if not primary:
                primary = Classroom(name=p['primary_classroom'], capacity=30, is_available=True)
                db.session.add(primary)
                db.session.flush()

            nearby = db.session.query(Classroom).filter_by(name=p['nearby_classroom']).first()
            if not nearby:
                nearby = Classroom(name=p['nearby_classroom'], capacity=30, is_available=True)
                db.session.add(nearby)
                db.session.flush()

            rel = db.session.query(ClassroomProximity).filter_by(
                primary_classroom_id=primary.id,
                nearby_classroom_id=nearby.id
            ).first()

            if not rel:
                rel = ClassroomProximity(
                    primary_classroom_id=primary.id,
                    nearby_classroom_id=nearby.id,
                    is_adjacent=bool(p.get('is_adjacent')),
                    distance=p.get('distance'),
                    notes=p.get('notes')
                )
                db.session.add(rel)
                created += 1
            else:
                rel.is_adjacent = bool(p.get('is_adjacent'))
                rel.distance = p.get('distance')
                rel.notes = p.get('notes')
                updated += 1

        except Exception as e:
            db.session.rollback()
            return {'status': 'error', 'message': str(e)}

    db.session.commit()
    return {'status': 'success', 'created': created, 'updated': updated, 'total': created + updated}


def import_capacity_to_db(filepath: str, db, Classroom, Course) -> Dict:
    """
    Kapasite Excel'ini okuyup Classroom veya Course tablolarını güncelle.
    """
    processor = ExcelProcessor()
    capacities, error = processor.read_capacity_excel(filepath)
    if error:
        return {'status': 'error', 'message': error}

    updated_classrooms = 0
    updated_courses = 0
    created_classrooms = 0
    created_courses = 0
    errors = []

    for cap in capacities:
        try:
            if cap['type'] == 'classroom':
                classroom = db.session.query(Classroom).filter_by(name=cap['name']).first()
                if classroom:
                    classroom.capacity = cap['capacity']
                    updated_classrooms += 1
                else:
                    classroom = Classroom(
                        name=cap['name'],
                        capacity=cap['capacity'],
                        is_available=True
                    )
                    db.session.add(classroom)
                    db.session.flush()
                    created_classrooms += 1
            
            elif cap['type'] == 'course':
                course = db.session.query(Course).filter_by(code=cap['code']).first()
                if course:
                    course.student_count = cap['student_count']
                    updated_courses += 1
                else:
                    course = Course(
                        code=cap['code'],
                        name=cap['code'],
                        student_count=cap['student_count'],
                        has_exam=True
                    )
                    db.session.add(course)
                    db.session.flush()
                    created_courses += 1

        except Exception as e:
            errors.append({'item': cap, 'message': str(e)})

    if errors:
        db.session.rollback()
        return {
            'status': 'partial',
            'message': f'{len(errors)} kayıt işlenemedi',
            'errors': errors,
            'updated_classrooms': updated_classrooms,
            'updated_courses': updated_courses,
            'created_classrooms': created_classrooms,
            'created_courses': created_courses
        }

    db.session.commit()
    return {
        'status': 'success',
        'updated_classrooms': updated_classrooms,
        'updated_courses': updated_courses,
        'created_classrooms': created_classrooms,
        'created_courses': created_courses,
        'total': updated_classrooms + updated_courses + created_classrooms + created_courses
    }


# ==================== AKADEMIK KADRO EXCEL IMPORT ====================

def import_teachers_from_excel(filepath: str, db, force_dept_id: int = None) -> Dict:
    """
    akademik_kadro.xlsx dosyasından öğretim üyelerini ve fakülteleri veritabanına aktar.
    
    Excel sütunları:
    - Unvan (Prof. Dr., Dr. Öğr. Üyesi, vb.)
    - Ad Soyad
    - Fakülte / Birim / Görev
    
    Args:
        filepath: Excel dosyasının yolu
        db: SQLAlchemy db nesnesi
        force_dept_id: Bölüm yöneticisiyse, yüklenen öğretim üyelerini bu bölüme ata
        
    Returns:
        İthalatın sonuç bilgisi
    """
    try:
        # Excel dosyasını oku
        df = pd.read_excel(filepath)
        
        # Sütun adlarını kontrol et
        expected_cols = ['Unvan', 'Ad Soyad', 'Fakülte / Birim / Görev']
        if list(df.columns) != expected_cols:
            return {
                'status': 'error',
                'message': f'Excel sütun adları yanlış. Beklenen: {expected_cols}, Mevcut: {list(df.columns)}'
            }
        
        # Import models (burada Teacher, Faculty, Department kullanacağız)
        from app import Teacher, Faculty, Department
        
        created_teachers = 0
        updated_teachers = 0
        created_faculties = 0
        created_departments = 0
        errors = []
        
        # Her satır için işle
        for idx, row in df.iterrows():
            try:
                title = str(row['Unvan']).strip() if pd.notna(row['Unvan']) else ''
                name = str(row['Ad Soyad']).strip() if pd.notna(row['Ad Soyad']) else ''
                faculty_str = str(row['Fakülte / Birim / Görev']).strip() if pd.notna(row['Fakülte / Birim / Görev']) else ''
                
                # Ad boşsa atla
                if not name or name.lower() in ['akademik kadro', 'ad soyad']:
                    continue
                
                # Fakülteyi parse et (örn: "Diş Hekimliği Fakültesi" → Fakülte oluştur)
                # Eğer "Fakültesi" veya "Bölümü" içeriyorsa fakülte olarak al
                faculty_obj = None
                if 'Fakültesi' in faculty_str:
                    fac_name = faculty_str.split('Fakültesi')[0].strip() + ' Fakültesi'
                    faculty_obj = db.session.query(Faculty).filter_by(name=fac_name).first()
                    if not faculty_obj:
                        faculty_obj = Faculty(name=fac_name)
                        db.session.add(faculty_obj)
                        db.session.flush()
                        created_faculties += 1
                
                # Mevcut öğretim üyesini kontrol et
                existing_teacher = db.session.query(Teacher).filter_by(name=name).first()
                
                if existing_teacher:
                    # Güncellemeleri yap (başlık veya fakülte bilgisi varsa)
                    if title and not existing_teacher.title:
                        existing_teacher.title = title
                    if faculty_obj and not existing_teacher.department_id:
                        # Faculty'nin altında bir department oluştur veya default department'i kullan
                        dept = db.session.query(Department).filter_by(faculty_id=faculty_obj.id).first()
                        if not dept:
                            dept = Department(name=faculty_obj.name, faculty_id=faculty_obj.id)
                            db.session.add(dept)
                            db.session.flush()
                            created_departments += 1
                        existing_teacher.department_id = dept.id
                    elif force_dept_id and not existing_teacher.department_id:
                        # Bölüm yöneticisi tarafından yükleniyorsa kendi bölümüne ata
                        existing_teacher.department_id = force_dept_id
                    updated_teachers += 1
                else:
                    # Yeni öğretim üyesi oluştur
                    new_teacher = Teacher(
                        name=name,
                        title=title,
                        available_days='Mon,Tue,Wed,Thu,Fri'
                    )
                    
                    # Department bağlantısını yap
                    if force_dept_id:
                        # Bölüm yöneticisi tarafından yükleniyorsa kendi bölümüne ata
                        new_teacher.department_id = force_dept_id
                    elif faculty_obj:
                        dept = db.session.query(Department).filter_by(faculty_id=faculty_obj.id).first()
                        if not dept:
                            dept = Department(name=faculty_obj.name, faculty_id=faculty_obj.id)
                            db.session.add(dept)
                            db.session.flush()
                            created_departments += 1
                        new_teacher.department_id = dept.id
                    
                    db.session.add(new_teacher)
                    created_teachers += 1
                    
            except Exception as e:
                errors.append({
                    'row': idx + 2,  # Excel satır numarası (başlık +1)
                    'name': row.get('Ad Soyad', 'Bilinmiyor'),
                    'error': str(e)
                })
        
        db.session.commit()
        
        return {
            'status': 'success',
            'message': f'{created_teachers} yeni hoca eklendi, {updated_teachers} hoca güncellendi',
            'created_teachers': created_teachers,
            'updated_teachers': updated_teachers,
            'created_faculties': created_faculties,
            'created_departments': created_departments,
            'total': created_teachers + updated_teachers,
            'errors': errors if errors else None
        }
        
    except Exception as e:
        logger.error(f"Akademik kadro import hatası: {str(e)}", exc_info=True)
        return {
            'status': 'error',
            'message': f'Akademik kadro import hatası: {str(e)}'
        }
