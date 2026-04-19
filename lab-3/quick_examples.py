"""
Excel Yükleme Sistemi - Hızlı Başlangıç Örnekleri
===================================================

Bu dosya Excel işleme sisteminin pratik kullanım örneklerini içerir.
"""

# =============================================================================
# ÖRNEK 1: Tek bir Excel dosyasını yükleme (Python)
# =============================================================================

def example_1_single_file_upload():
    """
    Basit Excel yükleme örneği.
    
    Kullanım:
        python quick_examples.py
    """
    import requests
    
    API_URL = "http://localhost:5000/api"
    
    # Dosyayı aç ve yükle
    with open("YZM332.xlsx", "rb") as f:
        files = {"file": f}
        response = requests.post(
            f"{API_URL}/excel/upload",
            files=files
        )
    
    result = response.json()
    
    print("\n" + "="*60)
    print("SONUÇ: Excel Yükleme")
    print("="*60)
    print(f"Durum: {result['status']}")
    
    if result['status'] == 'success':
        print(f"✅ Ders: {result['course_name']}")
        print(f"📊 Yüklenen Öğrenci: {result['students_imported']}")
        print(f"  ├─ Yeni: {result['new_students']}")
        print(f"  └─ Mevcut: {result['existing_students']}")
    else:
        print(f"❌ Hata: {result['message']}")
    print("="*60 + "\n")


# =============================================================================
# ÖRNEK 2: Klasördeki tüm Excel dosyalarını tarama
# =============================================================================

def example_2_scan_folder():
    """
    Klasördeki Excel dosyalarını tara ve bilgi al.
    
    Kullanım:
        folder_path = "excel_listeleri"
        example_2_scan_folder()
    """
    import requests
    
    API_URL = "http://localhost:5000/api"
    folder_path = "excel_listeleri"  # Klasör yolunu ayarlayın
    
    response = requests.post(
        f"{API_URL}/excel/scan-folder",
        json={"folder_path": folder_path}
    )
    
    result = response.json()
    
    print("\n" + "="*60)
    print("KLASÖR TARAMA SONUÇLARI")
    print("="*60)
    print(f"Taramada bulundu: {result['total_files']} dosya")
    print(f"  ✅ Geçerli: {result['valid_files']}")
    print(f"  ❌ Geçersiz: {result['invalid_files']}")
    print("\nDosyalar:")
    print("-" * 60)
    
    for file in result['files']:
        status_symbol = "✅" if file['valid'] else "❌"
        print(f"{status_symbol} {file['filename']}")
        print(f"   Ders Kodu: {file['course_code'] or 'Bulunamadı'}")
        print(f"   Satır Sayısı: {file['row_count']}")
        if file['error']:
            print(f"   Hata: {file['error']}")
    
    print("="*60 + "\n")


# =============================================================================
# ÖRNEK 3: Derslik Yakınlık dosyası yükleme
# =============================================================================

def example_3_upload_classroom_proximity():
    """
    Derslik Yakınlık Excel dosyasını yükle.
    """
    import requests
    
    API_URL = "http://localhost:5000/api"
    
    with open("DerslikYakınlık.xlsx", "rb") as f:
        files = {"file": f}
        response = requests.post(
            f"{API_URL}/excel/import-classroom-proximity",
            files=files
        )
    
    result = response.json()
    
    print("\n" + "="*60)
    print("DERSLIK YAKINLIK YÜKLEME")
    print("="*60)
    
    if result['status'] == 'success':
        print(f"✅ {result['proximities_imported']} ilişki yüklendi")
    else:
        print(f"❌ Hata: {result['message']}")
    
    print("="*60 + "\n")


# =============================================================================
# ÖRNEK 4: Yükleme geçmişini görüntüleme
# =============================================================================

def example_4_view_import_history():
    """
    Excel yükleme geçmişini incele.
    """
    import requests
    from datetime import datetime
    
    API_URL = "http://localhost:5000/api"
    
    # Son 10 kaydı getir
    response = requests.get(f"{API_URL}/excel/logs?limit=10")
    logs = response.json()
    
    print("\n" + "="*60)
    print("YÜKLEME GEÇMİŞİ (Son 10 kayıt)")
    print("="*60)
    
    for log in logs:
        date = datetime.fromisoformat(log['import_date']).strftime("%d.%m.%Y %H:%M")
        status_symbol = "✅" if log['status'] == 'success' else "❌"
        
        print(f"\n{status_symbol} {log['filename']}")
        print(f"   Tarih: {date}")
        print(f"   Durum: {log['status'].upper()}")
        print(f"   Kaydedilen: {log['records_imported']}")
        if log['error_message']:
            print(f"   Hata: {log['error_message']}")
    
    print("\n" + "="*60 + "\n")


# =============================================================================
# ÖRNEK 5: Dosya değişiklikleri kontrol etme (BONUS)
# =============================================================================

def example_5_check_file_changes():
    """
    Dosya daha önce yüklendi mi ve değişti mi kontrol et.
    """
    import requests
    
    API_URL = "http://localhost:5000/api"
    
    response = requests.post(
        f"{API_URL}/excel/check-file",
        json={"filepath": "YZM332.xlsx"}
    )
    
    result = response.json()
    
    print("\n" + "="*60)
    print("DOSYA KONTROLÜ")
    print("="*60)
    
    if result['status'] == 'success':
        is_imported = result['is_imported_before']
        has_changed = result['has_changed']
        
        print(f"Dosya Adı: {result['filename']}")
        print(f"Daha önce yüklendi mi: {'Evet' if is_imported else 'Hayır'}")
        print(f"Değişti mi: {'Evet' if has_changed else 'Hayır'}")
        
        if result['history']:
            history = result['history']
            print(f"\nGeçmiş:")
            print(f"  Ders Kodu: {history['course_code']}")
            print(f"  Öğrenci Sayısı: {history['student_count']}")
            print(f"  Yükleme Tarihi: {history['import_date']}")
            print(f"  Kaç kez yüklendi: {history['import_count']}")
    
    print("="*60 + "\n")


# =============================================================================
# ÖRNEK 6: İki Excel dosyasını karşılaştırma (BONUS)
# =============================================================================

def example_6_compare_excel_files():
    """
    Eski ve yeni Excel dosyasını karşılaştır, değişiklikleri göster.
    """
    import requests
    
    API_URL = "http://localhost:5000/api"
    
    response = requests.post(
        f"{API_URL}/excel/compare-files",
        json={
            "file1_path": "YZM332_old.xlsx",
            "file2_path": "YZM332_new.xlsx",
            "course_code": "YZM332"
        }
    )
    
    result = response.json()
    
    print("\n" + "="*60)
    print("DOSYA KARŞILAŞTIRMASI")
    print("="*60)
    
    if result['status'] == 'success':
        comp = result['comparison']
        
        print(f"Ders: {result['course_code']}")
        print(f"\nDeğişiklikler:")
        print(f"  ✅ Yeni Eklenen: {comp['added_count']}")
        print(f"  ❌ Silinen: {comp['removed_count']}")
        print(f"  = Değişmeyen: {comp['unchanged_count']}")
        print(f"  📊 Toplam Değişiklik: {comp['total_changes']}")
        
        if comp['added']:
            print(f"\nYeni Öğrenciler:")
            for student in comp['added'][:5]:
                print(f"  + {student['number']}: {student['name']}")
            if len(comp['added']) > 5:
                print(f"  ... ve {len(comp['added']) - 5} daha")
        
        if comp['removed']:
            print(f"\nSilinen Öğrenciler:")
            for student in comp['removed'][:5]:
                print(f"  - {student['number']}: {student['name']}")
            if len(comp['removed']) > 5:
                print(f"  ... ve {len(comp['removed']) - 5} daha")
        
        print(f"\n{result['report']}")
    
    print("="*60 + "\n")


# =============================================================================
# ÖRNEK 7: Toplu yeniden yükleme (BONUS)
# =============================================================================

def example_7_bulk_reimport():
    """
    Klasördeki tüm Excel dosyalarını temizleyip yeniden yükle.
    """
    import requests
    
    API_URL = "http://localhost:5000/api"
    
    # Önce onay iste
    print("⚠️  Tüm öğrenci verileri silinecek ve yeniden yüklenecek!")
    confirm = input("Devam etmek istediğinize emin misiniz? (evet/hayır): ")
    
    if confirm.lower() != 'evet':
        print("❌ İşlem iptal edildi")
        return
    
    response = requests.post(
        f"{API_URL}/excel/bulk-reimport",
        json={
            "folder_path": "excel_listeleri",
            "clear_existing": True,
            "confirm": True
        }
    )
    
    result = response.json()
    
    print("\n" + "="*60)
    print("TOPLU YENIDEN YÜKLEME")
    print("="*60)
    
    if result['status'] == 'success':
        print(f"✅ {result['succeeded']} dosya başarıyla yüklendi")
        print(f"❌ {result['failed']} dosya başarısız oldu")
        print(f"📊 Toplam: {result['processed']} dosya işlendi")
        
        print(f"\nDetaylar:")
        for detail in result['details']:
            status_symbol = "✅" if detail['status'] == 'success' else "❌"
            print(f"{status_symbol} {detail['filename']}")
            if detail['status'] == 'success':
                print(f"   Ders: {detail['course_code']}")
                print(f"   Öğrenci: {detail['students_imported']}")
            else:
                print(f"   Hata: {detail['error']}")
    
    print("="*60 + "\n")


# =============================================================================
# ÖRNEK 8: Derslik Yakınlıkları Görüntüleme
# =============================================================================

def example_8_view_classroom_proximities():
    """
    Yüklenen derslik yakınlıklarını görüntüle.
    """
    import requests
    
    API_URL = "http://localhost:5000/api"
    
    response = requests.get(f"{API_URL}/classroom-proximities")
    proximities = response.json()
    
    print("\n" + "="*60)
    print("DERSLIK YAKINLIK TABLOSU")
    print("="*60)
    
    if not proximities:
        print("Hiçbir yakınlık kaydı bulunamadı")
    else:
        print(f"{'Ana':<10} {'Yakın':<10} {'Bitişik':<8} {'Mesafe':<8} {'Notlar':<30}")
        print("-" * 70)
        
        for prox in proximities:
            adjacent = "✅ Evet" if prox['is_adjacent'] else "❌ Hayır"
            distance = f"{prox['distance']}m" if prox['distance'] else "-"
            notes = prox['notes'][:25] if prox['notes'] else ""
            
            print(f"{prox['primary_classroom']:<10} {prox['nearby_classroom']:<10} {adjacent:<8} {distance:<8} {notes:<30}")
    
    print("="*60 + "\n")


# =============================================================================
# MENU VE MAIN
# =============================================================================

def show_menu():
    """İnteraktif menü göster"""
    print("\n" + "="*60)
    print("EXCEL YÜKLEME SİSTEMİ - HIZLI BAŞLANGIÇ ÖRNEKLERİ")
    print("="*60)
    print("\nSeçenekler:")
    print("1. Tek Excel dosyası yükle")
    print("2. Klasördeki dosyaları tara")
    print("3. Derslik Yakınlık yükle")
    print("4. Yükleme geçmişi görüntüle")
    print("5. Dosya değişiklikleri kontrol et (BONUS)")
    print("6. İki dosyayı karşılaştır (BONUS)")
    print("7. Toplu yeniden yükle (BONUS)")
    print("8. Derslik Yakınlıkları görüntüle")
    print("0. Çık")
    print("="*60)


def main():
    """Ana program"""
    while True:
        show_menu()
        choice = input("\nSeçiminiz (0-8): ").strip()
        
        try:
            if choice == "1":
                example_1_single_file_upload()
            elif choice == "2":
                example_2_scan_folder()
            elif choice == "3":
                example_3_upload_classroom_proximity()
            elif choice == "4":
                example_4_view_import_history()
            elif choice == "5":
                example_5_check_file_changes()
            elif choice == "6":
                example_6_compare_excel_files()
            elif choice == "7":
                example_7_bulk_reimport()
            elif choice == "8":
                example_8_view_classroom_proximities()
            elif choice == "0":
                print("\n👋 Hoşça kalın!")
                break
            else:
                print("❌ Geçersiz seçim!")
        
        except Exception as e:
            print(f"❌ Hata: {e}")
            print("💡 API sunucusunun çalışmakta olduğundan emin olun")


if __name__ == "__main__":
    # Seçim yapın:
    # 1. İnteraktif menü:
    main()
    
    # 2. VEYA direkt örnek çalıştır:
    # example_1_single_file_upload()
