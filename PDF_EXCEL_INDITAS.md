# Általános PDF → Excel – első fejlesztési változat

A meglévő `app.py` és az éles indítás változatlan. Az új alkalmazás: `webapp:app`.

## Elkészült

- Több PDF vagy PDF-eket tartalmazó ZIP, legfeljebb 5 dokumentum / 10 oldal / 20 MB.
- Általános, oldalankénti AI-adatkinyerés, külön táblázatok és nem táblázatos szöveg.
- Dokumentumonként külön XLSX, több dokumentumnál ZIP letöltés.
- Forrásfájl és oldalszám; bizonytalanságok munkalap; az eredeti számírásmód és kezdő nullák megőrzése szöveges cellákkal.
- Háttérfeldolgozás, állapotjelzés, kitalálhatatlan letöltési token.
- Feltöltési és ZIP-korlátok, képletfuttatás kizárása Excel-cellákban.
- Bemenetek csak feldolgozás alatt a memóriában; eredmény kb. 15 percig (30 másodperces takarítás). Multipart fogadásnál a keretrendszer átmeneti fájlt is használhat, amely a kérés lezárásakor törlődik.
- API-kulcs és adatkezelési URL nélkül a feldolgozás nem indul el.

## Indítás

Python 3.12+.

```text
pip install -r requirements-pdf-excel.txt
uvicorn webapp:app --host 0.0.0.0 --port 8000 --workers 1 --no-access-log
```

Szerveroldali változók:

- OPENAI_API_KEY: a saját OpenAI projekt API-kulcsa, titkos változóként.
- OPENAI_MODEL: alapértelmezett tesztjelölt gpt-5.4-mini; valódi mintákon még nem validált.
- PRIVACY_URL: a végleges, ehhez a szolgáltatáshoz igazított HTTPS adatkezelési tájékoztató URL-je.
- PILOT_MAX_JOBS: alapértelmezetten 20 indítás folyamatonként.

Railway tesztszolgáltatásban a telepítési parancs használja a külön requirements-pdf-excel.txt fájlt. Az indítóparancsban a Railway PORT változóját kell alkalmazni. Az éles szolgáltatást és a régi requirements.txt fájlt nem módosítottuk.

## Ellenőrzés

```text
pip install pytest
pytest -q
```

Nyolc teszt sikeres: XLSX-tartalom, vezető nullák, képletbiztonság, több PDF kimenete, ZIP-útvonal, oldallimit, sérült bemenet, konfigurációs tiltás és szimulált végponttól végpontig feldolgozás. A tesztek egy része több állítást ellenőriz.

Az AI-t a tesztekben helyettesítő függvény váltotta ki. Nem történt fizetős API-hívás, valódi OCR-minőségmérés vagy éles telepítés. A felületet HTTP-n ellenőriztük, böngészős vizuális teszt még nem történt.

## Nyilvános reklámozás előtt

1. Saját API-kulcs biztonságos bekötése és valódi magyar PDF-ekkel minőségteszt, számlákon, képeket tartalmazó PDF-eken és többoldalas táblákon.
2. Adatkezelési tájékoztató: az OpenAI is adatot kap. A store=false nem jelent garantált nulla szolgáltatói megőrzést. Üzemeltető, szolgáltatók és megőrzések rögzítése.
3. Tartós, újraindítást túlélő összesített költségkeret és nyilvános visszaélésvédelem (pl. Turnstile). A jelenlegi folyamatonkénti 20-as limit újrainduláskor nullázódik; nyilvános kampányhoz önmagában nem elég.
4. A pilot egy munkással, memóriában kezeli a munkákat; újraindításkor a folyamatban lévő és letölthető munkák elvesznek. Tartós munkasor szükséges, ha a terhelés vagy elvárt rendelkezésre állás ezt indokolja.
5. Proxy feltöltési limit és az ideiglenes tárhely ellenőrzése; párhuzamos túlterhelési teszt.
6. Sikeres, de hibás AI-kiolvasás lehetséges: nincs minden dokumentumtípusra általános teljességi bizonyíték. Ez az első kipróbálható kódváltozat, nem minősített könyvelési import.

## Tudatos működési döntések

Nincs ügyféloldali oszloplista vagy szabad szöveges feladatleírás. Nincs e-mail, importkonverzió vagy előfizetés ebben a változatban. Az új dokumentumfajtához nem kell egyedi parser. Az azonos című és azonos fejlécű táblákat a rendszer egy dokumentumon belül egyesíti, az eltérőeket külön lapra teszi. A teljes oldalankénti kontextus hiánya miatt többoldalas fejléc nélküli táblák külön lapra kerülhetnek. Az eredeti app érintetlen.
