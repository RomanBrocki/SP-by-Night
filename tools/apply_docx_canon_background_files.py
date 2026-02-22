from __future__ import annotations

import re
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANON = ROOT / "01_BACKGROUND_NARRADOR" / "canon_docx_integral.md"


def norm(s: str) -> str:
    s = (s or "").strip().lower()
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    s = re.sub(r"\s+", " ", s)
    return s


def parse_headings(md: str) -> list[tuple[int, int, str]]:
    out: list[tuple[int, int, str]] = []
    lines = md.splitlines()
    for i, ln in enumerate(lines):
        m = re.match(r"^(#{1,6})\s+(.*)$", ln)
        if not m:
            continue
        out.append((i, len(m.group(1)), m.group(2).strip()))
    return out


def section_by_heading(md: str, heading_contains: str) -> str:
    lines = md.splitlines()
    heads = parse_headings(md)
    key = norm(heading_contains)
    for idx, lvl, title in heads:
        if key not in norm(title):
            continue
        end = len(lines)
        for j, lvl2, _t2 in heads:
            if j <= idx:
                continue
            if lvl2 <= lvl:
                end = j
                break
        return "\n".join(lines[idx:end]).rstrip() + "\n"
    raise ValueError(f"heading not found: {heading_contains}")


def join_sections(*parts: str) -> str:
    out = []
    for p in parts:
        p = p.strip()
        if p:
            out.append(p)
    return "\n\n".join(out).rstrip() + "\n"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def extract_rumors(md: str) -> str:
    lines = md.splitlines()
    heads = parse_headings(md)
    chunks: list[str] = ["# Rumores de Sao Paulo (Canon DOCX)\n"]
    for idx, lvl, title in heads:
        t = norm(title)
        if "boatos" not in t and "rumor" not in t:
            continue
        end = len(lines)
        for j, lvl2, _ in heads:
            if j <= idx:
                continue
            if lvl2 <= lvl:
                end = j
                break
        body = "\n".join(lines[idx:end]).strip()
        if body:
            chunks.append(body)
    return "\n\n".join(chunks).rstrip() + "\n"


def main() -> int:
    if not CANON.exists():
        raise SystemExit(f"Arquivo canonico nao encontrado: {CANON}")
    md = CANON.read_text(encoding="utf-8")

    cap1 = section_by_heading(md, "capitulo 1")
    cap2 = section_by_heading(md, "capitulo 2")
    cap3 = section_by_heading(md, "capitulo 3")
    cap4 = section_by_heading(md, "capitulo 4")
    cap5 = section_by_heading(md, "capitulo 5")
    cap6 = section_by_heading(md, "capitulo 6")
    cap7 = section_by_heading(md, "capitulo 7")
    cap8 = section_by_heading(md, "capitulo 8")

    s11 = section_by_heading(md, "1.1")
    s12 = section_by_heading(md, "1.2")
    s13 = section_by_heading(md, "1.3")
    s14 = section_by_heading(md, "1.4")
    s15 = section_by_heading(md, "1.5")
    s16 = section_by_heading(md, "1.6")
    s17 = section_by_heading(md, "1.7")
    s29 = section_by_heading(md, "2.9")
    s39 = section_by_heading(md, "3.9")
    s48 = section_by_heading(md, "4.8")
    s65 = section_by_heading(md, "6.5")

    s72 = section_by_heading(md, "7.2")
    s73 = section_by_heading(md, "7.3")
    s74 = section_by_heading(md, "7.4")
    s75 = section_by_heading(md, "7.5")
    s76 = section_by_heading(md, "7.6")
    s77 = section_by_heading(md, "7.7")
    s7c = section_by_heading(md, "checklist de uso")

    s82 = section_by_heading(md, "8.2")
    s83 = section_by_heading(md, "8.3")

    # 00_BACKGROUND_JOGADORES
    write(ROOT / "00_BACKGROUND_JOGADORES" / "overview_sao_paulo.md", join_sections("# Visao Geral (Canon DOCX)", s11, s12, s13, s14))
    write(ROOT / "00_BACKGROUND_JOGADORES" / "seitas_e_politica.md", join_sections("# Seitas e Politica (Canon DOCX)", cap2, cap3, cap4, cap6))
    write(ROOT / "00_BACKGROUND_JOGADORES" / "mascarade_e_ameacas.md", join_sections("# Mascara e Ameacas (Canon DOCX)", s13, s14, s15, s72, s73, s74, s75))
    write(ROOT / "00_BACKGROUND_JOGADORES" / "bairros_e_dominios.md", join_sections("# Bairros e Dominios (Canon DOCX)", cap5))
    write(ROOT / "00_BACKGROUND_JOGADORES" / "rumores.md", extract_rumors(md))

    # 01_BACKGROUND_NARRADOR
    write(ROOT / "01_BACKGROUND_NARRADOR" / "segredos_e_verdades.md", join_sections("# Segredos e Verdades (Canon DOCX)", s17, section_by_heading(md, "2.2"), section_by_heading(md, "3.8"), section_by_heading(md, "4.2"), section_by_heading(md, "5.2")))
    write(ROOT / "01_BACKGROUND_NARRADOR" / "cronologia.md", join_sections("# Cronologia (Canon DOCX)", s16))
    write(ROOT / "01_BACKGROUND_NARRADOR" / "tramas_em_andamento.md", join_sections("# Tramas em Andamento (Canon DOCX)", s17, s29, s39, s48, s65, section_by_heading(md, "7.7")))
    write(ROOT / "01_BACKGROUND_NARRADOR" / "index_personagens.md", join_sections("# Index de Personagens (Canon DOCX)", s82, s83, "## Referencia de fichas essenciais\nVer capitulo 8.4 em `01_BACKGROUND_NARRADOR/canon_docx_integral.md`."))
    write(ROOT / "01_BACKGROUND_NARRADOR" / "coteries_e_associacoes.md", join_sections("# Coteries e Associacoes (Canon DOCX)", cap6))

    # 04_ANTAGONISTAS_V5
    write(ROOT / "04_ANTAGONISTAS_V5" / "second_inquisition.md", join_sections("# Segunda Inquisicao (Canon DOCX)", s72))
    write(ROOT / "04_ANTAGONISTAS_V5" / "hunters.md", join_sections("# Hunters (Canon DOCX)", s73))
    write(ROOT / "04_ANTAGONISTAS_V5" / "werewolves.md", join_sections("# Werewolves (Canon DOCX)", s74))
    write(ROOT / "04_ANTAGONISTAS_V5" / "sabbat.md", join_sections("# Sabbat (Canon DOCX)", s75))
    write(ROOT / "04_ANTAGONISTAS_V5" / "ghosts_and_occult.md", join_sections("# Ghosts and Occult (Canon DOCX)", s76))
    write(ROOT / "04_ANTAGONISTAS_V5" / "cults.md", join_sections("# Cults (Canon DOCX)", s77))
    write(ROOT / "04_ANTAGONISTAS_V5" / "creatures_index.md", join_sections("# Creatures Index (Canon DOCX)", s72, s73, s74, s75, s76, s77, s7c))

    print("[canon-bg] backgrounds and antagonists overwritten from DOCX canon")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

