import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


REPL = {
    # Kindred domains moved to explicit territories
    "Centro Expandido (mobilidade)": "Santana/Tucuruvi (Xerifado; base de pressao e resposta)",
    "Centro Expandido (refugios dispersos)": "Butanta/USP (Torre Tremere; refugios dispersos)",
    "Centro/Paulista (salas privadas)": "Bela Vista/Bixiga (Confissao; salas privadas)",
    # Helena's satelite Elysium is explicit
    "Paulista (Elysium)": "Liberdade (Elysium satelite)",
}


EXTS = {".md", ".txt", ".yml", ".yaml", ".dot", ".html", ".svg"}


def should_touch(p: Path) -> bool:
    if p.suffix.lower() not in EXTS:
        return False
    # Avoid rewriting the huge map HTML (it is regenerated from sources).
    if p.name == "mapa_sp_dominios.html":
        return False
    return True


def main() -> int:
    changed = 0
    scanned = 0
    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue
        if not should_touch(p):
            continue
        try:
            before = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # Some generated assets may not be UTF-8; skip.
            continue
        scanned += 1
        after = before
        for a, b in REPL.items():
            after = after.replace(a, b)
        if after != before:
            p.write_text(after, encoding="utf-8")
            changed += 1
    print(f"scanned={scanned} changed={changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
