import json
import time
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "tools" / "sp_map_places_seed.json"
OUT = ROOT / "tools" / "sp_map_config.json"
CACHE = ROOT / "tools" / "sp_map_geocode_cache.json"


def http_get_json(url: str, headers: dict) -> object:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read()
    return json.loads(data.decode("utf-8"))


def geocode(q: str, cache: dict, headers: dict) -> dict:
    key = q.strip()
    if key in cache:
        return cache[key]
    params = {"format": "json", "q": key, "limit": 1}
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(params)
    res = http_get_json(url, headers=headers)
    if not res:
        raise SystemExit(f"Geocode failed (no results) for: {q}")
    hit = res[0]
    out = {
        "lat": float(hit["lat"]),
        "lon": float(hit["lon"]),
        "display_name": hit.get("display_name", ""),
    }
    cache[key] = out
    return out


def main() -> None:
    seed = json.loads(SEED.read_text(encoding="utf-8"))
    cache = {}
    if CACHE.exists():
        cache = json.loads(CACHE.read_text(encoding="utf-8"))

    # Nominatim usage policy wants a descriptive User-Agent.
    headers = {"User-Agent": "SPByNightMap/1.0 (local generator; contact: none)"}

    zones_out = []
    for z in seed.get("geo_zones", []):
        g = geocode(z["search"], cache, headers=headers)
        zones_out.append(
            {
                "id": z["id"],
                "name": z["name"],
                "faction": z.get("faction", ""),
                "center": {"lat": g["lat"], "lon": g["lon"]},
                "radius_m": int(z.get("radius_m", 5000)),
                "notes": z.get("notes", ""),
                "search": z["search"],
            }
        )
        time.sleep(1.0)

    domains_out = []
    for d in seed.get("domains", []):
        g = geocode(d["search"], cache, headers=headers)
        domains_out.append(
            {
                "id": d["id"],
                "name": d["name"],
                "center": {"lat": g["lat"], "lon": g["lon"]},
                "radius_m": int(d.get("radius_m", 2500)),
                "keywords": list(d.get("keywords", [])),
                "faction": d.get("faction", ""),
                "search": d["search"],
            }
        )
        time.sleep(1.0)

    pois_out = []
    for p in seed.get("pois", []):
        g = geocode(p["search"], cache, headers=headers)
        pois_out.append(
            {
                "id": p["id"],
                "name": p["name"],
                "lat": g["lat"],
                "lon": g["lon"],
                "domain_id": p.get("domain_id", ""),
                "kind": p.get("kind", "poi"),
                "notes": p.get("notes", ""),
                "search": p["search"],
            }
        )
        time.sleep(1.0)

    cfg = {
        "meta": seed.get("meta", {}),
        "geo_zones": zones_out,
        "domains": domains_out,
        "pois": pois_out,
    }
    OUT.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("OK: wrote", OUT)


if __name__ == "__main__":
    main()
