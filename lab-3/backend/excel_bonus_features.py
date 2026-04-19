"""
Excel Yükleme - Opsiyonel Özellikler
=====================================
Dosya hash kontrolü ve değişiklik farkı tespit etme.

Özellikler:
- Aynı dosya kontrolü (hash)
- Değişiklik farkı tespit etme
- Re-import modu
"""

import hashlib
import json
from datetime import datetime
from typing import Dict, Optional, Tuple


class FileHashManager:
    """
    Dosya hash'lerini yöneterek çift yüklemeyi ve değişiklikleri tespit eder.
    """
    
    def __init__(self, storage_file: str = 'file_hashes.json'):
        """
        Manager'ı başlat.
        
        Args:
            storage_file: Hash'lerin saklanacağı JSON dosyası
        """
        self.storage_file = storage_file
        self.hashes = self._load_hashes()
    
    def _load_hashes(self) -> Dict:
        """Hash dosyasını yükle"""
        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except Exception as e:
            print(f"Hash dosyası yüklenirken hata: {e}")
            return {}
    
    def _save_hashes(self):
        """Hash'leri dosyaya kaydet"""
        try:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self.hashes, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Hash dosyası kaydedilirken hata: {e}")
    
    @staticmethod
    def calculate_hash(filepath: str) -> str:
        """
        Dosyasının SHA256 hash'ini hesapla.
        
        Args:
            filepath: Dosya yolu
            
        Returns:
            Hash string'i
        """
        sha256_hash = hashlib.sha256()
        
        with open(filepath, 'rb') as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        return sha256_hash.hexdigest()
    
    def is_file_imported(self, filename: str) -> bool:
        """
        Dosya daha önce yüklendi mi?
        
        Args:
            filename: Dosya adı
            
        Returns:
            True eğer yüklendiyse
        """
        return filename in self.hashes
    
    def has_file_changed(self, filepath: str) -> Tuple[bool, Optional[str]]:
        """
        Dosya değişti mi kontrol et.
        
        Args:
            filepath: Dosya yolu
            
        Returns:
            (değişti_mi, eski_hash)
        """
        filename = filepath.split('\\')[-1] if '\\' in filepath else filepath.split('/')[-1]
        current_hash = self.calculate_hash(filepath)
        
        if filename not in self.hashes:
            return False, None  # Dosya yüklenmedi
        
        old_hash = self.hashes[filename]['hash']
        return current_hash != old_hash, old_hash
    
    def record_import(self, filepath: str, course_code: str, student_count: int):
        """
        Dosya yüklemesini kaydını tut.
        
        Args:
            filepath: Dosya yolu
            course_code: Ders kodu
            student_count: Yüklenen öğrenci sayısı
        """
        filename = filepath.split('\\')[-1] if '\\' in filepath else filepath.split('/')[-1]
        file_hash = self.calculate_hash(filepath)
        
        self.hashes[filename] = {
            'hash': file_hash,
            'course_code': course_code,
            'student_count': student_count,
            'import_date': datetime.now().isoformat(),
            'import_count': self.hashes.get(filename, {}).get('import_count', 0) + 1
        }
        
        self._save_hashes()
    
    def get_file_history(self, filename: str) -> Optional[Dict]:
        """
        Dosyanın yükleme geçmişini getir.
        
        Args:
            filename: Dosya adı
            
        Returns:
            Geçmiş bilgileri veya None
        """
        return self.hashes.get(filename)
    
    def get_all_history(self) -> Dict:
        """Tüm yükleme geçmişini getir"""
        return self.hashes.copy()
    
    def clear_history(self):
        """Tüm hash'leri temizle (yeniden başlama)"""
        self.hashes = {}
        self._save_hashes()


class ChangeDetector:
    """
    İki Excel dosyası arasındaki değişiklikleri tespit eder.
    """
    
    @staticmethod
    def compare_student_lists(old_students: list, new_students: list) -> Dict:
        """
        İki öğrenci listesi arasındaki farkları tespit et.
        
        Args:
            old_students: Eski öğrenci listesi
            new_students: Yeni öğrenci listesi
            
        Returns:
            {
                'added': [...],      # Yeni eklenen öğrenciler
                'removed': [...],    # Silinen öğrenciler
                'unchanged': [...],  # Değişmeyenler
                'total_changes': N
            }
        """
        old_set = {s['number']: s for s in old_students}
        new_set = {s['number']: s for s in new_students}
        
        added = [new_set[num] for num in new_set if num not in old_set]
        removed = [old_set[num] for num in old_set if num not in new_set]
        unchanged = [s for num, s in new_set.items() if num in old_set and s.get('name') == old_set[num].get('name')]
        
        return {
            'added': added,
            'removed': removed,
            'unchanged': unchanged,
            'total_changes': len(added) + len(removed),
            'added_count': len(added),
            'removed_count': len(removed),
            'unchanged_count': len(unchanged)
        }
    
    @staticmethod
    def generate_change_report(comparison: Dict) -> str:
        """
        Değişiklik raporunu oluştur.
        
        Args:
            comparison: Karşılaştırma sonuçları
            
        Returns:
            Okunaklı rapor string'i
        """
        report = "EXCEL DOSYASI DEĞİŞİKLİK RAPORU\n"
        report += "=" * 50 + "\n\n"
        
        report += f"Toplam Değişiklik: {comparison['total_changes']}\n"
        report += f"  ✓ Yeni Eklenen: {comparison['added_count']}\n"
        report += f"  ✗ Silinen: {comparison['removed_count']}\n"
        report += f"  = Değişmeyen: {comparison['unchanged_count']}\n\n"
        
        if comparison['added']:
            report += "YENİ EKLENEN ÖĞRENCİLER:\n"
            report += "-" * 50 + "\n"
            for student in comparison['added'][:10]:  # İlk 10'u göster
                report += f"  + {student['number']}: {student['name']}\n"
            if len(comparison['added']) > 10:
                report += f"  ... ve {len(comparison['added']) - 10} daha\n"
            report += "\n"
        
        if comparison['removed']:
            report += "SİLİNEN ÖĞRENCİLER:\n"
            report += "-" * 50 + "\n"
            for student in comparison['removed'][:10]:  # İlk 10'u göster
                report += f"  - {student['number']}: {student['name']}\n"
            if len(comparison['removed']) > 10:
                report += f"  ... ve {len(comparison['removed']) - 10} daha\n"
            report += "\n"
        
        return report


class ReimportManager:
    """
    Önceki yüklemelerden sonra yeniden yükleme yönetimi.
    """
    
    def __init__(self, db):
        """
        Manager'ı başlat.
        
        Args:
            db: SQLAlchemy db nesnesi
        """
        self.db = db
        self.hash_manager = FileHashManager()
        self.change_detector = ChangeDetector()
    
    def can_reimport(self, filename: str) -> Tuple[bool, str]:
        """
        Dosya yeniden yüklenebilir mi kontrol et.
        
        Args:
            filename: Dosya adı
            
        Returns:
            (yeniden_yüklenebilir_mi, mesaj)
        """
        if not self.hash_manager.is_file_imported(filename):
            return True, "Dosya daha önce yüklenmedi, ilk kez yüklenecek"
        
        history = self.hash_manager.get_file_history(filename)
        return True, f"Dosya {history['import_count']} kez yüklendi"
    
    def handle_reimport(self, filepath: str, course_code: str, 
                       new_students: list, old_students: list) -> Dict:
        """
        Yeniden yükleme işlemini yönet.
        
        Args:
            filepath: Dosya yolu
            course_code: Ders kodu
            new_students: Yeni öğrenci listesi
            old_students: Eski öğrenci listesi
            
        Returns:
            {
                'action': 'add_new'|'replace'|'update',
                'comparison': {...},
                'report': '...'
            }
        """
        comparison = self.change_detector.compare_student_lists(old_students, new_students)
        report = self.change_detector.generate_change_report(comparison)
        
        # Karar ver: ne yapmalı?
        if comparison['total_changes'] == 0:
            action = 'no_change'
        elif comparison['removed_count'] > len(old_students) * 0.5:
            # Eğer %50'den fazlası silindiyse, uyarı ver
            action = 'verify_before_update'
        else:
            action = 'update'
        
        return {
            'action': action,
            'comparison': comparison,
            'report': report
        }


# Kullanım Örneği Fonksiyonları

def check_file_before_import(filepath: str) -> Dict:
    """
    Dosyayı yüklemeden önce kontrol et.
    
    Args:
        filepath: Dosya yolu
        
    Returns:
        Kontrol sonuçları
    """
    manager = FileHashManager()
    filename = filepath.split('\\')[-1] if '\\' in filepath else filepath.split('/')[-1]
    
    is_imported = manager.is_file_imported(filename)
    changed, old_hash = manager.has_file_changed(filepath)
    
    return {
        'filename': filename,
        'is_imported_before': is_imported,
        'has_changed': changed,
        'history': manager.get_file_history(filename)
    }


def log_import_hash(filepath: str, course_code: str, student_count: int):
    """
    Dosya yüklemesinin hash'ini kaydet.
    
    Args:
        filepath: Dosya yolu
        course_code: Ders kodu
        student_count: Öğrenci sayısı
    """
    manager = FileHashManager()
    manager.record_import(filepath, course_code, student_count)


def get_import_history() -> Dict:
    """Tüm yükleme geçmişini getir"""
    manager = FileHashManager()
    return manager.get_all_history()
