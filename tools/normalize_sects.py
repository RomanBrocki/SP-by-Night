import json
import os


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SOURCE_JSON = os.path.join(ROOT, "tools", "sp_by_night_source.json")


CANON_SECTS = {
    "Camarilla",
    "Anarch",
    "Independentes",
    "Autarquicos",
    "Zona cinza",
    "Segunda Inquisicao",
    "Sabbat",
    "Lobisomens",
}


def _master_id_from_links(e: dict) -> str | None:
    for l in e.get("links") or []:
        if l.get("type") == "servant" and l.get("to"):
            return l["to"]
    return None


def main() -> int:
    with open(SOURCE_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    entities = data.get("entities") or []
    by_id = {e["id"]: e for e in entities}

    changed = 0
    for e in entities:
        kind = e.get("kind")
        sect = (e.get("sect") or "").strip()

        # Normalize typos/variants
        if sect == "Autarquico":
            e["sect"] = "Autarquicos"
            changed += 1
            sect = "Autarquicos"

        if kind == "ghoul":
            mid = _master_id_from_links(e)
            if mid and mid in by_id:
                msect = (by_id[mid].get("sect") or "").strip()
                if msect:
                    if e.get("sect") != msect:
                        e["sect"] = msect
                        changed += 1
            else:
                # If unknown, keep to a neutral bucket (still useful for filtering).
                if sect and sect not in CANON_SECTS:
                    e["sect"] = "Mortal"
                    changed += 1

        if kind == "mortal":
            # Collapse verbose labels to a stable faction.
            if "lumen" in sect.lower() or "inquisi" in sect.lower():
                if e.get("sect") != "Segunda Inquisicao":
                    e["sect"] = "Segunda Inquisicao"
                    changed += 1
            else:
                if e.get("sect") not in ("Mortal", "Segunda Inquisicao"):
                    e["sect"] = "Mortal"
                    changed += 1

    if changed:
        with open(SOURCE_JSON, "w", encoding="utf-8", newline="\n") as wf:
            json.dump(data, wf, ensure_ascii=False, indent=2)
            wf.write("\n")

    print(f"[normalize_sects] changed={changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

