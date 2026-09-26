"""Fetch every DUPR player found in circles covering France into data/dupr/joueurs.json.

The search API caps the radius at 100 miles (160934 m), the page size at 25 and
the offset at 10000, so France is covered by a grid of overlapping circles and
results are deduplicated by player id. No country filter: many addresses lack a
country code (e.g. "Le Mans"), so every match is kept, border neighbours included.

Needs DUPR_REFRESH_TOKEN: the `__Host-dupr_rt` cookie from dashboard.dupr.com.
Each refresh returns a new refresh token valid 90 days, written to the file named by
DUPR_REFRESH_TOKEN_OUT (if set) so CI can store it back in its secret.
"""
import json
import os
import time
import urllib.request
from pathlib import Path

API = "https://api.dupr.com/player/v1.0/search"
REFRESH = "https://api.dupr.com/auth/v2.0/refresh"
OUT = Path(__file__).resolve().parent.parent / "data" / "dupr" / "joueurs.json"
RADIUS = 160934
PAGE = 25
MAX_OFFSET = 10000
# Pagination is unstable (players at the same distance come back in random order across
# pages, ~1% missed per pass), so a cell is re-paginated until every id has been seen.
MAX_PASSES = 6
# Metropolitan France: 1.5° lat x 2° lng cells, half diagonal ~115 km < radius.
# The north is covered by a single inland cell so no circle reaches England (and its
# thousands of players, which would hit the 10000 offset cap): (49, -5) dropped
# (Cornwall), (50, 3.2) reaches Dunkirk/Boulogne but stops before Dover.
METRO = [(41.5 + 1.5 * i, -5 + 2 * j) for i in range(6) for j in range(8) if (i, j) != (5, 0)] + [(50.0, 3.2)]
OVERSEAS = [(16.2, -61.5), (14.6, -61.0), (4.0, -53.0), (-21.1, 55.5), (-12.8, 45.2),
            (-21.5, 165.5), (-17.6, -149.5), (46.8, -56.2), (17.9, -62.8), (-13.3, -176.2)]


def refresh(rt):
    """Return (access_token, refresh_token) from the Set-Cookie headers of the refresh endpoint."""
    req = urllib.request.Request(REFRESH, data=b"{}", method="POST", headers={
        "Content-Type": "application/json",
        "Origin": "https://dashboard.dupr.com",
        "Cookie": f"__Host-dupr_rt={rt}",
    })
    with urllib.request.urlopen(req, timeout=60) as r:
        cookies = dict(c.split(";", 1)[0].split("=", 1) for c in r.headers.get_all("Set-Cookie") or [])
    if "__Host-dupr_at" not in cookies:
        raise SystemExit("DUPR refresh failed, DUPR_REFRESH_TOKEN expired? Copy a new __Host-dupr_rt cookie")
    return cookies["__Host-dupr_at"], cookies.get("__Host-dupr_rt", rt)


def get(token, path):
    req = urllib.request.Request(f"https://api.dupr.com{path}", headers={
        "Origin": "https://dashboard.dupr.com",
        "Cookie": f"__Host-dupr_at={token}",
    })
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)["result"]


def search(token, lat, lng, offset):
    body = {"limit": PAGE, "offset": offset, "query": "*", "exclude": [], "includeUnclaimedPlayers": True,
            "filter": {"lat": lat, "lng": lng, "rating": {}, "radiusInMeters": RADIUS}}
    req = urllib.request.Request(API, data=json.dumps(body).encode(), headers={
        "Content-Type": "application/json",
        "Origin": "https://dashboard.dupr.com",
        "Cookie": f"__Host-dupr_at={token}",
    })
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.load(r)
    if d.get("status") != "SUCCESS":
        raise SystemExit(f"DUPR error at {lat},{lng} offset {offset}: {d.get('message')}")
    return d["result"]


def main():
    token, rt = refresh(os.environ["DUPR_REFRESH_TOKEN"])
    if os.environ.get("DUPR_REFRESH_TOKEN_OUT"):
        Path(os.environ["DUPR_REFRESH_TOKEN_OUT"]).write_text(rt)
    players = {}
    for lat, lng in METRO + OVERSEAS:
        seen, total, passes = set(), 1, 0
        while len(seen) < total and passes < MAX_PASSES:
            passes, offset = passes + 1, 0
            while offset < total:
                res = search(token, lat, lng, offset)
                total = res["total"]
                if total > MAX_OFFSET:
                    raise SystemExit(f"{total} players around {lat},{lng}, split this cell")
                for h in res["hits"]:
                    seen.add(h["id"])
                    # distance depends on the query center, drop it to keep diffs clean
                    players[h["id"]] = {k: v for k, v in h.items() if not k.startswith("distance")}
                offset += PAGE
                time.sleep(0.2)
        print(f"{lat},{lng}: {len(seen)}/{total} joueurs en {passes} passes, {len(players)} cumulés")
    # search never returns the account owning the token, add it back with the same fields
    me = get(token, f"/player/v1.0/{get(token, '/user/v1.0/profile')['id']}")
    fields = set().union(*players.values())
    players[me["id"]] = {k: v for k, v in me.items() if k in fields}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(sorted(players.values(), key=lambda p: p["id"]), ensure_ascii=False, indent=2) + "\n")
    print(f"{len(players)} joueurs sauvegardés dans {OUT}")


if __name__ == "__main__":
    main()
