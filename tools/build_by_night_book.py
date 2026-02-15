from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

SRC = ROOT / "tools" / "sp_by_night_source.json"
CLAIMS = ROOT / "tools" / "sp_district_claims.json"
DISTRICTS = ROOT / "06_MAPA_SP" / "data" / "distritos-sp.geojson"

OUT_DIR = ROOT / "07_LIVRO_BY_NIGHT"
OUT_DATA = OUT_DIR / "book_data.json"
OUT_MAP_SVG = OUT_DIR / "mapa_macro_faccoes.svg"
OUT_HTML = OUT_DIR / "index.html"
OUT_CSS = OUT_DIR / "book.css"
OUT_JS = OUT_DIR / "book.js"


def die(msg: str) -> None:
    raise SystemExit(msg)


def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8").replace("\r\n", "\n")


def safe_id(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"[^a-z0-9_\-]+", "-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s or "sec"


def html_escape(s: str) -> str:
    s = s or ""
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def md_to_html(md: str) -> str:
    """
    Minimal markdown-ish renderer: headings, bullet lists, numbered lists, paragraphs.
    Keeps things readable without external dependencies.
    """
    md = (md or "").replace("\r\n", "\n")
    lines = md.splitlines()
    out: list[str] = []
    in_ul = False
    in_ol = False

    def close_lists() -> None:
        nonlocal in_ul, in_ol
        if in_ul:
            out.append("</ul>")
            in_ul = False
        if in_ol:
            out.append("</ol>")
            in_ol = False

    for raw in lines:
        line = raw.rstrip("\n")
        if not line.strip():
            close_lists()
            continue

        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            close_lists()
            lvl = len(m.group(1))
            txt = html_escape(m.group(2).strip())
            out.append(f"<h{lvl}>{txt}</h{lvl}>")
            continue

        m = re.match(r"^\s*[-*]\s+(.*)$", line)
        if m:
            if in_ol:
                out.append("</ol>")
                in_ol = False
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{html_escape(m.group(1).strip())}</li>")
            continue

        m = re.match(r"^\s*\d+\.\s+(.*)$", line)
        if m:
            if in_ul:
                out.append("</ul>")
                in_ul = False
            if not in_ol:
                out.append("<ol>")
                in_ol = True
            out.append(f"<li>{html_escape(m.group(1).strip())}</li>")
            continue

        close_lists()
        out.append(f"<p>{html_escape(line)}</p>")

    close_lists()
    return "\n".join(out)


def as_list(v: Any) -> list:
    return v if isinstance(v, list) else []


def macro_key(v: str) -> str:
    v = (v or "").lower()
    if "camar" in v:
        return "Camarilla"
    if "anarch" in v:
        return "Anarch"
    if "indep" in v or "autarqu" in v or "zona" in v:
        return "Independentes"
    if "segunda" in v or "inquis" in v:
        return "Segunda Inquisição"
    if "mortal" in v:
        return "Mortal"
    return v.strip().title() or "Outro"


@dataclass
class DistrictStyle:
    fill: str
    stroke: str
    stroke_width: float
    opacity: float
    dash: str | None = None
    hatch: bool = False


COLORS = {
    "Camarilla": "#f5c542",
    "Anarch": "#ff7a00",
    "Independentes": "#6f2dbd",
    "Contestado": "#ff0033",
    "Lupino": "#00b050",
    "NeutralStroke": "rgba(20, 24, 33, 0.65)",
}


def district_style(dominant: str, disputed: list[str]) -> DistrictStyle:
    dom = macro_key(dominant)
    fill = COLORS.get(dom, "#9aa0a6")
    stroke = "#0b0e13"
    sw = 0.65
    op = 0.62
    dash = None
    hatch = False
    if disputed:
        # Contested districts: stronger outline + hatch overlay pattern.
        sw = 1.2
        dash = "4 3"
        hatch = True
    return DistrictStyle(fill=fill, stroke=stroke, stroke_width=sw, opacity=op, dash=dash, hatch=hatch)


def iter_rings(geom: dict) -> list[list[list[float]]]:
    """Return a list of linear rings (list of [lon,lat]) for Polygon/MultiPolygon."""
    if not isinstance(geom, dict):
        return []
    t = geom.get("type")
    coords = geom.get("coordinates")
    if t == "Polygon" and isinstance(coords, list):
        return [ring for ring in coords if isinstance(ring, list)]
    if t == "MultiPolygon" and isinstance(coords, list):
        rings: list[list[list[float]]] = []
        for poly in coords:
            if not isinstance(poly, list):
                continue
            for ring in poly:
                if isinstance(ring, list):
                    rings.append(ring)
        return rings
    return []


def project_factory(features: list[dict]) -> tuple[float, float, float, float]:
    minlon = 1e9
    minlat = 1e9
    maxlon = -1e9
    maxlat = -1e9
    for ft in features:
        geom = ft.get("geometry") or {}
        for ring in iter_rings(geom):
            for pt in ring:
                if not (isinstance(pt, list) and len(pt) >= 2):
                    continue
                lon, lat = float(pt[0]), float(pt[1])
                minlon = min(minlon, lon)
                maxlon = max(maxlon, lon)
                minlat = min(minlat, lat)
                maxlat = max(maxlat, lat)
    if minlon > maxlon or minlat > maxlat:
        die("bounds not found in geojson")
    return minlon, minlat, maxlon, maxlat


def ring_to_path(ring: list[list[float]], minlon: float, minlat: float, maxlon: float, maxlat: float, w: float, h: float) -> str:
    if not ring:
        return ""
    rng_lon = (maxlon - minlon) or 1.0
    rng_lat = (maxlat - minlat) or 1.0

    def xy(lon: float, lat: float) -> tuple[float, float]:
        x = (lon - minlon) / rng_lon * w
        # Flip y so north is up.
        y = (maxlat - lat) / rng_lat * h
        return x, y

    cmds: list[str] = []
    first = True
    for pt in ring:
        if not (isinstance(pt, list) and len(pt) >= 2):
            continue
        lon, lat = float(pt[0]), float(pt[1])
        x, y = xy(lon, lat)
        if first:
            cmds.append(f"M {x:.2f} {y:.2f}")
            first = False
        else:
            cmds.append(f"L {x:.2f} {y:.2f}")
    if not cmds:
        return ""
    cmds.append("Z")
    return " ".join(cmds)


def build_macro_svg(districts_geojson: dict, claims: dict) -> str:
    feats = as_list(districts_geojson.get("features"))
    dom_raw = (claims.get("dominant") or {}) if isinstance(claims, dict) else {}
    disputes_raw = (claims.get("disputes") or {}) if isinstance(claims, dict) else {}

    minlon, minlat, maxlon, maxlat = project_factory(feats)
    w, h = 1000.0, 820.0

    def dk(name: str) -> str:
        name = (name or "").strip().lower()
        name = re.sub(r"\s+", " ", name)
        return name

    # Normalize claim keys to match the same canonicalization used for geojson district names.
    dom = {dk(str(k)): v for k, v in (dom_raw.items() if isinstance(dom_raw, dict) else [])}
    disputes = {dk(str(k)): v for k, v in (disputes_raw.items() if isinstance(disputes_raw, dict) else [])}

    # Precompute district paths
    pieces: list[str] = []

    # Hatch pattern for contested districts
    pieces.append(
        """
<defs>
  <pattern id="hatch" width="10" height="10" patternUnits="userSpaceOnUse" patternTransform="rotate(20)">
    <line x1="0" y1="0" x2="0" y2="10" stroke="rgba(0,0,0,0.45)" stroke-width="2"/>
  </pattern>
</defs>
""".strip()
    )

    # Background
    pieces.append(f'<rect x="0" y="0" width="{w:.0f}" height="{h:.0f}" fill="#0b0e13" />')

    for ft in feats:
        props = ft.get("properties") or {}
        name = props.get("ds_nome") or props.get("name") or ""
        dkey = dk(str(name))
        dominant = dom.get(dkey) or "Camarilla"
        disputed = disputes.get(dkey) or None
        between: list[str] = []
        if isinstance(disputed, dict):
            between = as_list(disputed.get("between"))
        style = district_style(dominant, between)

        geom = ft.get("geometry") or {}
        rings = iter_rings(geom)
        if not rings:
            continue

        # Build one path per ring; overlay hatch if contested.
        path_d = " ".join(
            [ring_to_path(r, minlon, minlat, maxlon, maxlat, w, h) for r in rings if r]
        ).strip()
        if not path_d:
            continue

        title_lines = [str(name).strip() or "(sem nome)"]
        title_lines.append(f"Dominante: {macro_key(str(dominant))}")
        if between:
            title_lines.append("Disputa: " + " vs ".join(macro_key(x) for x in between))
        title = html_escape(" | ".join(title_lines))
        dom_txt = html_escape(macro_key(str(dominant)))
        dis_txt = html_escape(" vs ".join(macro_key(x) for x in between)) if between else ""

        dash = f' stroke-dasharray="{style.dash}"' if style.dash else ""
        pieces.append(
            f'<path d="{path_d}" fill="{style.fill}" fill-opacity="{style.opacity}" '
            f'stroke="{style.stroke}" stroke-width="{style.stroke_width}"{dash} '
            f'data-district="{html_escape(str(name))}" data-dominant="{dom_txt}" data-dispute="{dis_txt}">'
            f"<title>{title}</title></path>"
        )
        if style.hatch:
            pieces.append(
                f'<path d="{path_d}" fill="url(#hatch)" fill-opacity="0.28" stroke="none" pointer-events="none"></path>'
            )

    # Outline frame
    pieces.append(f'<rect x="8" y="8" width="{w-16:.0f}" height="{h-16:.0f}" fill="none" stroke="rgba(245,245,250,0.18)" stroke-width="2" />')

    svg = "\n".join(pieces)
    return f'<svg viewBox="0 0 {w:.0f} {h:.0f}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Mapa macro por faccoes">{svg}</svg>'


def gather_files() -> dict[str, str]:
    files: dict[str, str] = {}

    def add_dir(prefix: str, p: Path) -> None:
        if not p.exists():
            return
        for f in sorted(p.glob("*.md")):
            files[f"{prefix}/{f.name}"] = read_text(f)

    # Player-facing
    add_dir("jogadores", ROOT / "00_BACKGROUND_JOGADORES")
    # Storyteller
    add_dir("narrador", ROOT / "01_BACKGROUND_NARRADOR")
    add_dir("narrador/faccoes", ROOT / "01_BACKGROUND_NARRADOR" / "faccoes")

    # Antagonists
    add_dir("antagonistas", ROOT / "04_ANTAGONISTAS_V5")

    # Clan structures
    clan_root = ROOT / "02_NPCS"
    for clan_dir in sorted([d for d in clan_root.iterdir() if d.is_dir()]):
        f = clan_dir / "estrutura_do_cla.md"
        if f.exists():
            files[f"clas/{clan_dir.name}/estrutura_do_cla.md"] = read_text(f)

    return files


def canonical_entity_dir(e: dict) -> Path | None:
    kind = (e.get("kind") or "kindred").lower()
    stem = e.get("file_stem") or ""
    if not stem:
        return None
    if kind == "kindred":
        clan = (e.get("clan") or "Sem_Cla").replace(" ", "_")
        return ROOT / "02_NPCS" / clan
    if kind == "ghoul":
        return ROOT / "03_SERVOS_E_CONTATOS" / "ghouls"
    if kind == "mortal":
        return ROOT / "03_SERVOS_E_CONTATOS" / "mortais_influentes"
    return None


def read_entity_docs(e: dict) -> dict[str, Any]:
    stem = e.get("file_stem") or ""
    base = canonical_entity_dir(e)
    if not base or not base.exists() or not stem:
        return {"files": {}, "paths": {}}

    files: dict[str, str] = {}
    paths: dict[str, str] = {}

    def try_read(suffix: str, key: str) -> None:
        p = base / f"{stem}{suffix}"
        if p.exists():
            files[key] = read_text(p)
            paths[key] = str(p.relative_to(ROOT)).replace("\\", "/")

    try_read("_ficha_resumida.txt", "ficha_resumida")
    try_read("_historia.txt", "historia")
    try_read("_ficha_completa.md", "ficha_completa")
    return {"files": files, "paths": paths}


def build_data() -> dict[str, Any]:
    if not SRC.exists():
        die(f"missing {SRC}")
    src = json.loads(SRC.read_text(encoding="utf-8"))
    entities = as_list(src.get("entities"))
    by_id = {e.get("id"): e for e in entities if isinstance(e, dict) and e.get("id")}

    kindred = [e for e in entities if (e.get("kind") or "kindred") == "kindred"]
    ghouls = [e for e in entities if e.get("kind") == "ghoul"]
    mortals = [e for e in entities if e.get("kind") == "mortal"]

    for e in entities:
        e["sect_norm"] = macro_key(str(e.get("sect") or ""))

    # In this project, servant links are modeled as: servant -> master (link.type === "servant").
    servant_to_masters: dict[str, set[str]] = {}
    for e in entities:
        if not isinstance(e, dict) or not e.get("id"):
            continue
        sid = e["id"]
        for lk in as_list(e.get("links")):
            if not isinstance(lk, dict):
                continue
            if (lk.get("type") or "").lower() != "servant":
                continue
            mid = lk.get("to")
            if mid and mid in by_id:
                servant_to_masters.setdefault(sid, set()).add(mid)

    # Build inverse: master -> servants.
    master_to_servants: dict[str, set[str]] = {}
    for sid, mids in servant_to_masters.items():
        for mid in mids:
            master_to_servants.setdefault(mid, set()).add(sid)

    # servant -> master clans (for filtering ghouls by clan in the book)
    servant_to_master_clans: dict[str, set[str]] = {}
    for sid, mids in servant_to_masters.items():
        for mid in mids:
            m = by_id.get(mid) or {}
            mclan = (m.get("clan") or "").strip()
            if mclan:
                servant_to_master_clans.setdefault(sid, set()).add(mclan)

    # coteries_all: include inferred coteries for ghouls that serve a coterie member.
    for e in entities:
        if not isinstance(e, dict) or not e.get("id"):
            continue
        direct = [x for x in as_list(e.get("coteries")) if isinstance(x, str) and x.strip()]
        inferred: set[str] = set()
        if (e.get("kind") or "").lower() == "ghoul":
            # inherit coteries of their masters
            for mid in sorted(servant_to_masters.get(e["id"], set())):
                me = by_id.get(mid) or {}
                for cid in as_list(me.get("coteries")):
                    if isinstance(cid, str) and cid.strip():
                        inferred.add(cid)
        e["coteries_all"] = sorted(set(direct) | inferred)
        if (e.get("kind") or "").lower() == "ghoul":
            e["serves_clans"] = sorted(servant_to_master_clans.get(e["id"], set()))

    # Coteries/associacoes: keep from source if present (already used in map),
    # but expand membership with "ghouls dos membros" when those ghouls have ficha files.
    coteries = as_list(src.get("coteries"))
    coteries_by_id: dict[str, dict] = {}
    for c in coteries:
        if not isinstance(c, dict) or not c.get("id"):
            continue
        coteries_by_id[c["id"]] = c

    def ghoul_has_sheet(eid: str) -> bool:
        e = by_id.get(eid) or {}
        if (e.get("kind") or "").lower() != "ghoul":
            return False
        stem = e.get("file_stem") or ""
        if not stem:
            return False
        p = ROOT / "03_SERVOS_E_CONTATOS" / "ghouls" / f"{stem}_ficha_resumida.txt"
        return p.exists()

    for cid, c in coteries_by_id.items():
        members = [m for m in as_list(c.get("members")) if isinstance(m, str) and m.strip()]
        expanded = set(members)
        for mid in members:
            for sid in sorted(master_to_servants.get(mid, set())):
                if ghoul_has_sheet(sid):
                    expanded.add(sid)
        c["members_expanded"] = sorted(expanded)

    # Files
    files = gather_files()

    # Embed per-entity docs (ficha/historia/ficha completa) for click-to-open in the book.
    for e in entities:
        if not isinstance(e, dict) or not e.get("file_stem"):
            continue
        e["docs"] = read_entity_docs(e)

    return {
        "meta": {
            "title": "Sao Paulo by Night (V5) - Livro da Cronica",
            "chronicle_year": src.get("meta", {}).get("chronicle_year", 2035),
        },
        "counts": {
            "entities": len(entities),
            "kindred": len(kindred),
            "ghouls": len(ghouls),
            "mortals": len(mortals),
        },
        "entities": entities,
        "coteries": coteries,
        "coteries_by_id": coteries_by_id,
        "files": files,
        "paths": {
            "portraits_base": "../05_ASSETS/portraits/",
            "map_html": "../06_MAPA_SP/mapa_sp_dominios.html",
            "teia_html": "../01_BACKGROUND_NARRADOR/teia_de_conexoes_mapa.html",
        },
    }


def write_assets() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if not CLAIMS.exists():
        die(f"missing {CLAIMS}")
    if not DISTRICTS.exists():
        die(f"missing {DISTRICTS}")
    claims = json.loads(CLAIMS.read_text(encoding="utf-8"))
    districts = json.loads(DISTRICTS.read_text(encoding="utf-8"))
    OUT_MAP_SVG.write_text(build_macro_svg(districts, claims), encoding="utf-8", newline="\n")


def write_book_files(data: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    css = """
:root{
  --bg:#0c0c10;
  --panel:#14141b;
  --text:#e9e9ef;
  --muted:#a7a7b3;
  --border:rgba(255,255,255,0.10);
  --accent:#e3c26b;
  --shadow: rgba(0,0,0,0.45);
  --chip: rgba(255,255,255,0.06);
}
*{ box-sizing:border-box; }
body{ margin:0; background: radial-gradient(1200px 800px at 20% 10%, #151525, var(--bg)); color:var(--text); font: 14px/1.5 ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial; }
a{ color: var(--accent); text-decoration:none; }
a:hover{ text-decoration:underline; }
.wrap{ display:grid; grid-template-columns: 360px 1fr; height:100vh; }
.side{ border-right:1px solid var(--border); background: linear-gradient(180deg, rgba(255,255,255,0.03), transparent); padding:16px; overflow:auto; }
.main{ position:relative; overflow:auto; }
h1{ margin:0 0 8px; font-size:18px; }
.hint{ color:var(--muted); margin: 0 0 12px; }
.sec{ border:1px solid var(--border); background: var(--panel); border-radius: 12px; padding:12px; margin:12px 0; box-shadow: 0 18px 40px var(--shadow); }
.sec h2{ margin:0 0 8px; font-size:14px; color:var(--accent); letter-spacing:0.02em; }
input[type="text"]{ width:100%; padding:8px 10px; border-radius:10px; border:1px solid var(--border); background: rgba(0,0,0,0.25); color: var(--text); }
button{ padding:8px 10px; border-radius: 10px; border:1px solid var(--border); background: rgba(255,255,255,0.06); color: var(--text); cursor:pointer; }
button:hover{ background: rgba(255,255,255,0.10); }
.toc a{ display:block; padding:6px 8px; border-radius: 10px; border:1px solid transparent; }
.toc a:hover{ border-color: var(--border); background: rgba(255,255,255,0.04); }
.chips{ display:flex; flex-wrap:wrap; gap:8px; }
.chip{ display:inline-flex; gap:8px; align-items:center; padding:6px 10px; border:1px solid var(--border); border-radius: 999px; background: rgba(0,0,0,0.20); }
.chip input{ transform: translateY(1px); }
.content{ max-width: 1100px; margin: 0 auto; padding: 18px 18px 48px 18px; }
.kicker{ color: var(--muted); font-size: 12px; }
.hero{ display:grid; grid-template-columns: 1fr; gap: 12px; }
.heroGrid{ display:grid; grid-template-columns: 1.3fr 1fr; gap: 14px; align-items:start; }
@media (max-width: 980px){ .wrap{ grid-template-columns: 1fr; } .side{ border-right:0; border-bottom:1px solid var(--border); } .heroGrid{ grid-template-columns: 1fr; } }
.mapBox{ border:1px solid var(--border); border-radius: 14px; padding: 10px; background: rgba(0,0,0,0.22); }
.mapBox svg{ width:100%; height:auto; display:block; }
.gridCards{ display:grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
@media (max-width: 1100px){ .gridCards{ grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 700px){ .gridCards{ grid-template-columns: 1fr; } }
.card{ border:1px solid var(--border); background: rgba(0,0,0,0.18); border-radius: 14px; overflow:hidden; }
.cardHead{ display:flex; gap:10px; padding: 10px; align-items:center; }
.portrait{ width: 64px; height: 64px; border-radius: 12px; overflow:hidden; border:1px solid rgba(238,241,247,0.18); background: rgba(0,0,0,0.25); flex: 0 0 auto; }
.portrait img{ width:100%; height:100%; object-fit:cover; display:block; }
.cardTitle{ font-weight: 700; }
.cardMeta{ color: var(--muted); font-size: 12px; line-height: 1.35; }
.cardBody{ padding: 0 10px 10px; white-space: pre-wrap; color: rgba(233,233,239,0.92); }
.mono{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }
.md h1,.md h2,.md h3,.md h4{ margin: 14px 0 8px; }
.md p{ margin: 8px 0; }
.md ul,.md ol{ margin: 8px 0 8px 18px; }
.md li{ margin: 3px 0; }
.embedRow{ display:flex; gap: 10px; flex-wrap: wrap; }
.embedRow a{ padding: 8px 10px; border:1px solid var(--border); border-radius: 10px; background: rgba(255,255,255,0.06); }
.embed{ width: 100%; height: 680px; border: 1px solid var(--border); border-radius: 14px; background: rgba(0,0,0,0.20); }
.mapTip{
  position:absolute;
  z-index: 50;
  pointer-events:none;
  display:none;
  max-width: 340px;
  padding: 8px 10px;
  border-radius: 12px;
  border: 1px solid rgba(255,255,255,0.12);
  background: rgba(20,20,27,0.96);
  box-shadow: 0 18px 46px var(--shadow);
  color: var(--text);
  font-size: 12px;
  line-height: 1.35;
}
.mapTip .t{ font-weight: 700; color: var(--accent); margin-bottom: 4px; }
.mapBox{ position: relative; }
.mapBox svg path{ cursor: help; }

/* Modal */
.modalWrap{
  position: fixed; inset: 0;
  display:none;
  align-items: center;
  justify-content: center;
  padding: 18px;
  background: rgba(0,0,0,0.78);
  z-index: 9999;
}
.modal{
  width: min(1040px, 96vw);
  max-height: min(86vh, 900px);
  overflow: auto;
  border: 1px solid var(--border);
  border-radius: 14px;
  background: rgba(12, 13, 18, 0.98);
  box-shadow: 0 30px 80px rgba(0,0,0,0.70);
}
.modalHead{
  position: sticky; top: 0;
  display:flex; gap: 10px; align-items:center; justify-content: space-between;
  padding: 12px 12px;
  background: rgba(12,12,16,0.98);
  border-bottom: 1px solid var(--border);
}
.modalHead .ttl{ font-weight: 800; }
.modalBody{ padding: 12px; }
.twoCol{ display:grid; grid-template-columns: 320px 1fr; gap: 12px; align-items:start; }
@media (max-width: 900px){ .twoCol{ grid-template-columns: 1fr; } }
.bigPortrait{ width: 100%; height: 360px; border-radius: 14px; overflow:hidden; border:1px solid rgba(238,241,247,0.18); background: rgba(0,0,0,0.25); }
.bigPortrait img{ width:100%; height:100%; object-fit:cover; display:block; }
.kv{ color: var(--muted); font-size: 12px; margin-top: 8px; white-space: pre-wrap; }
.blk{ border:1px solid var(--border); border-radius: 14px; padding: 10px; background: rgba(0,0,0,0.20); margin: 10px 0; }
.blk h3{ margin:0 0 6px; font-size: 13px; color: var(--accent); }
.blk pre{ margin:0; white-space: pre-wrap; }
""".strip() + "\n"
    OUT_CSS.write_text(css, encoding="utf-8", newline="\n")

    js = """
const state = {
  data: null,
  filters: {
    sect: new Set(),
    clan: new Set(),
    kind: new Set(),
    coterie: new Set(),
    q: '',
  }
};

function el(id){ return document.getElementById(id); }

function uniq(arr){ return Array.from(new Set(arr)); }

function norm(s){
  return String(s||'').toLowerCase().normalize('NFD').replace(/\\p{Diacritic}/gu,'');
}

function portraitSrc(stem){
  if(!stem) return '';
  return (state.data?.paths?.portraits_base || '../05_ASSETS/portraits/') + stem + '.png?v=' + (window.__PORTRAIT_V || Date.now());
}

function buildChips(id, values, labelFn){
  const box = el(id);
  box.innerHTML = '';
  values.forEach(v => {
    const lab = document.createElement('label');
    lab.className = 'chip';
    const cb = document.createElement('input');
    cb.type = 'checkbox';
    cb.value = v;
    cb.addEventListener('change', () => {
      const set = state.filters[id === 'chipsSect' ? 'sect' : id === 'chipsClan' ? 'clan' : id === 'chipsCoterie' ? 'coterie' : 'kind'];
      if(cb.checked) set.add(v); else set.delete(v);
      renderNpcCards();
    });
    const sp = document.createElement('span');
    sp.textContent = labelFn ? labelFn(v) : v;
    lab.appendChild(cb);
    lab.appendChild(sp);
    box.appendChild(lab);
  });
}

function matchesFilters(e){
  const f = state.filters;
  if(f.kind.size && !f.kind.has(e.kind || 'kindred')) return false;
  if(f.sect.size && !f.sect.has(e.sect_norm || e.sect || '')) return false;
  if(f.clan.size){
    if((e.kind||'kindred') === 'kindred'){
      if(!f.clan.has(e.clan || '')) return false;
    } else if((e.kind||'') === 'ghoul'){
      const sc = Array.isArray(e.serves_clans) ? e.serves_clans : [];
      if(!sc.some(x => f.clan.has(x))) return false;
    } else {
      // mortals without a clan are excluded when clan filter is active
      return false;
    }
  }
  if(f.coterie.size){
    const cs = Array.isArray(e.coteries_all) ? e.coteries_all : (Array.isArray(e.coteries) ? e.coteries : []);
    if(!cs.some(x => f.coterie.has(x))) return false;
  }
  const q = norm(f.q);
  if(q){
    const hay = norm([e.display_name, e.role, e.domain, e.sect, e.clan, e.signature_style].filter(Boolean).join(' '));
    if(!hay.includes(q)) return false;
  }
  return true;
}

function openModalForEntity(e){
  const wrap = el('modalWrap');
  wrap.style.display = 'flex';
  el('modalTitle').textContent = (e.display_name || e.id || 'NPC');

  const img = el('modalImg');
  img.style.display = 'block';
  img.alt = e.display_name || '';
  img.src = portraitSrc(e.file_stem);
  img.onerror = () => { img.style.display = 'none'; };

  const metaLines = [];
  metaLines.push((e.kind || 'kindred') + (e.clan ? ' · ' + e.clan : '') + (e.sect ? ' · ' + e.sect : ''));
  if(e.role) metaLines.push('Papel: ' + e.role);
  if(e.domain) metaLines.push('Domínio/Área: ' + e.domain);
  if(e.tier) metaLines.push('Tier: ' + e.tier);
  if(e.appearance_explicit) metaLines.push('Aparência: ' + e.appearance_explicit);
  const cs = Array.isArray(e.coteries_all) ? e.coteries_all : (Array.isArray(e.coteries) ? e.coteries : []);
  if(cs.length){
    const nm = (cid) => {
      const meta = (state.data?.coteries || []).find(x => x && x.id === cid) || null;
      return meta ? (meta.name || cid) : cid;
    };
    metaLines.push('Coteries/associações: ' + cs.map(nm).join(', '));
  }
  el('modalMeta').textContent = metaLines.join('\\n');

  el('modalPrompt').textContent = (e.portrait_prompt || '(sem prompt)');

  const docs = (e.docs && e.docs.files) ? e.docs.files : {};
  el('modalResumo').textContent = docs.ficha_resumida || '(sem ficha resumida)';
  el('modalHistoria').textContent = docs.historia || '(sem história)';
  el('modalCompleta').textContent = docs.ficha_completa || '(sem ficha completa em arquivo)';

  const fs = e.full_sheet || null;
  el('modalFullSheet').textContent = fs ? JSON.stringify(fs, null, 2) : '(sem ficha completa estruturada)';

  const paths = (e.docs && e.docs.paths) ? e.docs.paths : {};
  const lines = [];
  Object.entries(paths).forEach(([k,v]) => lines.push(k + ': ' + v));
  el('modalPaths').textContent = lines.length ? lines.join('\\n') : '(sem caminhos)';
}

function closeModal(){
  el('modalWrap').style.display = 'none';
}

function applyCoterieFilter(cid){
  // Mark the chip and update state.
  const box = el('chipsCoterie');
  if(!box) return;
  // Clear other coteries for clarity.
  state.filters.coterie.clear();
  box.querySelectorAll('input[type=checkbox]').forEach(cb => {
    cb.checked = (cb.value === cid);
    if(cb.checked) state.filters.coterie.add(cid);
  });
  // Scroll to NPC section as a convenience.
  try { document.getElementById('sec-npcs')?.scrollIntoView({behavior:'smooth', block:'start'}); } catch(e) {}
  renderNpcCards();
}

function cardText(e){
  const lines = [];
  if(e.kind === 'kindred'){
    if(e.sect) lines.push('Seita: ' + e.sect);
    if(e.clan) lines.push('Clã: ' + e.clan);
    if(e.role) lines.push('Papel: ' + e.role);
    if(e.domain) lines.push('Domínio: ' + e.domain);
    if(e.tier) lines.push('Tier: ' + e.tier);
    if(e.sire) lines.push('Sire: ' + e.sire);
    if(Array.isArray(e.childer) && e.childer.length) lines.push('Cria: ' + e.childer.join(', '));
  } else {
    if(e.sect) lines.push('Vínculo: ' + e.sect);
    if(e.role) lines.push('Papel: ' + e.role);
    if(e.domain) lines.push('Área: ' + e.domain);
  }
  return lines.join('\\n');
}

function renderNpcCards(){
  const box = el('npcCards');
  const ents = (state.data?.entities || []).filter(matchesFilters);

  // stable sort: Kindred first, then by sect, then clan, then name
  ents.sort((a,b)=>{
    const ak = a.kind==='kindred' ? 0 : a.kind==='ghoul' ? 1 : 2;
    const bk = b.kind==='kindred' ? 0 : b.kind==='ghoul' ? 1 : 2;
    if(ak !== bk) return ak-bk;
    const as = String(a.sect_norm||a.sect||'');
    const bs = String(b.sect_norm||b.sect||'');
    if(as !== bs) return as.localeCompare(bs);
    const ac = String(a.clan||'');
    const bc = String(b.clan||'');
    if(ac !== bc) return ac.localeCompare(bc);
    return String(a.display_name||'').localeCompare(String(b.display_name||''));
  });

  box.innerHTML = '';
  const max = 240; // keep it snappy
  const list = ents.slice(0, max);
  list.forEach(e=>{
    const card = document.createElement('div');
    card.className = 'card';
    const head = document.createElement('div');
    head.className = 'cardHead';
    const p = document.createElement('div');
    p.className = 'portrait';
    const img = document.createElement('img');
    img.loading = 'lazy';
    img.alt = e.display_name || '';
    img.src = portraitSrc(e.file_stem);
    img.onerror = () => { img.style.display='none'; };
    p.appendChild(img);
    const meta = document.createElement('div');
    const t = document.createElement('div');
    t.className = 'cardTitle';
    t.textContent = e.display_name || e.id;
    const m = document.createElement('div');
    m.className = 'cardMeta';
    m.textContent = (e.kind || 'kindred') + (e.clan ? ' · ' + e.clan : '') + (e.sect ? ' · ' + e.sect : '');
    meta.appendChild(t);
    meta.appendChild(m);
    head.appendChild(p);
    head.appendChild(meta);
    const body = document.createElement('div');
    body.className = 'cardBody mono';
    body.textContent = cardText(e);
    card.appendChild(head);
    card.appendChild(body);
    card.addEventListener('click', ()=> openModalForEntity(e));
    box.appendChild(card);
  });

  el('npcCount').textContent = `${ents.length} entidades (mostrando ${list.length}${ents.length>max ? ' / '+max : ''})`;
}

function mountMdSection(containerId, files, startsWith){
  const host = el(containerId);
  const keys = Object.keys(files).filter(k => k.startsWith(startsWith));
  keys.sort((a,b)=>a.localeCompare(b));
  host.innerHTML = '';
  keys.forEach(k=>{
    const sec = document.createElement('section');
    sec.className = 'sec md';
    sec.id = 'file-' + k.replace(/[^a-z0-9]+/gi,'-');
    const h2 = document.createElement('h2');
    h2.textContent = k;
    const div = document.createElement('div');
    div.innerHTML = files[k] || '';
    sec.appendChild(h2);
    sec.appendChild(div);
    host.appendChild(sec);
  });
}

function buildToc(){
  const toc = el('toc');
  const items = [
    ['Visão geral', '#sec-overview'],
    ['Mapa macro (facções)', '#sec-macro-map'],
    ['Ferramentas (Mapa/Teia)', '#sec-tools'],
    ['Facções (mestre)', '#sec-faccoes'],
    ['Clãs (estrutura)', '#sec-clas'],
    ['Coteries/Associações', '#sec-coteries'],
    ['NPCs e Servos (busca)', '#sec-npcs'],
    ['Antagonistas', '#sec-antagonistas'],
    ['Arquivos (jogadores)', '#sec-files-jogadores'],
    ['Arquivos (narrador)', '#sec-files-narrador'],
  ];
  toc.innerHTML = '';
  items.forEach(([label, href])=>{
    const a = document.createElement('a');
    a.href = href;
    a.textContent = label;
    toc.appendChild(a);
  });
}

async function main(){
  // Prefer inline data when opened via file:// (fetch is often blocked by CORS).
  let data = null;
  if (window.BOOK_DATA) {
    data = window.BOOK_DATA;
  } else {
    const elJson = document.getElementById('bookDataJson');
    if (elJson && elJson.textContent && elJson.textContent.trim()) {
      data = JSON.parse(elJson.textContent);
    } else {
      const res = await fetch('book_data.json', { cache: 'no-store' });
      data = await res.json();
    }
  }
  state.data = data;
  window.__PORTRAIT_V = Date.now();

  buildToc();
  el('kCounts').textContent = `Kindred: ${data.counts.kindred} · Ghouls: ${data.counts.ghouls} · Mortais: ${data.counts.mortals}`;

  // Render macro map
  if (window.MACRO_MAP_SVG) {
    el('macroMap').innerHTML = window.MACRO_MAP_SVG;
  } else {
    const elSvg = document.getElementById('macroMapSvg');
    const tpl = (elSvg && elSvg.content) ? elSvg.content : null;
    const markup = tpl ? (tpl.firstElementChild ? tpl.firstElementChild.outerHTML : '') : (elSvg ? elSvg.innerHTML : '');
    if (markup && markup.trim()) {
      el('macroMap').innerHTML = markup;
    } else {
      const svg = await fetch('mapa_macro_faccoes.svg', { cache:'no-store' }).then(r=>r.text());
      el('macroMap').innerHTML = svg;
    }
  }

  // Mount MD sections (converted server-side).
  mountMdSection('filesJogadores', data.files_html || {}, 'jogadores/');
  mountMdSection('filesNarrador', data.files_html || {}, 'narrador/');
  mountMdSection('filesFaccoes', data.files_html || {}, 'narrador/faccoes/');
  mountMdSection('filesAntagonistas', data.files_html || {}, 'antagonistas/');
  mountMdSection('filesClas', data.files_html || {}, 'clas/');

  // Coteries cards
  const cwrap = el('coteriesCards');
  const cots = Array.isArray(data.coteries) ? data.coteries : [];
  const byId = data.coteries_by_id || {};
  const byEntId = new Map((data.entities||[]).filter(Boolean).map(e => [e.id, e]));
  function entName(eid){
    const ent = byEntId.get(eid);
    return ent ? (ent.display_name || eid) : eid;
  }
  function entById(eid){ return byEntId.get(eid) || null; }
  if(cwrap){
    cwrap.innerHTML = '';
    cots.slice().sort((a,b)=>String(a.name||'').localeCompare(String(b.name||''))).forEach(c=>{
      const cid = c.id;
      const exp = (byId[cid] && Array.isArray(byId[cid].members_expanded)) ? byId[cid].members_expanded : (c.members||[]);
      const card = document.createElement('div');
      card.className = 'card';
      const head = document.createElement('div');
      head.className = 'cardHead';
      const meta = document.createElement('div');
      const t = document.createElement('div');
      t.className = 'cardTitle';
      t.textContent = c.name || cid;
      const m = document.createElement('div');
      m.className = 'cardMeta';
      m.textContent = (c.faction || '-') + (c.base ? (' · Base: ' + c.base) : '') + ' · Membros: ' + exp.length;
      meta.appendChild(t);
      meta.appendChild(m);
      head.appendChild(meta);

      const body = document.createElement('div');
      body.className = 'cardBody';
      const lines = [];
      if(c.notes) lines.push(c.notes);
      lines.push('');
      lines.push('Membros (inclui servos relevantes):');
      const shown = exp.slice(0, 28);
      shown.forEach(eid => lines.push('- ' + entName(eid)));
      if(exp.length > shown.length) lines.push('- ...');
      body.textContent = lines.join('\\n');

      card.appendChild(head);
      card.appendChild(body);

      // Click card: apply coterie filter
      card.addEventListener('click', ()=> applyCoterieFilter(cid));

      // Click member names: open modal (requires hit-test)
      card.addEventListener('dblclick', (ev)=>{
        // As a simple UX: double-click opens first member (or no-op). This keeps single click as filter.
        if(!shown.length) return;
        const ent = entById(shown[0]);
        if(ent) openModalForEntity(ent);
      });

      // Add lightweight member chips row (clickable) for the first few.
      const chips = document.createElement('div');
      chips.className = 'chips';
      chips.style.margin = '10px';
      exp.slice(0,10).forEach(eid=>{
        const ent = entById(eid);
        const a = document.createElement('a');
        a.href = '#';
        a.textContent = entName(eid);
        a.className = 'chip';
        a.addEventListener('click', (ev)=>{ ev.preventDefault(); ev.stopPropagation(); if(ent) openModalForEntity(ent); });
        chips.appendChild(a);
      });
      if(exp.length > 10){
        const more = document.createElement('span');
        more.className = 'chip';
        more.textContent = '+' + (exp.length - 10) + ' outros';
        chips.appendChild(more);
      }
      card.appendChild(chips);

      cwrap.appendChild(card);
    });
  }

  // Filters
  const sects = uniq((data.entities||[]).map(e=>e.sect_norm||macroKey(e.sect||'')).filter(Boolean)).sort((a,b)=>a.localeCompare(b));
  const clans = uniq((data.entities||[]).filter(e=>e.kind==='kindred').map(e=>e.clan).filter(Boolean)).sort((a,b)=>a.localeCompare(b));
  const kinds = ['kindred','ghoul','mortal'];
  buildChips('chipsSect', sects);
  buildChips('chipsClan', clans);
  buildChips('chipsKind', kinds, v => v==='kindred' ? 'kindred (vampiro)' : v);
  const coteries = (data.coteries || []).map(c => ({id:c.id, name:c.name})).filter(c => c.id && c.name).sort((a,b)=>a.name.localeCompare(b.name));
  buildChips('chipsCoterie', coteries.map(x=>x.id), (id) => {
    const m = coteries.find(x=>x.id===id);
    return m ? m.name : id;
  });

  el('q').addEventListener('input', (ev)=>{ state.filters.q = ev.target.value || ''; renderNpcCards(); });
  el('btnClear').addEventListener('click', ()=>{
    state.filters.q='';
    el('q').value='';
    ['chipsSect','chipsClan','chipsKind','chipsCoterie'].forEach(id=>{
      el(id).querySelectorAll('input[type=checkbox]').forEach(cb=>cb.checked=false);
    });
    state.filters.sect.clear(); state.filters.clan.clear(); state.filters.kind.clear(); state.filters.coterie.clear();
    renderNpcCards();
  });

  // Links
  el('lnkMap').href = data.paths.map_html;
  el('lnkTeia').href = data.paths.teia_html;

  // Macro map tooltip (explicit; file:// often ignores <title> tooltips in embedded SVG).
  const tip = el('mapTip');
  const macroHost = el('macroMap');
  function showTip(x,y,html){
    tip.style.display = 'block';
    tip.innerHTML = html;
    const r = macroHost.getBoundingClientRect();
    const maxX = r.width - 20;
    const maxY = r.height - 20;
    const left = Math.min(maxX, Math.max(10, x));
    const top = Math.min(maxY, Math.max(10, y));
    tip.style.left = left + 'px';
    tip.style.top = top + 'px';
  }
  function hideTip(){ tip.style.display = 'none'; }
  const svgEl = macroHost.querySelector('svg');
  if(svgEl){
    svgEl.querySelectorAll('path[data-district]').forEach(p=>{
      p.addEventListener('mousemove', (ev)=>{
        const name = p.getAttribute('data-district') || '';
        const dom = p.getAttribute('data-dominant') || '';
        const dis = p.getAttribute('data-dispute') || '';
        const html = `<div class=\"t\">${name}</div><div>Dominante: ${dom || '-'}</div>` + (dis ? `<div>Disputa: ${dis}</div>` : '');
        const r = macroHost.getBoundingClientRect();
        showTip(ev.clientX - r.left + 12, ev.clientY - r.top + 12, html);
      });
      p.addEventListener('mouseleave', hideTip);
    });
    svgEl.addEventListener('mouseleave', hideTip);
  }

  el('modalClose').addEventListener('click', closeModal);
  el('modalWrap').addEventListener('click', (ev)=>{ if(ev.target && ev.target.id==='modalWrap') closeModal(); });
  document.addEventListener('keydown', (ev)=>{ if(ev.key==='Escape') closeModal(); });

  renderNpcCards();
}

function macroKey(s){
  s = String(s||'').toLowerCase();
  if(s.includes('camar')) return 'Camarilla';
  if(s.includes('anarch')) return 'Anarch';
  if(s.includes('indep') || s.includes('autarqu') || s.includes('zona')) return 'Independentes';
  if(s.includes('segunda') || s.includes('inquis')) return 'Segunda Inquisição';
  if(s.includes('mortal')) return 'Mortal';
  return (s||'').trim();
}

main().catch(err => {
  console.error(err);
  const e = document.createElement('pre');
  e.textContent = String(err && err.stack ? err.stack : err);
  document.body.appendChild(e);
});
""".strip() + "\n"
    OUT_JS.write_text(js, encoding="utf-8", newline="\n")

    # Convert md to html now, and keep raw text in the JSON.
    files_html: dict[str, str] = {}
    for k, v in (data.get("files") or {}).items():
        files_html[k] = md_to_html(v)
    data2 = dict(data)
    data2["files_html"] = files_html
    OUT_DATA.write_text(json.dumps(data2, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    macro_svg = OUT_MAP_SVG.read_text(encoding="utf-8")

    # Inline JSON must not be HTML-escaped, otherwise JSON.parse fails.
    # Guard against accidentally closing the script tag.
    inline_json = json.dumps(data2, ensure_ascii=False).replace("</", "<\\/")

    html = f"""<!doctype html>
<html lang="pt-br">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Sao Paulo by Night (V5) - Livro</title>
  <link rel="stylesheet" href="book.css" />
</head>
<body>
  <!-- Inline payloads so the book works on file:// without fetch() -->
  <script id="bookDataJson" type="application/json">{inline_json}</script>
  <template id="macroMapSvg">{macro_svg}</template>
  <div class="wrap">
    <aside class="side">
      <h1>Livro: Sao Paulo by Night</h1>
      <div class="hint">Compilado do projeto (V5). Indice clicavel, mapa macro e busca de NPCs.</div>
      <div class="kicker" id="kCounts"></div>
      <div class="sec">
        <h2>Indice</h2>
        <nav class="toc" id="toc"></nav>
      </div>
      <div class="sec">
        <h2>Abrir</h2>
        <div class="embedRow">
          <a id="lnkMap" href="#">Mapa territorial (interativo)</a>
          <a id="lnkTeia" href="#">Teia de conexoes (interativa)</a>
        </div>
        <div class="small">Dica: no mapa, ative "Cainitas (pins)" para ver todos. Clique num pin para abrir o retrato e detalhes.</div>
      </div>
      <div class="sec">
        <h2>NPCs (filtros)</h2>
        <input id="q" type="text" placeholder="busca: nome, papel, dominio, seita..." />
        <div class="actions" style="margin-top:10px;">
          <button id="btnClear">Limpar filtros</button>
        </div>
        <div class="small">Seitas</div>
        <div class="chips" id="chipsSect" style="margin:8px 0 10px;"></div>
        <div class="small">Clãs (Kindred)</div>
        <div class="chips" id="chipsClan" style="margin:8px 0 10px;"></div>
        <div class="small">Coteries/associações</div>
        <div class="chips" id="chipsCoterie" style="margin:8px 0 10px;"></div>
        <div class="small">Tipos</div>
        <div class="chips" id="chipsKind" style="margin:8px 0 0;"></div>
      </div>
    </aside>

    <main class="main">
      <div class="content">
        <section class="sec hero" id="sec-overview">
          <h2>Visao geral</h2>
          <div class="kicker">Este livro junta: arquivos para jogadores e mestre, faccoes, clãs, coteries, NPCs/servos e antagonistas.</div>
          <div class="embedRow" style="margin-top:10px;">
            <a href="#sec-npcs">Ir para NPCs</a>
            <a href="#sec-antagonistas">Ir para Antagonistas</a>
          </div>
        </section>

        <section class="sec" id="sec-macro-map">
          <h2>Mapa macro (faccoes)</h2>
          <div class="heroGrid">
            <div class="mapBox" id="macroMap"><div id="mapTip" class="mapTip"></div></div>
            <div>
              <div class="kicker">Legenda</div>
              <div class="sec" style="margin:8px 0 0;">
                <div class="chips">
                  <span class="chip"><span class="dot" style="background:{COLORS['Camarilla']}; width:12px; height:12px; border-radius:999px; display:inline-block;"></span> Camarilla</span>
                  <span class="chip"><span class="dot" style="background:{COLORS['Anarch']}; width:12px; height:12px; border-radius:999px; display:inline-block;"></span> Anarch</span>
                  <span class="chip"><span class="dot" style="background:{COLORS['Independentes']}; width:12px; height:12px; border-radius:999px; display:inline-block;"></span> Independentes</span>
                  <span class="chip"><span class="dot" style="background:{COLORS['Contestado']}; width:12px; height:12px; border-radius:999px; display:inline-block;"></span> Contestado (hachura)</span>
                </div>
                <div class="small" style="margin-top:8px;">Passe o mouse por cima dos distritos para ver dominante e disputas (tooltip).</div>
              </div>
            </div>
          </div>
        </section>

        <section class="sec" id="sec-tools">
          <h2>Ferramentas</h2>
          <div class="embedRow">
            <a href="../06_MAPA_SP/mapa_sp_dominios.html">Abrir mapa territorial (Leaflet)</a>
            <a href="../01_BACKGROUND_NARRADOR/teia_de_conexoes_mapa.html">Abrir teia de conexoes (vis-network)</a>
          </div>
        </section>

        <section class="sec" id="sec-faccoes">
          <h2>Faccoes (mestre)</h2>
          <div id="filesFaccoes"></div>
        </section>

        <section class="sec" id="sec-clas">
          <h2>Clãs (estrutura)</h2>
          <div id="filesClas"></div>
        </section>

        <section class="sec" id="sec-coteries">
          <h2>Coteries e associacoes</h2>
          <div class="kicker">Clique em um cartao para aplicar filtro por coterie/associacao. Clique em um membro para abrir o dossie.</div>
          <div class="gridCards" id="coteriesCards" style="margin-top:10px;"></div>
        </section>

        <section class="sec" id="sec-npcs">
          <h2>NPCs e servos</h2>
          <div class="kicker" id="npcCount"></div>
          <div class="gridCards" id="npcCards" style="margin-top:10px;"></div>
          <div class="small" style="margin-top:10px;">Nota: os retratos usam `05_ASSETS/portraits/&lt;file_stem&gt;.png`.</div>
        </section>

        <section class="sec" id="sec-antagonistas">
          <h2>Antagonistas</h2>
          <div id="filesAntagonistas"></div>
        </section>

        <section class="sec" id="sec-files-jogadores">
          <h2>Arquivos (jogadores)</h2>
          <div id="filesJogadores"></div>
        </section>

        <section class="sec" id="sec-files-narrador">
          <h2>Arquivos (narrador)</h2>
          <div id="filesNarrador"></div>
        </section>
      </div>
    </main>
  </div>

  <div class="modalWrap" id="modalWrap" aria-hidden="true">
    <div class="modal" role="dialog" aria-modal="true">
      <div class="modalHead">
        <div class="ttl" id="modalTitle">NPC</div>
        <button id="modalClose">Fechar</button>
      </div>
      <div class="modalBody">
        <div class="twoCol">
          <div>
            <div class="bigPortrait"><img id="modalImg" alt="" /></div>
            <div class="kv mono" id="modalMeta"></div>
          </div>
          <div>
            <div class="blk">
              <h3>Prompt de imagem</h3>
              <pre class="mono" id="modalPrompt"></pre>
            </div>
            <div class="blk">
              <h3>Ficha resumida</h3>
              <pre class="mono" id="modalResumo"></pre>
            </div>
            <div class="blk">
              <h3>História</h3>
              <pre class="mono" id="modalHistoria"></pre>
            </div>
            <div class="blk">
              <h3>Ficha completa (arquivo)</h3>
              <pre class="mono" id="modalCompleta"></pre>
            </div>
            <div class="blk">
              <h3>Ficha completa (estruturada)</h3>
              <pre class="mono" id="modalFullSheet"></pre>
            </div>
            <div class="blk">
              <h3>Caminhos (referência)</h3>
              <pre class="mono" id="modalPaths"></pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  <script src="book.js"></script>
</body>
</html>
"""
    OUT_HTML.write_text(html, encoding="utf-8", newline="\n")


def main() -> int:
    data = build_data()
    write_assets()
    write_book_files(data)
    print(f"[book] wrote {OUT_HTML}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
