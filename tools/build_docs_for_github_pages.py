from __future__ import annotations

import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def sync_tree(src: Path, dst: Path) -> None:
    """
    Best-effort "rsync": copy src -> dst without needing to delete dst first.

    This is intentionally tolerant because OneDrive/browser processes can keep files
    open on Windows, causing rmtree/unlink to fail.
    """
    dst.mkdir(parents=True, exist_ok=True)
    for p in src.rglob("*"):
        rel = p.relative_to(src)
        out = dst / rel
        if p.is_dir():
            out.mkdir(parents=True, exist_ok=True)
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, out)


def write(p: Path, s: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8", newline="\n")


def patch_text(p: Path, reps: list[tuple[str, str]]) -> None:
    txt = p.read_text(encoding="utf-8")
    for a, b in reps:
        txt = txt.replace(a, b)
    p.write_text(txt, encoding="utf-8", newline="\n")


def main() -> int:
    # Build in-place (best-effort). Avoid deleting docs/ first: on Windows+OneDrive
    # folders can be locked by a running browser tab or sync process.
    DOCS.mkdir(parents=True, exist_ok=True)

    # Core folders
    sync_tree(ROOT / "07_LIVRO_BY_NIGHT", DOCS / "book")
    sync_tree(ROOT / "06_MAPA_SP", DOCS / "map")
    (DOCS / "map" / "data").mkdir(parents=True, exist_ok=True)
    # Ensure geojson exists under map/data (some tooling expects it).
    src_geo = ROOT / "06_MAPA_SP" / "data" / "distritos-sp.geojson"
    if src_geo.exists():
        shutil.copyfile(src_geo, DOCS / "map" / "data" / "distritos-sp.geojson")

    # Teia: copy html + fallback images
    (DOCS / "teia").mkdir(parents=True, exist_ok=True)
    for name in ["teia_de_conexoes_mapa.html", "teia_de_conexoes_mapa.png", "teia_de_conexoes_mapa.svg"]:
        src = ROOT / "01_BACKGROUND_NARRADOR" / name
        if src.exists():
            shutil.copyfile(src, DOCS / "teia" / name)

    # Portrait assets (the book/map/teia will use this path)
    (DOCS / "assets" / "portraits").mkdir(parents=True, exist_ok=True)
    for png in (ROOT / "05_ASSETS" / "portraits").glob("*.png"):
        shutil.copyfile(png, DOCS / "assets" / "portraits" / png.name)

    # No Jekyll (avoid underscore issues)
    write(DOCS / ".nojekyll", "")

    # Root index redirects to the book
    write(
        DOCS / "index.html",
        """<!doctype html>
<html lang="pt-br">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Sao Paulo by Night</title>
  <meta http-equiv="refresh" content="0; url=book/index.html" />
  <style>body{font:14px/1.4 system-ui,Segoe UI,Roboto,Arial; padding:24px} a{color:#0b62d6}</style>
</head>
<body>
  <p>Redirecionando para o livro...</p>
  <p><a href="book/index.html">Abrir agora</a></p>
  <script>location.replace('book/index.html');</script>
</body>
</html>
""",
    )

    # Patch paths for docs layout
    reps_book = [
        ("../05_ASSETS/portraits/", "../assets/portraits/"),
        ("../06_MAPA_SP/mapa_sp_dominios.html", "../map/mapa_sp_dominios.html"),
        ("../01_BACKGROUND_NARRADOR/teia_de_conexoes_mapa.html", "../teia/teia_de_conexoes_mapa.html"),
    ]
    patch_text(DOCS / "book" / "index.html", reps_book)
    patch_text(DOCS / "book" / "book.js", [("../05_ASSETS/portraits/", "../assets/portraits/")])

    reps_map = [
        ("../05_ASSETS/portraits/", "../assets/portraits/"),
    ]
    patch_text(DOCS / "map" / "mapa_sp_dominios.html", reps_map)

    reps_teia = [
        ("../05_ASSETS/portraits/", "../assets/portraits/"),
    ]
    patch_text(DOCS / "teia" / "teia_de_conexoes_mapa.html", reps_teia)

    print("[pages] built docs/ for GitHub Pages")
    print("[pages] entry: docs/index.html -> docs/book/index.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
