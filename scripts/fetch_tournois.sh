#!/usr/bin/env bash
# Récupère tous les tournois de Pickleball en France (API FFT tenup) et les
# sauvegarde en JSON, pour réutilisation en contenu (articles, réseaux sociaux...).
set -euo pipefail

OUT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/data/tournois"
mkdir -p "$OUT_DIR"

ENDPOINT="https://tenup.fft.fr/back/public/v1/tournois"
NOW=$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")
IN_3_MONTHS=$(date -u -v+3m +"%Y-%m-%dT%H:%M:%S.000Z" 2>/dev/null || date -u -d "+3 months" +"%Y-%m-%dT%H:%M:%S.000Z")
SIZE=50
FROM=0
ALL_CARDS="[]"

while :; do
  BODY=$(jq -n --arg from "$FROM" --arg size "$SIZE" --arg debut "$NOW" --arg fin "$IN_3_MONTHS" '{
    pratique: "PICKLE", from: ($from|tonumber), size: ($size|tonumber),
    lat: 46.603354, lng: 1.888334, distance: 1000000,
    type: [], codeClub: null, ligues: [], comites: [],
    dateDebut: $debut, dateFin: $fin, utiliserMesDonnees: false,
    naturesEpreuves: [], typesEpreuves: [], naturesTerrains: [],
    categoriesJeu: [], categoriesAge: [], familles: [], tournoiInterne: false,
    classements: [], inscriptionEnLigne: null, paiementEnLigne: null,
    filtres: true, sort: "DATE_DEBUT"
  }')

  # -f: fail on HTTP errors instead of overwriting latest.json with an empty list
  RESP=$(curl -sf -X POST "$ENDPOINT" \
    -H 'Content-Type: application/json' \
    -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36' \
    -H 'Origin: https://tenup.fft.fr' \
    -H 'Referer: https://tenup.fft.fr/' \
    -d "$BODY")

  CARDS=$(echo "$RESP" | jq '.cards // []')
  TOTAL=$(echo "$RESP" | jq '.nbResultats // 0')
  ALL_CARDS=$(jq -s '.[0] + .[1]' <(echo "$ALL_CARDS") <(echo "$CARDS"))

  FROM=$((FROM + SIZE))
  [ "$FROM" -ge "$TOTAL" ] && break
done

OUT_FILE="$OUT_DIR/latest.json"
echo "$ALL_CARDS" | jq '.' > "$OUT_FILE"

echo "$(jq 'length' <<<"$ALL_CARDS") tournois sauvegardés dans $OUT_FILE"
