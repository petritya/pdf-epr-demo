import re


def _normalize_text(text: str) -> str:
    """
    Google Docs TXT néha összetapaszt két szót/cikkszámot.
    Pl: ...LAGUVAL574164 -> ...LAGU VAL574164
    """
    # szóköz beszúrása, ha egy BETŰ után közvetlenül jön a VAL + 6 szám
    text = re.sub(r"([A-ZÁÉÍÓÖŐÚÜŰ])(?=VAL\d{6}\b)", r"\1 ", text)

    # whitespace normalizálás
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\r\n|\r", "\n", text)

    return text


def parse_text(text: str):
    text = _normalize_text(text)
    results = []

    # Régi logika, csak kicsit rugalmasabb:
    # NÉV + (szóköz) + CIKKSZÁM + (szóköz) + SZT/szt + ... + ÁR + HUF + 0,xx 0,xx
    #
    # FONTOS: itt csak 1 darab "HUF" van az ár után!
    pattern = re.finditer(
        r"(?P<name>.+?)\s+"
        r"(?P<code>\S+)\s+"
        r"(?P<uom>SZT|szt)\s+"
        r".*?"
        r"(?P<price>[\d ]+,\d+)\s+HUF\s+"
        r"(?P<w1>\d+,\d+)\s+(?P<w2>\d+,\d+)",
        text,
        flags=re.DOTALL
    )

    for m in pattern:
        nev = m.group("name").strip()
        cikkszam = m.group("code").strip()
        ar = m.group("price").strip()

        # súlyszám eltávolítása (régi)
        nev = re.sub(r"^\d+,\d+\s+", "", nev).strip()

        # fejléc kiszűrés (régi)
        if "Számla" in nev or "Auto Partner" in nev:
            continue

        # Szépítés: "1 889,00" -> "1889,00"
        ar = ar.replace(" ", "")

        results.append((nev, cikkszam, ar))

    return results
