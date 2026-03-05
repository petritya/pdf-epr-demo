import re


def normalize_val_glue(text: str) -> str:
    """
    Javítja azokat az eseteket, amikor a Google Docs összetapaszt
    egy szót a VALxxxxxx cikkszámmal, pl: LAGUVAL574164 -> LAGU VAL574164
    """
    # Csak akkor szúrunk be szóközt, ha közvetlenül előtte betű van,
    # és utána pontosan VAL + 6 szám jön.
    return re.sub(r"([A-ZÁÉÍÓÖŐÚÜŰ])(?=VAL\d{6}\b)", r"\1 ", text)


def parse_text(text: str):
    results = []

    text = normalize_val_glue(text)

    # EZ AZ EREDETI LOGIKA (csak meghagytuk):
    # NÉV (bármi) + szóköz + CIKKSZÁM (nem whitespace) + szóköz + SZT/szt + ... HUF + szám(,szám)
    pattern = re.finditer(
        r'(.+?)\s+(\S+)\s+(SZT|szt)\s+.*?HUF\s+([\d,]+)',
        text
    )

    for match in pattern:
        nev = match.group(1).strip()
        cikkszam = match.group(2).strip()
        brutto_suly = match.group(4).strip()

        # súlyszám eltávolítása (eredeti)
        nev = re.sub(r'^\d+,\d+\s+', '', nev)

        # fejléc kiszűrés (eredeti)
        if "Számla" in nev or "Auto Partner" in nev:
            continue

        results.append((nev, cikkszam, brutto_suly))

    return results
