from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGETS = [ROOT / "02_NPCS", ROOT / "03_SERVOS_E_CONTATOS"]
REPORT = ROOT / "tools" / "history_polish_report.md"


def collect_files() -> list[Path]:
    out: list[Path] = []
    for base in TARGETS:
        if base.exists():
            out.extend(sorted(base.rglob("*_historia.txt")))
    return out


def first_name(text: str) -> str:
    for ln in text.splitlines():
        t = ln.strip()
        if t:
            return t
    return "Este personagem"


def extract_domain(text: str) -> str:
    m = re.search(r"^- Dominio:\s*([^\|\n]+)", text, flags=re.MULTILINE)
    if m:
        return m.group(1).strip()
    m = re.search(r"^- Area:\s*([^\n]+)", text, flags=re.MULTILINE)
    if m:
        return m.group(1).strip()
    return "sua area de atuacao"


def clean_sentence(s: str) -> str:
    s = (s or "").strip()
    s = s.strip(". ")
    s = re.sub(r"\s+", " ", s)
    return s


def rewrite_ambition_block(text: str) -> tuple[str, int]:
    changed = 0
    who = first_name(text)
    dom = extract_domain(text)

    p1 = re.compile(
        r"A ambicao e direta:\s*(?P<a>.+?)\.\s*"
        r"Em cena, isso aparece em escolhas concretas de prazo, risco e custo dentro de\s*(?P<ctx>.+?)\.\s*"
        r"O medo e igualmente pratico:\s*(?P<m>.+?)\.\s*"
        r"Quando o tema encosta na mesa, a pessoa acelera decis[aã]o, reduz plateia e tenta controlar a vers[aã]o antes da verdade circular\.",
        flags=re.IGNORECASE | re.DOTALL,
    )

    def r1(m: re.Match[str]) -> str:
        nonlocal changed
        changed += 1
        amb = clean_sentence(m.group("a"))
        fear = clean_sentence(m.group("m"))
        ctx = clean_sentence(m.group("ctx")) or dom
        return (
            f"A ambicao de {who} e {amb}. Na pratica, isso orienta decisoes no eixo de {ctx}, "
            "com foco em discricao, tempo de resposta e controle de danos. "
            f"O medo principal e {fear}. Quando esse risco aparece, {who} reduz exposicao, "
            "limita testemunhas e muda o plano para preservar a rede."
        )

    text = p1.sub(r1, text)

    p2 = re.compile(
        r"A ambicao e direta:\s*(?P<a>.+?)\.\s*"
        r"O medo e igualmente pratico:\s*(?P<m>.+?)\.",
        flags=re.IGNORECASE | re.DOTALL,
    )

    def r2(m: re.Match[str]) -> str:
        nonlocal changed
        changed += 1
        amb = clean_sentence(m.group("a"))
        fear = clean_sentence(m.group("m"))
        return (
            f"A ambicao de {who} e {amb}. O medo principal e {fear}. "
            f"No territorio de {dom}, isso torna cada acordo mais tenso e cada erro mais caro."
        )

    text = p2.sub(r2, text)

    p3 = re.compile(
        r"A ambicao e:\s*(?P<a>.+?)\.\.?\s*O medo e:\s*(?P<m>.+?)\.\.?",
        flags=re.IGNORECASE | re.DOTALL,
    )

    def r3(m: re.Match[str]) -> str:
        nonlocal changed
        changed += 1
        amb = clean_sentence(m.group("a"))
        fear = clean_sentence(m.group("m"))
        return (
            f"A ambicao de {who} e {amb}. O medo central e {fear}. "
            f"Em {dom}, essa tensao define como a pessoa negocia, recua ou ataca."
        )

    text = p3.sub(r3, text)

    # Residual variant after first-pass rewrites.
    p4 = re.compile(
        r"A ambicao de (?P<who>.+?) e (?P<a>.+?)\.\s*"
        r"Em cena, isso aparece em escolhas concretas de prazo, risco e custo dentro de\s*(?P<ctx>.+?)\.\s*"
        r"O medo principal e (?P<m>.+?)\.\s*"
        r"No territorio de (?P<dom>.+?), isso torna cada acordo mais tenso e cada erro mais caro\.\s*"
        r"Quando o tema encosta na mesa, a pessoa acelera decis[aã]o, reduz plateia e tenta controlar a vers[aã]o antes da verdade circular\.",
        flags=re.IGNORECASE | re.DOTALL,
    )

    def r4(m: re.Match[str]) -> str:
        nonlocal changed
        changed += 1
        who2 = clean_sentence(m.group("who")) or who
        amb = clean_sentence(m.group("a"))
        fear = clean_sentence(m.group("m"))
        ctx = clean_sentence(m.group("ctx"))
        dom2 = clean_sentence(m.group("dom")) or dom
        return (
            f"A ambicao de {who2} e {amb}. Na pratica, isso se traduz em rotina operacional no eixo de {ctx}, "
            "com foco em manter influencia sem gerar rastro desnecessario. "
            f"O medo principal e {fear}. Em {dom2}, {who2} evita exposicao longa, corta intermediarios instaveis "
            "e prefere acordos verificaveis."
        )

    text = p4.sub(r4, text)

    p5 = re.compile(
        r"Quando sente esse risco, a pessoa troca conveni[eê]ncia por conten[cç][aã]o\.",
        flags=re.IGNORECASE,
    )
    if p5.search(text):
        text = p5.sub(f"Quando percebe esse risco, {who} reduz exposicao e prioriza controle de dano.", text)
        changed += 1

    return text, changed


def polish_scenes(text: str) -> tuple[str, int]:
    changed = 0
    # "- Cena: X. X. ..." -> "- Cena: X. ..."
    p_dup = re.compile(r"(- Cena:\s*)([^.\n]+)\.\s*\2\.\s*", flags=re.IGNORECASE)

    def rdup(m: re.Match[str]) -> str:
        nonlocal changed
        changed += 1
        return f"{m.group(1)}{m.group(2)}. "

    text = p_dup.sub(rdup, text)

    # Replace a very repetitive generic hook line.
    generic = "Um encontro pequeno vira custo grande."
    if generic in text:
        text = text.replace(
            generic,
            "Uma reuniao aparentemente simples revela uma cobranca antiga e coloca os PJs sob avaliacao local.",
        )
        changed += 1

    # Collapse accidental double periods left by generation.
    new = re.sub(r"\.\.(?=\s|$)", ".", text)
    if new != text:
        changed += 1
        text = new
    return text, changed


def main() -> int:
    files = collect_files()
    total_changes = 0
    touched = 0
    details: list[str] = []

    for p in files:
        raw = p.read_text(encoding="utf-8", errors="ignore")
        t1, c1 = rewrite_ambition_block(raw)
        t2, c2 = polish_scenes(t1)
        c = c1 + c2
        if c > 0 and t2 != raw:
            p.write_text(t2, encoding="utf-8", newline="\n")
            touched += 1
            total_changes += c
            details.append(f"- `{p.relative_to(ROOT).as_posix()}`: {c} ajustes")

    rep: list[str] = []
    rep.append("# History Polish Report")
    rep.append("")
    rep.append(f"- Arquivos verificados: **{len(files)}**")
    rep.append(f"- Arquivos alterados: **{touched}**")
    rep.append(f"- Ajustes aplicados (aprox): **{total_changes}**")
    rep.append("")
    rep.append("## Detalhe")
    if details:
        rep.extend(details)
    else:
        rep.append("- Nenhuma alteracao necessaria.")

    REPORT.write_text("\n".join(rep).rstrip() + "\n", encoding="utf-8")
    print(f"wrote {REPORT}")
    print(f"files={len(files)} touched={touched} changes={total_changes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
