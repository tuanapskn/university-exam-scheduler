from kostu_scraper import scrape_kostu_teachers

teachers, error = scrape_kostu_teachers()

if error:
    print(f"❌ Hata: {error}")
else:
    print(f"✅ {len(teachers)} öğretim üyesi çekildi\n")
    for i, teacher in enumerate(teachers[:10]):
        print(f"{i+1}. {teacher['name']}")
        print(f"   Unvan: {teacher['title']}")
        print(f"   Fakülte: {teacher['faculty']}")
        print()
