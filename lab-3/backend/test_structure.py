import requests
from bs4 import BeautifulSoup

response = requests.get('https://kocaelisaglik.edu.tr/akademik-kadro/', timeout=30)
soup = BeautifulSoup(response.content, 'html.parser')

# Tüm yapıyı kontrol et
print("=== Sayfadaki tüm başlıklar ===")
h4s = soup.find_all('h4')
h5s = soup.find_all('h5')
print(f"H4 eleman: {len(h4s)}")
print(f"H5 eleman: {len(h5s)}")

if len(h4s) > 0:
    print("\n=== İlk 5 H4 eleman ===")
    for i in range(min(5, len(h4s))):
        print(f"H4[{i}]: {h4s[i].get_text(strip=True)[:100]}")
        
if len(h5s) > 0:
    print("\n=== İlk 5 H5 eleman ===")
    for i in range(min(5, len(h5s))):
        print("\n" + "="*50 + "\n")
        print(f"H5[{i}]: {h5s[i].get_text(strip=True)[:100]}")

# Yapıyı daha detaylı kontrol et
print("\n\n=== Detaylı Yapı Analizi ===")
all_divs = soup.find_all('div')
for i, div in enumerate(all_divs[:10]):
    print(f"Div {i}: class={div.get('class')} | text={div.get_text(strip=True)[:50]}")
