import pandas as pd
from pathlib import Path

# Klasörü oluştur
excel_dir = Path("excel-listeleri")
excel_dir.mkdir(exist_ok=True)

# Test 1: Sınıf Listesi - YZM332
data1 = {
    'Öğrenci Numarası': ['001', '002', '003', '004'],
    'Öğrenci Adı': ['Ahmet Yılmaz', 'Betül Kaya', 'Cem Öztürk', 'Deniz Şahin']
}
df1 = pd.DataFrame(data1)
df1.to_excel(excel_dir / 'SınıfListesi[YZM332].xlsx', index=False)
print("✅ SınıfListesi[YZM332].xlsx oluşturuldu")

# Test 2: Sınıf Listesi - MAT213
data2 = {
    'öğrenci numarası': ['101', '102', '103'],
    'öğrenci adı': ['Emir Demir', 'Figen Gül', 'Gözde Han']
}
df2 = pd.DataFrame(data2)
df2.to_excel(excel_dir / 'SınıfListesi[MAT213].xlsx', index=False)
print("✅ SınıfListesi[MAT213].xlsx oluşturuldu")

# Test 3: Sınıf Listesi - BLM111 (alternative column names)
data3 = {
    'numara': ['201', '202', '203', '204', '205'],
    'ad': ['İbrahim İnal', 'Jale Japon', 'Kaan Kaynak', 'Leyla Ladin', 'Mert Müller']
}
df3 = pd.DataFrame(data3)
df3.to_excel(excel_dir / 'SınıfListesi[BLM111].xlsx', index=False)
print("✅ SınıfListesi[BLM111].xlsx oluşturuldu")

# Test 4: Derslik Yakınlıkları
proximity_data = {
    'Ana Derslik': ['A101', 'A102', 'A103', 'B201'],
    'Yakın Derslik': ['A102', 'A103', 'A104', 'B202'],
    'Bitişik': [True, True, False, True],
    'Mesafe': [5.5, 3.2, 15.0, 2.1]
}
df_proximity = pd.DataFrame(proximity_data)
df_proximity.to_excel(excel_dir / 'DerslikYakınlık.xlsx', index=False)
print("✅ DerslikYakınlık.xlsx oluşturuldu")

print(f"\n📁 Tüm dosyalar '{excel_dir}' klasöründe oluşturuldu!")
print("\nDosya Listesi:")
for file in sorted(excel_dir.glob('*.xlsx')):
    print(f"  - {file.name}")
