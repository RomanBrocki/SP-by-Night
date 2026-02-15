import re
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def parse_rede_cainita(path: Path) -> dict[str, str]:
    # Minimal YAML-ish parse: the file structure is stable (id: "...", domain: "...").
    text = path.read_text(encoding="utf-8", errors="replace").splitlines()
    cur_id = None
    out: dict[str, str] = {}
    for line in text:
        m = re.match(r'\s*-\s+id:\s*"([^"]+)"\s*$', line)
        if m:
            cur_id = m.group(1).strip()
            continue
        m = re.match(r'\s*domain:\s*"([^"]*)"\s*$', line)
        if m and cur_id:
            out[cur_id] = m.group(1)
    return out


def history_domain_for_kindred(kindred_id: str, src_entities: dict[str, dict]) -> str | None:
    e = src_entities.get(kindred_id)
    if not e:
        return None
    clan = e.get("clan") or "Unknown"
    stem = e.get("file_stem") or ""
    if not stem:
        return None
    p = ROOT / "02_NPCS" / clan.replace(" ", "_").replace("-", "_").replace("/", "_") / f"{stem}_historia.txt"
    if not p.exists():
        return None
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        # Example: "- Dominio: X | Idade aparente: 42"
        if line.strip().startswith("- Dominio:"):
            s = line.split(":", 1)[1].strip()
            return s.split("|", 1)[0].strip()
    return None


def main() -> int:
    src_path = ROOT / "tools" / "sp_by_night_source.json"
    rede_path = ROOT / "01_BACKGROUND_NARRADOR" / "data" / "rede_cainita.yml"
    if not src_path.exists():
        raise SystemExit(f"missing {src_path}")
    src = read_json(src_path)
    entities = [e for e in (src.get("entities") or []) if isinstance(e, dict)]
    by_id = {e.get("id"): e for e in entities if e.get("id")}

    mismatches: list[str] = []

    if rede_path.exists():
        rede = parse_rede_cainita(rede_path)
        for e in entities:
            if e.get("kind") != "kindred":
                continue
            eid = e.get("id")
            want = (e.get("domain") or "").strip()
            got = (rede.get(eid) or "").strip()
            if got and want and got != want:
                mismatches.append(f"rede_cainita.yml domain mismatch for {eid}: rede='{got}' src='{want}'")

    # Check per-NPC history header domains
    for e in entities:
        if e.get("kind") != "kindred":
            continue
        eid = e.get("id")
        want = (e.get("domain") or "").strip()
        got = history_domain_for_kindred(eid, by_id)
        if got and want and got != want:
            mismatches.append(f"NPC historia domain mismatch for {eid}: historia='{got}' src='{want}'")

    if mismatches:
        print("MISMATCHES:")
        for m in mismatches:
            print("-", m)
        return 2
    print("OK: domains coherent across source, rede_cainita.yml, and NPC history headers (where present).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

