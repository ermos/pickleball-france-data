from fetch_rankings import parse_rows


def test_parse_rows():
    rows = [
        ["SÉRIE", "RANG", "NAT.", "NOM", "Prénom", "Licence", "LIGUE", "CLUB", "n", "t", "e", "a"],
        ["5.0", "1", "FRA", "PELTIER", "Cyril", "1560843 T", "BRETAGNE", "LANVALLAY", "7", "1655", "", ""],
        [None, "2", "FRA", "ROY", "Mathieu", "7158080 W", "OCCITANIE", "CUGNAUX", "13", "1435", "5.0", ""],
        ["3.0", "ESP", "CASANOVA", "Enrique", "4663042 Y", "OCCITANIE", "RAQUETTE CLUB PORT\nCAMARGUE", "1", "1", "3.0", ""],
        ["", "NAT.", "NOM", "Prénom", "Licence", "LIGUE", "CLUB", "n", "t", "e", "a"],
        ["titre seul"],
    ]
    p = parse_rows(rows)
    assert len(p) == 3
    assert p[1]["serie"] == "5.0" and p[1]["rang"] == 2 and p[1]["equivalence_plus_50"] == "5.0"
    assert p[2]["rang"] is None and p[2]["serie"] == "3.0" and p[2]["nationalite"] == "ESP" and p[2]["club"] == "RAQUETTE CLUB PORT CAMARGUE"
