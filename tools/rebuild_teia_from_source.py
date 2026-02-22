from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "tools" / "sp_by_night_source.json"
REDE_YML = ROOT / "01_BACKGROUND_NARRADOR" / "data" / "rede_cainita.yml"
TEIA_HTML = ROOT / "01_BACKGROUND_NARRADOR" / "teia_de_conexoes_mapa.html"


def die(msg: str) -> None:
    raise SystemExit(msg)


def _q(s: str) -> str:
    # YAML safe-ish scalar (double-quoted)
    s = "" if s is None else str(s)
    s = s.replace("\\", "\\\\").replace('"', '\\"')
    return f"\"{s}\""


def tier_size(tier: str, kind: str) -> int:
    t = (tier or "").strip().upper()
    if kind == "kindred":
        return {"S": 18, "A": 14, "B": 11, "C": 9, "D": 8}.get(t, 9)
    if kind == "ghoul":
        return 8
    return 7


EDGE_STYLE = {
    "ally": ("alianca", "rgba(107,208,227,0.55)", False),
    "enemy": ("inimizade", "rgba(227,107,125,0.55)", False),
    "pressure": ("pressao", "rgba(255,170,70,0.55)", True),
    "servant": ("servo", "rgba(135,227,140,0.55)", False),
    "boon_due": ("divida", "rgba(107,208,227,0.55)", False),
    "employer": ("comando", "rgba(135,227,140,0.55)", False),
    "mentor": ("mentor", "rgba(107,208,227,0.55)", False),
    "rival": ("rivalidade", "rgba(227,107,125,0.55)", True),
    "uneasy": ("tensao", "rgba(255,255,255,0.22)", True),
    "client": ("cliente", "rgba(255,255,255,0.22)", False),
    "oath": ("juramento", "rgba(135,227,140,0.55)", False),
    "contact": ("contato", "rgba(255,255,255,0.22)", False),
    "target": ("alvo", "rgba(255,170,70,0.55)", False),
}


def build_nodes_edges(entities: list[dict]) -> tuple[list[dict], list[dict]]:
    by_id = {e.get("id"): e for e in entities if isinstance(e, dict) and e.get("id")}

    nodes: list[dict] = []
    edges: list[dict] = []
    edge_id = 1

    for e in entities:
        if not isinstance(e, dict):
            continue
        eid = e.get("id") or ""
        if not eid:
            continue
        kind = e.get("kind") or "kindred"
        clan = e.get("clan") or ""
        sect = e.get("sect") or ""
        role = e.get("role") or ""
        dom = e.get("domain") or ""
        cots = e.get("coteries") or []
        if not isinstance(cots, list):
            cots = [cots]
        cots = [str(x) for x in cots if x]
        name = e.get("display_name") or e.get("name") or eid
        file_stem = e.get("file_stem") or ""
        embrace = e.get("embrace_year")
        tier = e.get("tier") or ""

        label = f"{name}"
        title_lines = [
            f"Nome: {name}",
            f"Tipo: {kind}",
        ]
        if clan:
            title_lines.append(f"Cla: {clan}")
        if sect:
            title_lines.append(f"Seita: {sect}")
        if role:
            title_lines.append(f"Funcao: {role}")
        if dom:
            title_lines.append(f"Dominio: {dom}")
        if cots:
            title_lines.append("Coteries/associacoes: " + ", ".join(cots[:6]) + (" ..." if len(cots) > 6 else ""))
        if embrace:
            title_lines.append(f"Abraco: {embrace}")
        if tier:
            title_lines.append(f"Tier: {tier}")

        nodes.append(
            {
                "id": eid,
                "file_stem": file_stem,
                "label": label,
                "group": clan or kind,
                "kind": kind,
                "clan": clan,
                "sect": sect,
                "role": role,
                "domain": dom,
                "coteries": cots,
                "embrace_year": embrace,
                "tier": tier,
                "title": "\n".join(title_lines),
                "shape": "dot",
                "size": tier_size(tier, kind),
            }
        )

    for e in entities:
        if not isinstance(e, dict):
            continue
        frm = e.get("id") or ""
        if not frm:
            continue
        for l in (e.get("links") or []):
            if not isinstance(l, dict):
                continue
            to = l.get("to") or ""
            if not to or to not in by_id:
                continue
            typ = (l.get("type") or "contact").strip()
            note = l.get("note") or ""
            label, color, dashed = EDGE_STYLE.get(typ, ("ligacao", "rgba(255,255,255,0.22)", False))
            to_name = (by_id.get(to) or {}).get("display_name") or to
            from_name = (by_id.get(frm) or {}).get("display_name") or frm
            edges.append(
                {
                    "id": f"e{edge_id:04d}",
                    "from": frm,
                    "to": to,
                    "type": typ,
                    "label": label,
                    "note": note,
                    "arrows": "to",
                    "title": f"Tipo: {label}\\nDe: {from_name}\\nPara: {to_name}\\nNota: {note}",
                    "color": {"color": color},
                    "dashes": bool(dashed),
                }
            )
            edge_id += 1

    return nodes, edges


def write_rede_yml(entities: list[dict]) -> None:
    # Minimal YAML used as "fonte oficial" para coerencia: o mapa/teia usam src JSON.
    # Keep it human-readable.
    lines: list[str] = []
    lines.append("meta:")
    lines.append("  chronicle_year: 2035")
    lines.append("  note: \"Arquivo gerado a partir de tools/sp_by_night_source.json.\"")
    lines.append("entities:")
    for e in entities:
        if not isinstance(e, dict):
            continue
        eid = e.get("id") or ""
        if not eid:
            continue
        lines.append(f"  - id: {_q(eid)}")
        lines.append(f"    name: {_q(e.get('display_name') or e.get('name') or '')}")
        lines.append(f"    file_stem: {_q(e.get('file_stem') or '')}")
        lines.append(f"    kind: {_q(e.get('kind') or '')}")
        lines.append(f"    clan: {_q(e.get('clan') or '')}")
        lines.append(f"    sect: {_q(e.get('sect') or '')}")
        lines.append(f"    role: {_q(e.get('role') or '')}")
        lines.append(f"    domain: {_q(e.get('domain') or '')}")
        aa = e.get("apparent_age")
        lines.append(f"    apparent_age: {_q(aa) if aa is not None else 'null'}")
        ey = e.get("embrace_year")
        lines.append(f"    embrace_year: {ey if isinstance(ey,int) else 'null'}")
        by = e.get("born_year")
        lines.append(f"    born_year: {by if isinstance(by,int) else 'null'}")
        sire = e.get("sire")
        lines.append(f"    sire: {_q(sire) if sire else 'null'}")
        ch = e.get("childer") or []
        lines.append("    childer:")
        if ch:
            for x in ch:
                lines.append(f"      - {_q(x)}")
        else:
            lines.append("      - null")
        lines.append(f"    tier: {_q(e.get('tier') or '')}")
        lines.append("    links:")
        ln = e.get("links") or []
        if ln:
            for l in ln:
                if not isinstance(l, dict):
                    continue
                lines.append(f"      - to: {_q(l.get('to') or '')}")
                lines.append(f"        type: {_q(l.get('type') or '')}")
                lines.append(f"        note: {_q(l.get('note') or '')}")
        else:
            lines.append("      - to: null")
            lines.append("        type: \"\"")
            lines.append("        note: \"\"")
    REDE_YML.parent.mkdir(parents=True, exist_ok=True)
    REDE_YML.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def patch_teia_html(nodes: list[dict], edges: list[dict]) -> None:
    if not TEIA_HTML.exists():
        die(f"missing {TEIA_HTML}")
    html = TEIA_HTML.read_text(encoding="utf-8")

    nodes_json = json.dumps(nodes, ensure_ascii=False)
    edges_json = json.dumps(edges, ensure_ascii=False)

    n0 = html.find("const NODES")
    if n0 < 0:
        die("failed to patch teia html: const NODES not found")
    e0 = html.find("const EDGES", n0)
    if e0 < 0:
        die("failed to patch teia html: const EDGES not found")

    # Replace NODES statement (from 'const NODES' until the following ';')
    n_end = html.find("];", n0)
    if n_end < 0 or n_end > e0:
        die("failed to patch teia html: NODES terminator not found")
    n_end += 2  # include ];

    # Replace EDGES statement (from 'const EDGES' until the next '];')
    e_end = html.find("];", e0)
    if e_end < 0:
        die("failed to patch teia html: EDGES terminator not found")
    e_end += 2

    out = []
    out.append(html[:n0])
    out.append(f"const NODES = {nodes_json};")
    out.append(html[n_end:e0])
    out.append(f"const EDGES = {edges_json};")
    out.append(html[e_end:])
    TEIA_HTML.write_text("".join(out), encoding="utf-8")


def main() -> int:
    if not SRC.exists():
        die(f"missing {SRC}")
    data = json.loads(SRC.read_text(encoding="utf-8"))
    entities = [e for e in (data.get("entities") or []) if isinstance(e, dict)]
    coteries_by_id = {}
    for c in (data.get("coteries") or []):
        if not isinstance(c, dict):
            continue
        cid = (c.get("id") or "").strip()
        if cid:
            coteries_by_id[cid] = (c.get("name") or cid).strip() or cid

    # Replace entity coteries ids with display labels for the teia UI (filters need readable text).
    for e in entities:
        cs = e.get("coteries") or []
        if not isinstance(cs, list):
            cs = [cs]
        labs = []
        for cid in cs:
            if not cid:
                continue
            cid = str(cid)
            labs.append(coteries_by_id.get(cid, cid))
        e["coteries"] = labs
    nodes, edges = build_nodes_edges(entities)
    write_rede_yml(entities)
    patch_teia_html(nodes, edges)
    print(f"wrote {REDE_YML}")
    print(f"patched {TEIA_HTML}")
    print(f"nodes={len(nodes)} edges={len(edges)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
