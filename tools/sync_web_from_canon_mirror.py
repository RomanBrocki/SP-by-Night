from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
MIRROR = ROOT / "RECONSTRUCAO_CANONICA"

BOOK_SRC_DIR = ROOT / "07_LIVRO_BY_NIGHT"
BOOK_DOCS_DIR = ROOT / "docs" / "book"
BOOK_SRC_JSON = BOOK_SRC_DIR / "book_data.json"
BOOK_DOCS_JSON = BOOK_DOCS_DIR / "book_data.json"
BOOK_SRC_INDEX = BOOK_SRC_DIR / "index.html"
BOOK_DOCS_INDEX = BOOK_DOCS_DIR / "index.html"

TEIA_FILES = [
    ROOT / "01_BACKGROUND_NARRADOR" / "teia_de_conexoes_mapa.html",
    ROOT / "docs" / "teia" / "teia_de_conexoes_mapa.html",
]

MAP_FILES = [
    ROOT / "06_MAPA_SP" / "data" / "canon_map_data.json",
    ROOT / "docs" / "map" / "data" / "canon_map_data.json",
]

CANON_COTERIES = {
    "coterie_ferrugem_mooca": {
        "heading_key": "coterie ferrugem mooca tatuape",
        "name": "Coterie Ferrugem (Mooca/Tatuapé)",
        "base": "Mooca/Tatuapé",
    },
    "coterie_leste_de_aco": {
        "heading_key": "leste de aco itaquera extremo leste",
        "name": "Leste de Aço (Itaquera/Extremo Leste)",
        "base": "Itaquera/Extremo Leste",
    },
    "coterie_matilha_do_sul": {
        "heading_key": "matilha do sul capao grajau e bordas verdes",
        "name": "Matilha do Sul (Capão/Grajaú)",
        "base": "Capão/Grajaú e bordas verdes",
    },
}

KNOWN_CLANS = [
    "Banu Haqim",
    "Brujah",
    "Caitiff",
    "Gangrel",
    "Hecata",
    "Lasombra",
    "Malkavian",
    "Ministry",
    "Nosferatu",
    "Ravnos",
    "Salubri",
    "Thin-Blood",
    "Toreador",
    "Tremere",
    "Tzimisce",
    "Ventrue",
]

SECT_LABELS = {
    "Anarch": "Anarquistas",
    "Anarquistas": "Anarquistas",
    "Camarilla": "Camarilla",
    "Independentes": "Independentes",
    "Mortal": "Mortal",
    "Mortais": "Mortal",
    "Segunda Inquisição": "Segunda Inquisição",
    "Segunda Inquisicao": "Segunda Inquisição",
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def norm_key(text: str) -> str:
    plain = unicodedata.normalize("NFKD", str(text or ""))
    plain = "".join(ch for ch in plain if not unicodedata.combining(ch))
    plain = (
        plain.replace("’", "'")
        .replace("“", '"')
        .replace("”", '"')
        .replace("–", " ")
        .replace("—", " ")
        .replace("/", " ")
        .replace("-", " ")
    )
    plain = re.sub(r"[^a-zA-Z0-9]+", " ", plain.lower())
    return re.sub(r"\s+", " ", plain).strip()


def relative_project_path(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def html_escape(text: str) -> str:
    return (
        str(text or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def md_to_html(md: str) -> str:
    lines = (md or "").replace("\r\n", "\n").splitlines()
    out: list[str] = []
    in_ul = False
    in_ol = False

    def close_lists() -> None:
        nonlocal in_ul, in_ol
        if in_ul:
            out.append("</ul>")
        if in_ol:
            out.append("</ol>")
        in_ul = False
        in_ol = False

    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            close_lists()
            continue

        heading = re.match(r"^(#{1,6})\s+(.*)$", line)
        if heading:
            close_lists()
            level = len(heading.group(1))
            out.append(f"<h{level}>{html_escape(heading.group(2).strip())}</h{level}>")
            continue

        bullet = re.match(r"^\s*[-*]\s+(.*)$", line)
        if bullet:
            if in_ol:
                out.append("</ol>")
                in_ol = False
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{html_escape(bullet.group(1).strip())}</li>")
            continue

        ordered = re.match(r"^\s*\d+\.\s+(.*)$", line)
        if ordered:
            if in_ul:
                out.append("</ul>")
                in_ul = False
            if not in_ol:
                out.append("<ol>")
                in_ol = True
            out.append(f"<li>{html_escape(ordered.group(1).strip())}</li>")
            continue

        close_lists()
        out.append(f"<p>{html_escape(line)}</p>")

    close_lists()
    return "\n".join(out)


def sanitize_site_copy(text: str) -> str:
    cleaned = str(text or "")
    cleaned = re.sub(r"Fonte can[oô]nica:", "Fonte do livro:", cleaned, flags=re.I)
    cleaned = re.sub(r"índices can[oô]nicos", "índices do livro", cleaned, flags=re.I)
    cleaned = re.sub(r"índice can[oô]nico", "índice do livro", cleaned, flags=re.I)
    cleaned = re.sub(r"Coteries can[oô]nicas", "Coteries", cleaned, flags=re.I)
    cleaned = re.sub(r"Coteries canonicas", "Coteries", cleaned, flags=re.I)
    return cleaned


def canonical_sect(value: str) -> str:
    raw = str(value or "").strip()
    return SECT_LABELS.get(raw, raw)


def parse_int(value: str) -> int | None:
    match = re.search(r"\d{3,4}", value or "")
    return int(match.group(0)) if match else None


def split_csv_names(value: str) -> list[str]:
    raw = str(value or "").strip()
    if not raw or raw == "-":
        return []
    parts = [part.strip() for part in re.split(r"\s*,\s*", raw) if part.strip()]
    return [part for part in parts if part != "-"]


def extract_served_clans(*values: Any) -> list[str]:
    found: list[str] = []
    joined = " ".join(str(v or "") for v in values)
    normed = norm_key(joined)
    for clan in KNOWN_CLANS:
        if norm_key(clan) in normed and clan not in found:
            found.append(clan)
    return found


def collect_bullets(lines: list[str], start_index: int) -> tuple[list[str], int]:
    items: list[str] = []
    idx = start_index
    while idx < len(lines):
        line = lines[idx]
        if line.startswith("- "):
            items.append(line[2:].strip())
            idx += 1
            continue
        if not line:
            idx += 1
            continue
        break
    return items, idx


def parse_presence_line(value: str) -> tuple[str | None, str | None]:
    text = str(value or "").strip()
    if not text:
        return None, None
    appearance = None
    signature = None
    if "Assinatura social:" in text:
        before, after = text.split("Assinatura social:", 1)
        signature = after.strip()
        if ";" in before:
            appearance = before.split(";", 1)[0].strip()
        else:
            appearance = before.strip()
    return appearance or None, signature or None


def compact_domain_text(value: str) -> str:
    text = str(value or "").strip().rstrip(".")
    if not text:
        return ""
    if " • " in text:
        return text.split(". ", 1)[0].strip()

    parts = [part.strip().rstrip(".") for part in re.split(r"\.\s+", text) if part.strip()]
    if len(parts) >= 3 and parts[1].startswith("Função oficial:") and parts[2].startswith("Função real:"):
        return " • ".join(parts[:3])
    if len(parts) >= 2 and (
        parts[1].startswith("Função real:")
        or parts[1].startswith("Redes:")
        or parts[1].startswith("Estado:")
        or parts[1].startswith("Vínculo:")
    ):
        return " • ".join(parts[:2])
    return parts[0] if parts else text


def parse_summary_file(summary_path: Path, kind_hint: str | None) -> dict[str, Any]:
    lines = [line.strip() for line in read_text(summary_path).splitlines()]
    content = [line for line in lines if line]
    body = [
        line
        for line in content
        if not line.startswith("Fonte canônica:")
        and not line.startswith("Apoio complementar:")
    ]
    if not body:
        return {}

    parsed: dict[str, Any] = {
        "docs": {
            "files": {
                "ficha_resumida": sanitize_site_copy(read_text(summary_path)),
            },
            "paths": {
                "ficha_resumida": relative_project_path(summary_path),
            },
        }
    }

    first = body[0]
    essential = re.match(
        r"^(?P<tier>[A-Z])\s+•\s+(?P<sect>.+?)\s+•\s+(?P<clan>.+?)\s+•\s+(?P<role>.+?)\s+\((?P<class>[^)]+)\)$",
        first,
    )
    if essential:
        parsed["tier"] = essential.group("tier").strip()
        parsed["sect"] = canonical_sect(essential.group("sect"))
        parsed["clan"] = essential.group("clan").strip()
        parsed["role"] = essential.group("role").strip()
        parsed["kind_from_summary"] = norm_key(essential.group("class"))
        idx = 1
        while idx < len(body):
            line = body[idx]
            if line.startswith("Domínio:"):
                parsed["domain"] = line.split(":", 1)[1].strip().rstrip(".")
            elif line.startswith("Estado:"):
                parsed["state_line"] = line.split(":", 1)[1].strip()
            elif line.startswith("Nasc.:"):
                parsed["born_year"] = parse_int(line)
                embrace = re.search(r"Abraço:\s*(\d{3,4})", line)
                apparent = re.search(r"Idade aparente:\s*([^•]+)$", line)
                parsed["embrace_year"] = int(embrace.group(1)) if embrace else None
                parsed["apparent_age"] = apparent.group(1).strip() if apparent else None
            elif line.startswith("Sire:"):
                parsed["sire"] = line.split(":", 1)[1].strip()
            elif line.startswith("Childe(s):"):
                parsed["childer"] = split_csv_names(line.split(":", 1)[1])
            elif line.startswith("Domitor/Patrocinador:"):
                value = line.split(":", 1)[1].strip()
                parsed["domitor"] = value
                parsed["serves_clans"] = extract_served_clans(value)
            elif line.startswith("Equipe e dependentes:"):
                value = line.split(":", 1)[1].strip()
                parsed["team_line"] = value
                parsed["serves_clans"] = extract_served_clans(
                    *(parsed.get("serves_clans") or []), value
                )
            elif re.match(r"^Objetivo(?:\s*\(.*?\))?:", line):
                parsed["ambition"] = line.split(":", 1)[1].strip()
            elif line.startswith("Medo:"):
                parsed["fear"] = line.split(":", 1)[1].strip()
            elif re.match(r"^Segredo(?:\s*\(.*?\))?:", line):
                parsed["secret"] = line.split(":", 1)[1].strip()
            elif line.startswith("Verdade perigosa:"):
                parsed["dangerous_truth"] = line.split(":", 1)[1].strip()
            elif line.startswith("Falso rumor"):
                parsed["false_rumor"] = line.split(":", 1)[1].strip()
            elif line == "Ganchos curtos:":
                hooks, idx = collect_bullets(body, idx + 1)
                parsed["scene_hooks"] = hooks
                continue
            elif line.startswith("Vínculo mais usado"):
                parsed["canon_anchor_name"] = line.split(":", 1)[1].strip()
            idx += 1
        return parsed

    fields: dict[str, str] = {}
    for line in body:
        if ": " not in line:
            continue
        key, value = line.split(":", 1)
        fields[norm_key(key)] = value.strip()

    parsed["display_name"] = fields.get("nome")
    parsed["tier"] = fields.get("tier")
    parsed["sect"] = canonical_sect(
        fields.get("faccao afiliacao") or fields.get("secao maior") or ""
    )
    parsed["clan"] = fields.get("cla ou tipo")
    parsed["role"] = fields.get("funcao")
    parsed["domain"] = fields.get("area de atuacao")
    parsed["canon_anchor_name"] = fields.get("vinculo mais usado")
    if kind_hint:
        parsed["kind_from_summary"] = kind_hint
    return parsed


def parse_history_file(history_path: Path) -> dict[str, Any]:
    lines = [line.strip() for line in read_text(history_path).splitlines()]
    content = [line for line in lines if line]
    body = [
        line
        for line in content
        if not line.startswith("Fonte canônica:")
        and not line.startswith("Apoio complementar:")
        and line != "História e comportamento:"
    ]
    parsed: dict[str, Any] = {}
    idx = 0
    while idx < len(body):
        line = body[idx]
        if line.startswith("Nome:"):
            parsed["display_name"] = line.split(":", 1)[1].strip()
        elif line.startswith("Nasc.:"):
            parsed["born_year"] = parse_int(line)
            embrace = re.search(r"Abraço:\s*(\d{3,4})", line)
            apparent = re.search(r"Idade aparente:\s*([^•]+)$", line)
            parsed["embrace_year"] = int(embrace.group(1)) if embrace else None
            parsed["apparent_age"] = apparent.group(1).strip() if apparent else None
        elif line.startswith("Sire:"):
            parsed["sire"] = line.split(":", 1)[1].strip()
        elif line.startswith("Childe(s):"):
            parsed["childer"] = split_csv_names(line.split(":", 1)[1])
        elif line.startswith("Domitor/Patrocinador:"):
            value = line.split(":", 1)[1].strip()
            parsed["domitor"] = value
            parsed["serves_clans"] = extract_served_clans(value)
        elif line.startswith("Equipe e dependentes:"):
            value = line.split(":", 1)[1].strip()
            parsed["team_line"] = value
            parsed["serves_clans"] = extract_served_clans(
                *(parsed.get("serves_clans") or []), value
            )
        elif line.startswith("Presença em cena:"):
            appearance, signature = parse_presence_line(line.split(":", 1)[1].strip())
            if appearance:
                parsed["appearance_explicit"] = appearance
            if signature:
                parsed["signature_style"] = signature
        elif re.match(r"^Objetivo(?:\s*\(.*?\))?:", line):
            parsed["ambition"] = line.split(":", 1)[1].strip()
        elif line.startswith("Medo:"):
            parsed["fear"] = line.split(":", 1)[1].strip()
        elif re.match(r"^Segredo(?:\s*\(.*?\))?:", line):
            parsed["secret"] = line.split(":", 1)[1].strip()
        elif line.startswith("Verdade perigosa:"):
            parsed["dangerous_truth"] = line.split(":", 1)[1].strip()
        elif line.startswith("Falso rumor"):
            parsed["false_rumor"] = line.split(":", 1)[1].strip()
        elif line == "Ganchos curtos:":
            hooks, idx = collect_bullets(body, idx + 1)
            parsed["scene_hooks"] = hooks
            continue
        idx += 1
    return parsed


def infer_kind_from_path(path: Path) -> str:
    rel = path.relative_to(MIRROR).as_posix()
    if rel.startswith("02_NPCS/"):
        return "kindred"
    if rel.startswith("03_SERVOS_E_CONTATOS/ghouls/"):
        return "ghoul"
    return "mortal"


def load_current_skeleton() -> dict[str, Any]:
    return json.loads(read_text(BOOK_SRC_JSON))


def build_canonical_entity_records(
    current_data: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    current_entities = current_data.get("entities") or []

    mirror_files = sorted(MIRROR.glob("02_NPCS/*/*_ficha_resumida.txt")) + sorted(
        MIRROR.glob("03_SERVOS_E_CONTATOS/**/*_ficha_resumida.txt")
    )

    parsed_by_stem: dict[str, dict[str, Any]] = {}
    missing_history: list[str] = []
    for summary_path in mirror_files:
        file_stem = summary_path.name[: -len("_ficha_resumida.txt")]
        history_path = summary_path.with_name(f"{file_stem}_historia.txt")
        full_path = summary_path.with_name(f"{file_stem}_ficha_completa.md")
        prompt_path = MIRROR / "05_ASSETS" / "portrait_prompts" / f"{file_stem}.txt"
        kind_hint = infer_kind_from_path(summary_path)
        parsed = parse_summary_file(summary_path, kind_hint)
        if history_path.exists():
            parsed.update(
                {
                    key: value
                    for key, value in parse_history_file(history_path).items()
                    if value not in (None, "", [])
                }
            )
        else:
            missing_history.append(file_stem)

        parsed["file_stem"] = file_stem
        parsed.setdefault("display_name", file_stem.replace("_", " "))
        parsed.setdefault("kind", kind_hint)
        parsed["docs"]["files"]["historia"] = sanitize_site_copy(read_text(history_path)) if history_path.exists() else ""
        parsed["docs"]["paths"]["historia"] = (
            relative_project_path(history_path) if history_path.exists() else ""
        )
        if full_path.exists():
            full_text = read_text(full_path)
            parsed["docs"]["files"]["ficha_completa"] = sanitize_site_copy(full_text)
            parsed["docs"]["paths"]["ficha_completa"] = relative_project_path(full_path)
            stripped = full_text.strip()
            if stripped.startswith("{") and stripped.endswith("}"):
                try:
                    parsed["full_sheet"] = json.loads(stripped)
                except json.JSONDecodeError:
                    parsed["full_sheet"] = None
            else:
                parsed["full_sheet"] = None
        else:
            parsed["docs"]["files"]["ficha_completa"] = ""
            parsed["docs"]["paths"]["ficha_completa"] = ""
            parsed["full_sheet"] = None
        parsed["portrait_prompt"] = sanitize_site_copy(read_text(prompt_path).strip()) if prompt_path.exists() else ""
        parsed_by_stem[norm_key(file_stem)] = parsed

    extras: list[str] = []
    missing: list[str] = []
    entities: list[dict[str, Any]] = []
    for current in current_entities:
        file_stem = current.get("file_stem") or ""
        parsed = parsed_by_stem.get(norm_key(file_stem))
        if not parsed:
            parsed = parsed_by_stem.get(norm_key(current.get("display_name")))
        if not parsed:
            missing.append(file_stem or str(current.get("id") or ""))
            parsed = {
                "display_name": current.get("display_name") or file_stem.replace("_", " "),
                "file_stem": file_stem,
                "kind": current.get("kind") or "kindred",
                "docs": {
                    "files": {
                        "ficha_resumida": "",
                        "historia": "",
                        "ficha_completa": "",
                    },
                    "paths": {
                        "ficha_resumida": "",
                        "historia": "",
                        "ficha_completa": "",
                    },
                },
                "portrait_prompt": current.get("portrait_prompt") or "",
                "full_sheet": None,
            }
        kind = current.get("kind") or parsed.get("kind") or "kindred"
        clan_value = parsed.get("clan") or current.get("clan") or ""
        serves_clans = parsed.get("serves_clans") or current.get("serves_clans") or []
        if isinstance(serves_clans, str):
            serves_clans = [serves_clans]
        if kind == "ghoul" and not serves_clans:
            serves_clans = extract_served_clans(
                parsed.get("domitor"),
                parsed.get("team_line"),
                current.get("clan"),
                current.get("sect"),
            )

        entity = {
            "id": current.get("id"),
            "display_name": parsed.get("display_name") or current.get("display_name"),
            "file_stem": file_stem or parsed.get("file_stem"),
            "kind": kind,
            "clan": clan_value,
            "sect": canonical_sect(parsed.get("sect") or current.get("sect") or ""),
            "sect_norm": canonical_sect(parsed.get("sect") or current.get("sect") or ""),
            "role": parsed.get("role") or current.get("role") or "",
            "domain": parsed.get("domain") or current.get("domain") or "",
            "apparent_age": parsed.get("apparent_age") or current.get("apparent_age"),
            "embrace_year": parsed.get("embrace_year"),
            "born_year": parsed.get("born_year"),
            "sire": parsed.get("sire") or "",
            "childer": parsed.get("childer") or [],
            "signature_style": parsed.get("signature_style") or "",
            "appearance_explicit": parsed.get("appearance_explicit") or "",
            "ambition": parsed.get("ambition") or "",
            "fear": parsed.get("fear") or "",
            "secret": parsed.get("secret") or "",
            "dangerous_truth": parsed.get("dangerous_truth") or "",
            "false_rumor": parsed.get("false_rumor") or "",
            "scene_hooks": parsed.get("scene_hooks") or [],
            "tier": parsed.get("tier") or current.get("tier") or "",
            "links": [],
            "full_sheet": parsed.get("full_sheet"),
            "portrait_prompt": parsed.get("portrait_prompt") or current.get("portrait_prompt") or "",
            "docs": parsed.get("docs"),
            "map_domains": current.get("map_domains") or [],
            "serves_clans": serves_clans,
            "coteries": [],
            "coteries_all": [],
        }
        entity["domain_compact"] = compact_domain_text(entity.get("domain"))
        entities.append(entity)

    seen_stems = {norm_key(entity.get("file_stem")) for entity in entities}
    for stem_key, parsed in parsed_by_stem.items():
        if stem_key not in seen_stems:
            extras.append(parsed.get("file_stem") or stem_key)

    extras.extend(missing_history)
    return entities, missing, extras


def parse_coteries(entities: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, list[str]]]:
    name_to_id = {
        norm_key(entity.get("display_name")): entity.get("id")
        for entity in entities
        if entity.get("display_name") and entity.get("id")
    }
    lines = read_text(MIRROR / "01_BACKGROUND_NARRADOR" / "coteries_e_associacoes.md").splitlines()
    sections: list[tuple[str, list[str]]] = []
    idx = 0
    while idx < len(lines):
        line = lines[idx]
        if line.startswith("### 6.4."):
            title = line.split(" - ", 1)[1].strip()
            block: list[str] = []
            idx += 1
            while idx < len(lines) and not lines[idx].startswith("### 6.4."):
                block.append(lines[idx])
                idx += 1
            sections.append((title, block))
            continue
        idx += 1

    coteries: list[dict[str, Any]] = []
    by_member: dict[str, list[str]] = {}

    for title, block in sections:
        title_key = norm_key(title)
        coterie_id = None
        for candidate_id, info in CANON_COTERIES.items():
            if info["heading_key"] == title_key:
                coterie_id = candidate_id
                break
        if not coterie_id:
            continue

        first_paragraph: list[str] = []
        members: list[str] = []
        notes: list[str] = []
        active_section = ""

        for raw in block:
            line = raw.strip()
            if not line:
                if active_section in {"intro", "notes"}:
                    active_section = ""
                continue
            if line.startswith("#### "):
                active_section = ""
                if "Quem é quem" in line:
                    active_section = "members"
                elif "Razão de existir" in line:
                    active_section = "notes"
                continue
            if not first_paragraph:
                first_paragraph.append(line)
                active_section = "intro"
                continue
            if active_section == "intro":
                first_paragraph.append(line)
                continue
            if active_section == "members" and line.startswith("- "):
                name_part = line[2:].split(" - ", 1)[0].strip()
                name_part = re.sub(r"\s*\([^)]*\)\s*$", "", name_part).strip()
                entity_id = name_to_id.get(norm_key(name_part))
                if entity_id and entity_id not in members:
                    members.append(entity_id)
                continue
            if active_section == "notes":
                notes.append(line)

        coterie = {
            "id": coterie_id,
            "name": CANON_COTERIES[coterie_id]["name"],
            "type": "coterie",
            "faction": "Anarquistas",
            "base": CANON_COTERIES[coterie_id]["base"],
            "notes": " ".join(notes).strip() or " ".join(first_paragraph).strip(),
            "members": members,
            "members_expanded": members[:],
        }
        coteries.append(coterie)
        for member_id in members:
            by_member.setdefault(member_id, []).append(coterie_id)

    return coteries, by_member


def build_files_payload() -> tuple[dict[str, str], dict[str, str]]:
    files_html: dict[str, str] = {}
    files: dict[str, str] = {}

    ordered_sources = [
        (MIRROR / "00_BACKGROUND_JOGADORES", "jogadores", [
            "overview_sao_paulo.md",
            "seitas_e_politica.md",
            "mascarade_e_ameacas.md",
            "bairros_e_dominios.md",
            "rumores.md",
        ]),
        (MIRROR / "01_BACKGROUND_NARRADOR", "narrador", [
            "cronologia.md",
            "segredos_e_verdades.md",
            "tramas_em_andamento.md",
            "teia_de_conexoes.md",
            "index_personagens.md",
            "geopolitica_territorial.md",
            "coteries_e_associacoes.md",
            "painel_consolidado_faccoes_e_grupos.md",
            "relatorio_populacao_e_lacunas.md",
        ]),
        (MIRROR / "01_BACKGROUND_NARRADOR" / "faccoes", "narrador/faccoes", [
            "index.md",
            "Camarilla.md",
            "Anarquistas.md",
            "Independentes.md",
            "Mortal.md",
            "Segunda_Inquisicao.md",
        ]),
        (MIRROR / "04_ANTAGONISTAS_V5", "antagonistas", [
            "hunters.md",
            "second_inquisition.md",
            "sabbat.md",
            "werewolves.md",
            "ghosts_and_occult.md",
            "cults.md",
            "creatures_index.md",
        ]),
    ]

    for base_dir, prefix, names in ordered_sources:
        for name in names:
            path = base_dir / name
            if not path.exists():
                continue
            key = f"{prefix}/{name}"
            files[key] = key
            files_html[key] = md_to_html(sanitize_site_copy(read_text(path)))

    for clan_dir in sorted((MIRROR / "02_NPCS").iterdir(), key=lambda path: path.name):
        structure_file = clan_dir / "estrutura_do_cla.md"
        if not structure_file.exists():
            continue
        key = f"clas/{clan_dir.name}/estrutura_do_cla.md"
        files[key] = key
        files_html[key] = md_to_html(sanitize_site_copy(read_text(structure_file)))

    return files, files_html


def build_book_payload() -> tuple[dict[str, Any], list[str], list[str]]:
    current_data = load_current_skeleton()
    entities, missing, extras = build_canonical_entity_records(current_data)
    coteries, coteries_by_member = parse_coteries(entities)
    coteries_by_id = {coterie["id"]: coterie for coterie in coteries}

    for entity in entities:
        ids = coteries_by_member.get(entity["id"], [])
        entity["coteries"] = ids[:]
        entity["coteries_all"] = ids[:]
        if entity["kind"] == "ghoul" and not entity["serves_clans"]:
            entity["serves_clans"] = extract_served_clans(
                entity["docs"]["files"]["ficha_resumida"],
                entity["docs"]["files"]["historia"],
            )

    files, files_html = build_files_payload()

    counts = {
        "entities": len(entities),
        "kindred": sum(1 for entity in entities if entity.get("kind") == "kindred"),
        "ghouls": sum(1 for entity in entities if entity.get("kind") == "ghoul"),
        "mortals": sum(1 for entity in entities if entity.get("kind") == "mortal"),
    }

    payload = {
        "meta": {
            "title": "Sao Paulo by Night (V5) - Livro da Cronica",
            "chronicle_year": 2026,
        },
        "counts": counts,
        "entities": entities,
        "coteries": coteries,
        "coteries_by_id": coteries_by_id,
        "files": files,
        "files_html": files_html,
        "paths": current_data.get("paths")
        or {
            "map_html": "../06_MAPA_SP/mapa_sp_dominios.html",
            "teia_html": "../01_BACKGROUND_NARRADOR/teia_de_conexoes_mapa.html",
            "portraits_base": "../05_ASSETS/portraits/",
        },
    }
    return payload, missing, extras


def payload_with_paths(payload: dict[str, Any], *, docs_mode: bool) -> dict[str, Any]:
    cloned = json.loads(json.dumps(payload, ensure_ascii=False))
    if docs_mode:
        cloned["paths"] = {
            "portraits_base": "../assets/portraits/",
            "map_html": "../map/mapa_sp_dominios.html",
            "teia_html": "../teia/teia_de_conexoes_mapa.html",
        }
    else:
        cloned["paths"] = {
            "portraits_base": "../05_ASSETS/portraits/",
            "map_html": "../06_MAPA_SP/mapa_sp_dominios.html",
            "teia_html": "../01_BACKGROUND_NARRADOR/teia_de_conexoes_mapa.html",
        }
    return cloned


def replace_inline_json(index_path: Path, payload: dict[str, Any]) -> None:
    raw = read_text(index_path)
    dumped = json.dumps(payload, ensure_ascii=False)
    updated, count = re.subn(
        r'(<script id="bookDataJson" type="application/json">)(.*?)(</script>)',
        lambda match: match.group(1) + dumped + match.group(3),
        raw,
        count=1,
        flags=re.S,
    )
    if count != 1:
        raise RuntimeError(f"bookDataJson inline payload not found in {index_path}")
    write_text(index_path, updated)


def build_teia_title(entity: dict[str, Any], coterie_names: list[str]) -> str:
    domain_text = entity.get("domain_compact") or entity.get("domain") or "-"
    lines = [
        f"Nome: {entity.get('display_name') or '-'}",
        f"Tipo: {entity.get('kind') or '-'}",
    ]
    if entity.get("kind") == "kindred":
        lines.append(f"Clã: {entity.get('clan') or '-'}")
        lines.append(f"Seita: {entity.get('sect') or '-'}")
        lines.append(f"Função: {entity.get('role') or '-'}")
        lines.append(f"Domínio: {domain_text}")
        if coterie_names:
            lines.append(f"Coteries/associações: {', '.join(coterie_names)}")
        if entity.get("embrace_year"):
            lines.append(f"Abraço: {entity['embrace_year']}")
        lines.append(f"Tier: {entity.get('tier') or '-'}")
    else:
        lines.append(f"Vínculo: {entity.get('sect') or '-'}")
        lines.append(f"Papel: {entity.get('role') or '-'}")
        lines.append(f"Área: {domain_text}")
    return "\n".join(lines)


def sync_teia(payload: dict[str, Any]) -> None:
    entities_by_id = {entity["id"]: entity for entity in payload["entities"] if entity.get("id")}
    coterie_name_by_id = {
        coterie["id"]: coterie["name"] for coterie in payload.get("coteries") or []
    }

    for teia_path in TEIA_FILES:
        text = read_text(teia_path)
        match = re.search(r"(const NODES = )(\[.*?\])(;[\s\r\n]*const EDGES = )", text, re.S)
        if not match:
            raise RuntimeError(f"NODES payload not found in {teia_path}")
        nodes = json.loads(match.group(2))
        for node in nodes:
            entity = entities_by_id.get(node.get("id"))
            if not entity:
                continue
            coterie_names = [
                coterie_name_by_id[cid]
                for cid in entity.get("coteries") or []
                if cid in coterie_name_by_id
            ]
            node["file_stem"] = entity.get("file_stem") or node.get("file_stem")
            node["label"] = entity.get("display_name") or node.get("label")
            node["group"] = entity.get("clan") or node.get("group")
            node["kind"] = entity.get("kind") or node.get("kind")
            node["clan"] = entity.get("clan") or node.get("clan")
            node["sect"] = entity.get("sect") or node.get("sect")
            node["role"] = entity.get("role") or node.get("role")
            node["domain"] = entity.get("domain_compact") or entity.get("domain") or node.get("domain")
            node["tier"] = entity.get("tier") or node.get("tier")
            node["embrace_year"] = entity.get("embrace_year")
            node["coteries"] = coterie_names
            node["title"] = build_teia_title(entity, coterie_names)

        updated = (
            text[: match.start(2)]
            + json.dumps(nodes, ensure_ascii=False)
            + text[match.end(2) :]
        )
        updated = re.sub(
            r'\n\s*lines\.push\(""\);\n\s*lines\.push\("Tooltip:"\);\n\s*lines\.push\(n\.title \|\| ""\);\n',
            "\n",
            updated,
            count=1,
        )
        updated = re.sub(
            r"Vinculo mais usado \(canon DOCX, cap\. 8\.[23]\)",
            "Vínculo mais usado no índice canônico",
            updated,
        )
        write_text(teia_path, updated)


def map_pin_type(kind: str) -> str:
    if kind == "kindred":
        return "Vampiro"
    if kind == "ghoul":
        return "Ghoul"
    return "Mortal"


def first_domain_region(domain: str, fallback: str) -> str:
    raw = str(domain or "").strip()
    if not raw:
        return fallback
    return raw.split(" • ", 1)[0].strip().rstrip(".")


def sync_map(payload: dict[str, Any]) -> None:
    by_name = {
        norm_key(entity.get("display_name")): entity
        for entity in payload["entities"]
        if entity.get("display_name")
    }
    by_stem = {
        norm_key(entity.get("file_stem")): entity
        for entity in payload["entities"]
        if entity.get("file_stem")
    }

    for map_path in MAP_FILES:
        data = json.loads(read_text(map_path))
        for pin in data.get("npcs") or []:
            entity = by_name.get(norm_key(pin.get("name"))) or by_stem.get(
                norm_key(pin.get("portrait_stem"))
            )
            if not entity:
                continue
            domain_text = entity.get("domain_compact") or entity.get("domain") or ""
            pin["name"] = entity.get("display_name") or pin.get("name")
            pin["group"] = canonical_sect(entity.get("sect") or pin.get("group") or "")
            pin["faction"] = canonical_sect(entity.get("sect") or pin.get("faction") or "")
            if entity.get("kind") == "kindred":
                pin["subgroup"] = entity.get("clan") or pin.get("subgroup") or ""
            elif entity.get("serves_clans"):
                pin["subgroup"] = entity["serves_clans"][0]
            pin["clan"] = entity.get("clan") or pin.get("clan") or ""
            pin["tier"] = entity.get("tier") or pin.get("tier") or ""
            pin["npc_type"] = map_pin_type(entity.get("kind") or "mortal")
            pin["role"] = entity.get("role") or pin.get("role") or ""
            pin["domain_text"] = domain_text or pin.get("domain_text") or ""
            pin["region"] = first_domain_region(domain_text, pin.get("region") or "")
            pin["portrait_stem"] = entity.get("file_stem") or pin.get("portrait_stem")
        write_text(map_path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def write_book_payload(payload: dict[str, Any]) -> None:
    src_payload = payload_with_paths(payload, docs_mode=False)
    docs_payload = payload_with_paths(payload, docs_mode=True)
    write_text(BOOK_SRC_JSON, json.dumps(src_payload, ensure_ascii=False, indent=2) + "\n")
    write_text(BOOK_DOCS_JSON, json.dumps(docs_payload, ensure_ascii=False, indent=2) + "\n")
    replace_inline_json(BOOK_SRC_INDEX, src_payload)
    replace_inline_json(BOOK_DOCS_INDEX, docs_payload)


def main() -> int:
    payload, missing, extras = build_book_payload()
    write_book_payload(payload)
    sync_teia(payload)
    sync_map(payload)

    print(
        json.dumps(
            {
                "entities": payload["counts"]["entities"],
                "kindred": payload["counts"]["kindred"],
                "ghouls": payload["counts"]["ghouls"],
                "mortals": payload["counts"]["mortals"],
                "missing_in_mirror": missing,
                "mirror_extras_or_missing_history": extras,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
