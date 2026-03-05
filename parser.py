import re


def parse_text(text):
    results = []

    pattern = re.finditer(
        r"(.+?)\s+(\S+)\s+(SZT|szt)\s+.*?HUF\s+([\d,]+)",
        text,
    )

    for match in pattern:
        nev = match.group(1).strip()
        cikkszam = match.group(2).strip()
        brutto_suly = match.group(4).strip()

        # súlyszám eltávolítása
        nev = re.sub(r"^\d+,\d+\s+", "", nev)

        # fejléc kiszűrés
        if "Számla" in nev or "Auto Partner" in nev:
            continue

        results.append((nev, cikkszam, brutto_suly))

    return results
