"""Download FFT pickleball ranking PDFs and convert them to JSON in data/."""
import io
import json
import re
import unicodedata
import urllib.request
from pathlib import Path

import pdfplumber

PAGE = "https://www.fft.fr/nos-sports/pickleball/les-regles-et-classement-pickleball"
OUT = Path(__file__).resolve().parent.parent / "data"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def to_int(s):
    return int(s) if s and s.strip().isdigit() else None


def parse_rows(rows):
    """Turn raw table rows into player dicts. Series is only printed on the first row of each block."""
    players, serie = [], None
    for r in rows:
        r = [(c or "").replace("\n", " ").strip() for c in r]
        if "NOM" in r:
            if len(r) == 11:  # header of the unranked foreign players section
                serie = None
            continue
        if len(r) == 11:  # unranked foreign players: no RANG column
            r.insert(1, "")
        if len(r) != 12 or not r[5]:
            continue
        serie = r[0] or serie
        players.append({
            "serie": serie,
            "rang": to_int(r[1]),
            "nationalite": r[2],
            "nom": r[3],
            "prenom": r[4],
            "licence": r[5],
            "ligue": r[6],
            "club": r[7],
            "tournois_joues": to_int(r[8]),
            "points": to_int(r[9]),
            "equivalence_plus_50": r[10] or None,
            "equivalence_autres_pratiques": r[11] or None,
        })
    return players


def slugify(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def convert(url):
    with pdfplumber.open(io.BytesIO(get(url))) as pdf:
        text = pdf.pages[0].extract_text() or ""
        rows = [r for p in pdf.pages for t in p.extract_tables() for r in t]
    title = re.search(r"CLASSEMENT PICKLEBALL (.+)", text).group(1).strip()
    period = re.search(r"\((Tournois dont.+?)\)", text)
    date = re.findall(r"\d{2}/\d{2}/\d{4}", text)
    return slugify(title), {
        "titre": title,
        "periode": period and period.group(1),
        "date_publication": date[-1] if date else None,
        "source": url,
        "joueurs": parse_rows(rows),
    }


def main():
    html = get(PAGE).decode()
    urls = sorted(set(re.findall(r'href="([^"]*Classement[^"]*\.pdf)"', html)))
    if not urls:
        raise SystemExit("no ranking PDF found, page layout changed?")
    OUT.mkdir(exist_ok=True)
    for url in urls:
        slug, data = convert(url)
        (OUT / f"{slug}.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
        print(f"{slug}: {len(data['joueurs'])} joueurs")


if __name__ == "__main__":
    main()
