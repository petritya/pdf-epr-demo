import re


def _normalize_text(text: str) -> str:
    """
    Google Docs TXT néha össze tud ragasztani részeket.
    Tipikus: ...LAGUVAL574164 -> ...LAGU VAL574164
    """
    # szóköz beszúrása, ha egy BETŰ után közvetlenül jön a VAL + 6 szám
    text = re.sub(r"([A-ZÁÉÍÓÖŐÚÜŰ])(?=VAL\d{6}\b)", r"\1 ", text)

    # whitespace normalizálás
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\r\n|\r", "\n", text)

    return text


def _clean_name(name: str) -> str:
    name = name.strip()

    # súlyszám/vezető szám eltávolítása (régi logika)
    name = re.sub(r"^\d+,\d+\s+", "", name)

    # néha a név elején maradnak odacsúszó darabok: legyen egyben
    name = re.sub(r"\s+", " ", name).strip()

    return name


def parse_text(text):
    """
    Tétel mintázat (rugalmasan):
    NÉV + CIKKSZÁM + SZT + ... + HUF + ÁR + HUF + x,y x,y + (fitment...) + [következő tétel]
    """
    text = _normalize_text(text)

    results = []

    # Tétel-kereső regex:
    # - name: minimális, amíg el nem érjük a cikkszámot
    # - code: egy token (nem whitespace), ez lesz a cikkszám
    # - utána SZT
    # - ár: "1 889,00" jellegű is lehet
    # - utána HUF + két szám (pl. 0,05 0,05)
    # - majd bármi (fitment) egészen a következő cikkszám+SZT-ig vagy "Választék:"-ig
    item_re = re.compile(
        r"(?P<name>.+?)\s+"
        r"(?P<code>\S+)\s+"
        r"(?P<uom>SZT|szt)\s+"
        r".*?HUF\s+"
        r"(?P<price>[\d ]+,\d+)\s+HUF\s+"
        r"(?P<w1>\d+,\d+)\s+"
        r"(?P<w2>\d+,\d+)"
        r".*?"
        r"(?=(?:\s+\S+\s+(?:SZT|szt)\s+\d+,\d+)|(?:\s+\d+\s+Választék:)|$)",
        flags=re.DOTALL,
    )

    for m in item_re.finditer(text):
        name = _clean_name(m.group("name"))
        code = m.group("code").strip()

        # Fejlécek kiszűrése (régi logika)
        if "Számla" in name or "Auto Partner" in name:
            continue

        # Extra védelem: ha mégis beakadna egy "fitment/cikkszám összetapadás",
        # akkor próbáljuk a végéből kiszedni a valódi cikkszámot.
        # Pl.: CLIO/ESPACE/LAGUA VAL574164 -> code lehetne még rossz formátumban.
        # Ha a token tartalmaz / jelet, keressük benne a VAL\d{6} mintát:
        if "/" in code:
            mm = re.search(r"(VAL\d{6})\b", code)
            if mm:
                code = mm.group(1)

        # A te outputodban "Brutto_suly" volt, de valójában az ár jön innen.
        # Meghagyom ugyanúgy, csak a mezőnév a headerben az app.py-ban van.
        brutto_suly = m.group("price").strip().replace(" ", "")  # "1 889,00" -> "1889,00"

        results.append((name, code, brutto_suly))

    return results
