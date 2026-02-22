from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CANON_MD = ROOT / "01_BACKGROUND_NARRADOR" / "canon_docx_integral.md"
SRC = ROOT / "tools" / "sp_by_night_source.json"
MAP_CFG = ROOT / "tools" / "sp_map_config.json"
REPORT = ROOT / "tools" / "canon_alignment_report.md"


def norm(s: str) -> str:
    s = (s or "").strip().lower()
    s = s.replace('"', "").replace("'", "")
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    s = re.sub(r"\s+", " ", s)
    return s


def clean_text(s: str) -> str:
    # Normalize a few common mojibake variants while preserving readability.
    rep = {
        "â€”": "—",
        "â€¢": "•",
        "â€˜": "'",
        "â€™": "'",
        "â€œ": '"',
        "â€": '"',
        "â€‘": "-",
    }
    for a, b in rep.items():
        s = s.replace(a, b)
    return s


def norm_sect(v: str) -> str:
    n = norm(v)
    if "camar" in n:
        return "Camarilla"
    if "anar" in n:
        return "Anarch"
    if "autar" in n:
        return "Autarquicos"
    if "indep" in n:
        return "Independentes"
    if "segunda" in n and ("inqu" in n or "inquis" in n):
        return "Segunda Inquisição"
    if n == "mortal":
        return "Mortal"
    return v.strip()


def norm_clan(v: str) -> str:
    n = norm(v)
    if "thin" in n and "blood" in n:
        return "Thin Blood"
    table = {
        "banu haqim": "Banu Haqim",
        "brujah": "Brujah",
        "caitiff": "Caitiff",
        "gangrel": "Gangrel",
        "hecata": "Hecata",
        "lasombra": "Lasombra",
        "malkavian": "Malkavian",
        "ministry": "Ministry",
        "nosferatu": "Nosferatu",
        "ravnos": "Ravnos",
        "salubri": "Salubri",
        "toreador": "Toreador",
        "tremere": "Tremere",
        "tzimisce": "Tzimisce",
        "ventrue": "Ventrue",
        "mortal": "Mortal",
    }
    return table.get(n, v.strip())


def clean_domain(v: str) -> str:
    s = clean_text(v or "").strip()
    if not s:
        return s
    # Keep only domain/location statement, drop side-notes.
    s = s.split("•", 1)[0].strip()
    s = re.split(r"\s+Redes:\s+|\s+Função real:\s+|\s+Funcao real:\s+", s, maxsplit=1)[0].strip()
    return s.rstrip(" .;")


@dataclass
class Row:
    tier: str
    name: str
    sect: str
    clan: str
    role: str
    domain: str
    link_name: str
    source: str


def parse_rows(md: str) -> list[Row]:
    md = clean_text(md)
    lines = md.splitlines()
    out: list[Row] = []
    sec = ""
    in_target = False

    rx = re.compile(
        r"^- (?P<tier>[^|]+)\|\s*(?P<name>.+?)\s+[—-]\s+(?P<sect>[^•]+)\s+•\s+(?P<clan>[^.]+)\.\s+"
        r"(?P<role>.+?)\.\s+Atua em\s+(?P<domain>.+?)\.\s+V[ií]nculo mais usado:\s*(?P<link>.+?)\.?\s*$"
    )

    for line in lines:
        if line.startswith("## 8.2"):
            in_target = True
            sec = "8.2"
            continue
        if line.startswith("## 8.3"):
            in_target = True
            sec = "8.3"
            continue
        if line.startswith("## 8.4"):
            break
        if not in_target:
            continue
        m = rx.match(line.strip())
        if not m:
            continue
        out.append(
            Row(
                tier=m.group("tier").strip(),
                name=m.group("name").strip(),
                sect=norm_sect(m.group("sect")),
                clan=norm_clan(m.group("clan")),
                role=m.group("role").strip(),
                domain=clean_domain(m.group("domain")),
                link_name=m.group("link").strip(),
                source=sec,
            )
        )
    return out


def coterie_id_for_heading(h: str) -> str | None:
    n = norm(h)
    if "6.4.1" in n or "ferrugem" in n:
        return "coterie_ferrugem_mooca"
    if "6.4.2" in n or "leste de aco" in n:
        return "coterie_leste_de_aco"
    if "6.4.3" in n or "matilha do sul" in n:
        return "coterie_matilha_do_sul"
    return None


def parse_coterie_core(md: str) -> dict[str, list[str]]:
    md = clean_text(md)
    lines = md.splitlines()
    out: dict[str, list[str]] = {}
    in_64 = False
    current: str | None = None

    for line in lines:
        if line.startswith("## 6.4"):
            in_64 = True
            continue
        if in_64 and line.startswith("## 6.5"):
            break
        if not in_64:
            continue
        if line.startswith("### 6.4."):
            cid = coterie_id_for_heading(line)
            current = cid
            if cid:
                out.setdefault(cid, [])
            continue
        if current and line.startswith("- "):
            # "- Nome (Clan) — papel"
            raw = line[2:].strip()
            name = re.split(r"\s+\(|\s+—\s+", raw, maxsplit=1)[0].strip()
            if name:
                out[current].append(name)
    return out


def find_entity(entities: list[dict[str, Any]], name: str) -> dict[str, Any] | None:
    key = norm(name)
    aliases = {
        norm('Damiao "Guarita"'): norm('Damiao "Portaria"'),
        norm('Wesley "Faixa" Dias'): norm('Wesley "Corredor" Dias'),
        norm("Lia \"Comunidad\" Souza"): norm("Lia \"Comunidade\" Souza"),
    }
    alt = aliases.get(key)

    for e in entities:
        if norm(e.get("display_name", "")) == key:
            return e
    if alt:
        for e in entities:
            if norm(e.get("display_name", "")) == alt:
                return e

    # Containment fallback.
    for e in entities:
        dn = norm(e.get("display_name", ""))
        if key and (key in dn or dn in key):
            return e

    # First/last fallback for nickname drift.
    toks = [t for t in re.split(r"\s+", key) if t]
    if len(toks) >= 2:
        first, last = toks[0], toks[-1]
        for e in entities:
            dn = norm(e.get("display_name", ""))
            d = [t for t in re.split(r"\s+", dn) if t]
            if len(d) >= 2 and d[0] == first and d[-1] == last:
                return e
    return None


def infer_map_domains(domain: str, cfg_domains: list[dict[str, Any]]) -> list[str]:
    d = norm(domain)
    hits: list[str] = []
    for dom in cfg_domains:
        did = dom.get("id")
        if not did:
            continue
        keys = [norm(k) for k in (dom.get("keywords") or []) if norm(k)]
        if any(k in d for k in keys):
            hits.append(did)
    return sorted(set(hits))


def main() -> int:
    src = json.loads(SRC.read_text(encoding="utf-8"))
    md = CANON_MD.read_text(encoding="utf-8")
    cfg = json.loads(MAP_CFG.read_text(encoding="utf-8"))
    map_domains = cfg.get("domains") or []

    entities: list[dict[str, Any]] = [e for e in (src.get("entities") or []) if isinstance(e, dict)]
    coteries: list[dict[str, Any]] = [c for c in (src.get("coteries") or []) if isinstance(c, dict)]
    by_id = {e.get("id"): e for e in entities if e.get("id")}

    rows = parse_rows(md)
    cot_core = parse_coterie_core(md)

    updated = 0
    unresolved_rows: list[str] = []
    unresolved_links: list[str] = []
    added_links = 0
    normalized_domains = 0

    # Global domain cleanup pass.
    for e in entities:
        old = e.get("domain") or ""
        new = clean_domain(old)
        if new != old:
            e["domain"] = new
            normalized_domains += 1

    for r in rows:
        e = find_entity(entities, r.name)
        if not e:
            unresolved_rows.append(r.name)
            continue
        changed = False

        tier = r.tier.strip().upper()
        if tier in {"S", "A", "B", "C", "D"} and e.get("tier") != tier:
            e["tier"] = tier
            changed = True

        if r.sect and e.get("sect") != r.sect:
            e["sect"] = r.sect
            changed = True

        # Keep clan mutable for all (including ghouls listed as Mortal in 8.3).
        if r.clan and e.get("clan") != r.clan:
            e["clan"] = r.clan
            changed = True

        if r.role and e.get("role") != r.role:
            e["role"] = r.role
            changed = True

        d = clean_domain(r.domain)
        if d and e.get("domain") != d:
            e["domain"] = d
            changed = True

        inferred = infer_map_domains(e.get("domain") or "", map_domains)
        if inferred:
            if e.get("map_domains") != inferred:
                e["map_domains"] = inferred
                changed = True

        target = find_entity(entities, r.link_name)
        if target and e.get("id") and target.get("id"):
            links = e.setdefault("links", [])
            exists = any(
                isinstance(lk, dict) and lk.get("to") == target["id"] and (lk.get("type") or "") == "canon_anchor"
                for lk in links
            )
            if not exists:
                links.append(
                    {
                        "to": target["id"],
                        "type": "canon_anchor",
                        "note": f"Vinculo mais usado (canon DOCX, cap. {r.source})",
                    }
                )
                added_links += 1
                changed = True
        else:
            unresolved_links.append(f"{r.name} -> {r.link_name}")

        if changed:
            updated += 1

    coterie_assign = 0
    coteries_by_id = {c.get("id"): c for c in coteries if c.get("id")}
    for cid, names in cot_core.items():
        c = coteries_by_id.get(cid)
        if not c:
            continue
        members = [m for m in (c.get("members") or []) if isinstance(m, str) and m.strip()]
        existing = set(members)
        for n in names:
            e = find_entity(entities, n)
            if not e or not e.get("id"):
                continue
            if e["id"] not in existing:
                members.append(e["id"])
                existing.add(e["id"])
                coterie_assign += 1
            ec = [x for x in (e.get("coteries") or []) if isinstance(x, str)]
            if cid not in ec:
                ec.append(cid)
                e["coteries"] = sorted(set(ec))
        c["members"] = members

    # Reattach possibly mutated lists.
    src["entities"] = entities
    src["coteries"] = coteries
    src.setdefault("meta", {})
    src["meta"]["canon_sync_source"] = str(CANON_MD.relative_to(ROOT)).replace("\\", "/")
    src["meta"]["canon_sync"] = "8.2/8.3 rows + 6.4 core coteries"
    src["meta"]["canon_sync_at"] = "2026-02-20"
    SRC.write_text(json.dumps(src, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Post metrics.
    bad_domains = [
        e for e in entities if e.get("kind") == "kindred" and ("•" in (e.get("domain") or "") or "Redes:" in (e.get("domain") or ""))
    ]

    rep: list[str] = []
    rep.append("# Canon Alignment Report")
    rep.append("")
    rep.append("- Fonte canônica: `01_BACKGROUND_NARRADOR/canon_docx_integral.md`")
    rep.append(f"- Linhas canônicas processadas (8.2/8.3): **{len(rows)}**")
    rep.append(f"- Entidades atualizadas: **{updated}**")
    rep.append(f"- Limpeza de domínio aplicada: **{normalized_domains}**")
    rep.append(f"- Links canônicos adicionados: **{added_links}**")
    rep.append(f"- Membros de coterie adicionados (6.4 núcleo): **{coterie_assign}**")
    rep.append(f"- Domínios ainda poluídos: **{len(bad_domains)}**")
    rep.append("")
    rep.append("## Linhas não resolvidas")
    if unresolved_rows:
        for x in sorted(set(unresolved_rows)):
            rep.append(f"- {x}")
    else:
        rep.append("- Nenhuma")
    rep.append("")
    rep.append("## Vínculos sem alvo resolvido")
    if unresolved_links:
        for x in sorted(set(unresolved_links)):
            rep.append(f"- {x}")
    else:
        rep.append("- Nenhum")
    REPORT.write_text("\n".join(rep).rstrip() + "\n", encoding="utf-8")

    print(f"wrote {SRC}")
    print(f"wrote {REPORT}")
    print(f"rows={len(rows)} updated={updated} normalized_domains={normalized_domains} bad_domains={len(bad_domains)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

