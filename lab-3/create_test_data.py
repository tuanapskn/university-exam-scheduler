"""
Test Verileri - Excel Yükleme Sistemi
=====================================

Bu dosya test amacıyla örnek Excel dosyaları oluşturmak için
pandas kullanarak test veri setleri hazırlar.
"""

import pandas as pd
from pathlib import Path

def create_sample_class_lists():
    """
    Örnek sınıf listesi Excel dosyaları oluştur.
    """
    
    test_dir = Path("test_excel_files")
    test_dir.mkdir(exist_ok=True)
    
    # YZM332 - Algoritma
    yzm332_data = {
        'Öğrenci Numarası': [
            '2024001', '2024002', '2024003', '2024004', '2024005',
            '2024006', '2024007', '2024008', '2024009', '2024010',
            '2024011', '2024012', '2024013', '2024014', '2024015',
            '2024016', '2024017', '2024018', '2024019', '2024020'
        ],
        'Öğrenci Adı': [
            'Ahmet Yılmaz', 'Ayşe Demir', 'Mehmet Kara', 'Fatih Şahin', 'Zeynep Yıldız',
            'Can Öztürk', 'Elif Tarhan', 'Bünyamin Göçer', 'Deniz Arslanoğlu', 'Ece Kaya',
            'Furkan Kus', 'Gamze Taş', 'Halil Yücel', 'İrem Taner', 'Jale Kara',
            'Kadir Özkan', 'Leyla Güzel', 'Murat Yılmazer', 'Nilüfer Soy', 'Ödön Berger'
        ]
    }
    df = pd.DataFrame(yzm332_data)
    df.to_excel(test_dir / "YZM332_Algoritma.xlsx", index=False)
    print(f"✅ YZM332_Algoritma.xlsx ({len(df)} satır)")
    
    # BLM111 - Veri Tabanı
    blm111_data = {
        'Öğrenci Numarası': [
            '2024021', '2024022', '2024023', '2024024', '2024025',
            '2024026', '2024027', '2024028', '2024029', '2024030',
            '2024031', '2024032', '2024033', '2024034', '2024035'
        ],
        'Öğrenci Adı': [
            'Pınar Erdoğan', 'Ramazan Kaya', 'Sare Şarer', 'Turgay Topdemir', 'Ufuk Ugur',
            'Veda Voran', 'Wilya Weiss', 'Xena Xenakis', 'Yasemin Yasarcan', 'Zehra Zağlı',
            'Adnan Aşık', 'Berfu Başar', 'Cenk Çolak', 'Demir Duru', 'Emre Erkan'
        ]
    }
    df = pd.DataFrame(blm111_data)
    df.to_excel(test_dir / "BLM111_VT.xlsx", index=False)
    print(f"✅ BLM111_VT.xlsx ({len(df)} satır)")
    
    # YZM329 - İşletim Sistemleri
    yzm329_data = {
        'Öğrenci Numarası': [
            '2024036', '2024037', '2024038', '2024039', '2024040',
            '2024041', '2024042', '2024043', '2024044', '2024045'
        ],
        'Öğrenci Adı': [
            'Fidan Fin', 'Gülşah Güney', 'Hava Hakim', 'İbrahim İçen', 'Jale Jamal',
            'Koray Koçer', 'Lina Lekce', 'Müge Müller', 'Nurcan Nural', 'Özlem Özer'
        ]
    }
    df = pd.DataFrame(yzm329_data)
    df.to_excel(test_dir / "YZM329_OS.xlsx", index=False)
    print(f"✅ YZM329_OS.xlsx ({len(df)} satır)")
    
    # MAT211 - Lineer Cebir
    mat211_data = {
        'Öğrenci Numarası': [
            '2024101', '2024102', '2024103', '2024104', '2024105',
            '2024106', '2024107', '2024108', '2024109', '2024110',
            '2024111', '2024112', '2024113', '2024114', '2024115',
            '2024116', '2024117', '2024118', '2024119', '2024120'
        ],
        'Öğrenci Adı': [
            'Öner Öymen', 'Pınar Paşa', 'Rafet Rauf', 'Suat Suvak', 'Tevfik Tark',
            'Umut Uyan', 'Veli Vega', 'Wilmar Wagner', 'Yasir Yalçın', 'Zeki Zaman',
            'Aydın Ayrancı', 'Başak Başarslan', 'Cafer Caka', 'Dogan Doğdu', 'Edin Edis',
            'Fahri Fahr', 'Gani Gani', 'Haluk Hasan', 'İhsan İhsan', 'Jihan Jima'
        ]
    }
    df = pd.DataFrame(mat211_data)
    df.to_excel(test_dir / "MAT211_LinearAlgebra.xlsx", index=False)
    print(f"✅ MAT211_LinearAlgebra.xlsx ({len(df)} satır)")
    
    print(f"\n✨ Tüm örnek dosyalar {test_dir} klasöründe oluşturuldu")


def create_sample_classroom_proximity():
    """
    Örnek Derslik Yakınlığı dosyası oluştur.
    """
    
    test_dir = Path("test_excel_files")
    test_dir.mkdir(exist_ok=True)
    
    proximity_data = {
        'Ana Derslik': [
            'D101', 'D101', 'D101', 'D102', 'D102', 'D102', 'D103', 'D104',
            'A101', 'A101', 'A102', 'A103', 'A104', 'A105',
            'L101', 'L102', 'L103'
        ],
        'Yakın Derslik': [
            'D102', 'D103', 'D104', 'D101', 'D103', 'D105', 'D101', 'D105',
            'A102', 'A103', 'A101', 'A102', 'A103', 'A106',
            'L102', 'L101', 'L101'
        ],
        'Bitişik': [
            True, False, False, True, False, False, False, False,
            True, False, True, True, False, False,
            True, True, False
        ],
        'Mesafe': [
            5, 15, 25, 5, 10, 30, 15, 35,
            3, 12, 3, 5, 8, 20,
            2, 2, 50
        ]
    }
    
    df = pd.DataFrame(proximity_data)
    df.to_excel(test_dir / "DerslikYakınlık.xlsx", index=False)
    print(f"✅ DerslikYakınlık.xlsx ({len(df)} satır)")
    print(f"✨ Derslik Yakınlığı dosyası {test_dir} klasöründe oluşturuldu")


def create_invalid_test_file():
    """
    Geçersiz format test dosyası oluştur.
    """
    
    test_dir = Path("test_excel_files")
    test_dir.mkdir(exist_ok=True)
    
    # Yanlış sütun adları
    invalid_data = {
        'Numara': ['2024001', '2024002'],
        'İsim': ['Ahmet', 'Ayşe']  # "Öğrenci Numarası" ve "Öğrenci Adı" değil
    }
    
    df = pd.DataFrame(invalid_data)
    df.to_excel(test_dir / "InvalidFormat.xlsx", index=False)
    print(f"✅ InvalidFormat.xlsx (test için - geçersiz format)")


def create_empty_test_file():
    """
    Boş test dosyası oluştur.
    """
    
    test_dir = Path("test_excel_files")
    test_dir.mkdir(exist_ok=True)
    
    df = pd.DataFrame()
    df.to_excel(test_dir / "Empty.xlsx", index=False)
    print(f"✅ Empty.xlsx (test için - boş dosya)")


def main():
    """Ana test veri oluşturucu"""
    
    print("="*60)
    print("TEST VERİ OLUŞTURUCU")
    print("="*60 + "\n")
    
    print("📋 Örnek Sınıf Listeleri Oluşturuluyor...\n")
    create_sample_class_lists()
    
    print("\n📊 Derslik Yakınlığı Dosyası Oluşturuluyor...\n")
    create_sample_classroom_proximity()
    
    print("\n⚠️  Test Dosyaları (Hata Senaryoları) Oluşturuluyor...\n")
    create_invalid_test_file()
    create_empty_test_file()
    
    print("\n" + "="*60)
    print("✨ TÜM TEST VERİLERİ BAŞARIYLA OLUŞTURULDU!")
    print("="*60)
    
    print("\nKlasor: test_excel_files/")
    print("\nYükleme Talimatları:")
    print("1. Backend sunucusunu başlatın: python backend/app.py")
    print("2. Tek dosya yükleme: python quick_examples.py")
    print("3. Seçenek 1'i seçin ve test dosyalarından birini seçin")
    
    print("\nveya cURL kullanarak:")
    print("  curl -X POST http://localhost:5000/api/excel/scan-folder \\")
    print("    -H 'Content-Type: application/json' \\")
    print("    -d '{\"folder_path\": \"test_excel_files\"}'")


if __name__ == "__main__":
    main()
