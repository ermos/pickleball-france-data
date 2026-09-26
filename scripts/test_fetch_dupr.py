import json

import fetch_dupr


def test_missing_players_are_fetched_with_exclude(tmp_path, monkeypatch):
    ids = list(range(60))

    def search(token, lat, lng, offset, exclude=()):
        # unstable pagination: player 30 never shows up in offset pages
        rest = [i for i in ids if i not in exclude and (exclude or i != 30)]
        return {"total": len(ids) - len(exclude), "hits": [{"id": i, "distance": "1 mi"} for i in rest[offset:offset + 25]]}

    monkeypatch.setattr(fetch_dupr, "refresh", lambda rt: ("at", rt))
    monkeypatch.setattr(fetch_dupr, "search", search)
    monkeypatch.setattr(fetch_dupr, "METRO", [(0, 0)])
    monkeypatch.setattr(fetch_dupr, "OVERSEAS", [])
    monkeypatch.setattr(fetch_dupr, "OUT", tmp_path / "joueurs.json")
    monkeypatch.setattr(fetch_dupr.time, "sleep", lambda s: None)
    monkeypatch.setenv("DUPR_REFRESH_TOKEN", "rt")
    fetch_dupr.main()
    assert [p["id"] for p in json.loads((tmp_path / "joueurs.json").read_text())] == ids
