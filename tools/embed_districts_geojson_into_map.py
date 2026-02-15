import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "06_MAPA_SP" / "mapa_sp_dominios.html"
GEO = ROOT / "06_MAPA_SP" / "data" / "distritos-sp.geojson"


def main() -> int:
    if not HTML.exists():
        raise SystemExit(f"missing {HTML}")
    if not GEO.exists():
        raise SystemExit(f"missing {GEO}")

    html = HTML.read_text(encoding="utf-8")
    geo = json.loads(GEO.read_text(encoding="utf-8"))
    geo_js = json.dumps(geo, ensure_ascii=False)

    # Insert const DISTRICTS_GEOJSON near loadDistrictGeojson, once.
    if "const DISTRICTS_GEOJSON =" not in html:
        m = re.search(r"\n\s*async function loadDistrictGeojson\(\)\s*\{", html)
        if not m:
            raise SystemExit("could not find loadDistrictGeojson()")
        insert_at = m.start()
        html = html[:insert_at] + f"\n  const DISTRICTS_GEOJSON = {geo_js};\n" + html[insert_at:]

    # Replace the fetch block with direct usage, keeping try/catch.
    html = re.sub(
        r"(\s*)const r = await fetch\('data/distritos-sp\.geojson'\);\s*\n\s*const gj = await r\.json\(\);\s*",
        r"\1const gj = DISTRICTS_GEOJSON;\n",
        html,
        flags=re.M,
    )

    HTML.write_text(html, encoding="utf-8")
    print(f"embedded districts geojson into {HTML}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

