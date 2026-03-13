import re


def normalize_val_glue(text: str) -> str:
    """
    Javítja azokat az eseteket, amikor a Google Docs összetapaszt
    egy szót a VALxxxxxx cikkszámmal, pl:
    LAGUVAL574164 -> LAGU VAL574164
    """
    return re.sub(r"([A-ZÁÉÍÓÖŐÚÜŰ])(?=VAL\d{6}\b)", r"\1 ", text)


def parse_text(text: str):
    results = []

    text = normalize_val_glue(text)

    pattern = re.finditer(
        r"(.+?)\s+"                    # 1: terméknév
        r"(\S+)\s+"                    # 2: cikkszám
        r"(SZT|szt)\s+"                # 3: egység (nem mentjük)
        r"([\d,]+)\s+"                 # 4: mennyiség
        r"([A-Z]{2})\s+"               # 5: szállító országa
        r"(.+?)\s+"                    # 6: gyártó
        r"([\d ]+,\d+)\s+"             # 7: nettó ár / összeg
        r"([A-Z]{3})\s+"               # 8: valuta
        r"([\d,]+)\s+"                 # 9: bruttó súly
        r"([\d,]+)",                   # 10: bruttó tömeg
        text
    )

    for match in pattern:
        termeknev = match.group(1).strip()
        cikkszam = match.group(2).strip()
        mennyiseg = match.group(4).strip()
        szallito_orszag = match.group(5).strip()
        gyarto = match.group(6).strip()
        netto_ar = match.group(7).strip().replace(" ", "")
        valuta = match.group(8).strip()
        brutto_suly = match.group(9).strip()
        brutto_tomeg = match.group(10).strip()

        termeknev = re.sub(r"^\d+,\d+\s+", "", termeknev)

        if "Számla" in termeknev or "Auto Partner" in termeknev:
            continue

        if "Választék:" in termeknev:
            continue

        results.append((
            termeknev,
            cikkszam,
            mennyiseg,
            szallito_orszag,
            gyarto,
            netto_ar,
            valuta,
            brutto_suly,
            brutto_tomeg
        ))

    return results
