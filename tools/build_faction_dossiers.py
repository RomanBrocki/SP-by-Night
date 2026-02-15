import json
import os
from collections import defaultdict


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SOURCE_JSON = os.path.join(ROOT, "tools", "sp_by_night_source.json")
MACRO_JSON = os.path.join(ROOT, "tools", "sp_macro_territories.json")

OUT_DIR = os.path.join(ROOT, "01_BACKGROUND_NARRADOR", "faccoes")


FACTION_INTROS = {
    "Camarilla": (
        "A Camarilla em Sao Paulo e menos um partido e mais um **sistema operacional**: "
        "protocolos, acesso e contencao de dano. Ela domina a maior parte da cidade porque "
        "controla portas mortais (seguranca privada, eventos, midia, cartorios) e porque "
        "sabe fazer uma falha parecer 'caso isolado'.\n\n"
        "O preco e disciplina: quem alimenta fora de hora, fala fora de lugar, ou cria padrao "
        "mortal vira problema publico. E problema publico chama Lumen."
    ),
    "Anarch": (
        "Os Anarch aqui nao sao uma revolucao romantica: sao **governo de rua**. "
        "Eles seguram territórios que a Camarilla considera caros demais para retomar (logistica, risco, pouca vitrine) "
        "e sobrevivem porque criaram comunidade, rotas e retaliação.\n\n"
        "O pacto e simples: protecao em troca de obediencia local. Quem quebra, paga rapido e em publico."
    ),
    "Independentes": (
        "Os Independentes existem onde o protocolo falha: rota, carga, passagem, sumico. "
        "Eles nao querem governar a cidade; querem **cobrar pela cidade**.\n\n"
        "Por que a Camarilla tolera:\n"
        "- Porque a Camarilla usa esses servicos (correio, passagem, desaparecimento) quando nao pode assinar em cartorio.\n"
        "- Porque retomar corredor logistico e caro e barulhento; barulho puxa SI.\n"
        "- Porque um corredor 'neutro' serve como valvula: encontros, trocas, e descarte de prova.\n\n"
        "O acordo e simples: eles nao sabotam a Mascarada na vitrine, e a Camarilla finge que nao viu certos sumicos."
    ),
    "Autarquicos": (
        "Na pratica, 'Autarquicos' e o nome que a cidade da para quem sobrevive sem bandeira no Centro Velho. "
        "Eles funcionam como uma federacao de portas, arquivos e poroes: ninguem manda em tudo, "
        "mas todo mundo cobra um pedaco.\n\n"
        "Por que a Camarilla tolera:\n"
        "- Porque o Centro Velho e um campo minado de eco, arquivo e rotas antigas; reconquistar custa caro e expoe demais.\n"
        "- Porque os Autarquicos controlam servicos inevitaveis (cemiterio, funeraria, registro, passagem) que a Camarilla precisa.\n"
        "- Porque manter um acordo aqui reduz crise de Mascara: corpo some direito, registro some direito.\n\n"
        "Para jogadores: quando voce entra no Centro Velho, voce esta entrando num registro. "
        "Alguem vai lembrar que voce passou. A questao e quem."
    ),
    "Zona cinza": (
        "A Zona Cinza e o mercado que todo mundo nega e todo mundo usa: correios, sumicos, rotas e dados. "
        "Nao e um territorio 'ideologico'; e um territorio **funcional**.\n\n"
        "Aqui, a mascara cai por correlacao: camera, cracha, placa, horario. Quem repete padrao, perde."
    ),
    "Segunda Inquisicao": (
        "A Operacao Lumen (SI) em Sao Paulo nao governa bairro: governa **correlacao**. "
        "Eles cruzam incidente, padrao e imagem; nao precisam de prova perfeita, so de repeticao suficiente.\n\n"
        "Para o Narrador: trate SI como relogio. Cada cena barulhenta soma pontos. Quando passa do limite, "
        "eles entram com triagem, aprisionamento e 'limpeza'."
    ),
    "Mortal": (
        "Mortais relevantes que aparecem no projeto: contatos, alvos, liderancas institucionais. "
        "Nao sao 'neutros': cada um e uma porta (ou um risco) para alguem."
    ),
}


def _load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write(path: str, txt: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(txt.rstrip() + "\n")


def _fmt_entity_line(e: dict) -> str:
    clan = e.get("clan") or "-"
    role = e.get("role") or "-"
    domain = e.get("domain") or "-"
    kind = e.get("kind") or "-"
    # coteries in entities can be ids; dossiers should show readable names.
    cots = ", ".join(e.get("_coterie_names") or []) or "-"
    return f"- {e.get('display_name')} ({kind}; {clan}; {role}) | dominio: {domain} | coteries: {cots}"


def main() -> int:
    data = _load_json(SOURCE_JSON)
    macro = _load_json(MACRO_JSON)

    entities = data.get("entities") or []
    coteries_list = data.get("coteries") or []
    coteries = {c.get("id"): c for c in coteries_list if isinstance(c, dict) and c.get("id")}

    def coterie_names(ids):
        out = []
        for cid in ids or []:
            c = coteries.get(cid)
            if isinstance(c, dict) and c.get("name"):
                out.append(c["name"])
            else:
                out.append(str(cid))
        return out

    for e in entities:
        e["_coterie_names"] = coterie_names(e.get("coteries") or [])

    # Group members by sect
    members_by = defaultdict(list)
    for e in entities:
        sect = (e.get("sect") or "Mortal").strip()
        members_by[sect].append(e)

    # Build a quick macro territory summary keyed by faction
    territory_by_faction = defaultdict(list)
    for bucket in ("macro", "anarch_baronatos", "independentes", "contested"):
        for t in (macro.get(bucket) or []):
            territory_by_faction[(t.get("faction") or "").strip()].append(t)

    # Write index
    sects = sorted(members_by.keys())
    idx_lines = [
        "# Faccoes (indice)\n",
        "Arquivos detalhados por faccao:\n",
    ]
    for s in sects:
        safe = s.replace(" ", "_")
        idx_lines.append(f"- `{safe}.md` ({s})")
    _write(os.path.join(OUT_DIR, "index.md"), "\n".join(idx_lines))

    # Write per-faction dossiers
    for sect in sects:
        safe = sect.replace(" ", "_")
        ms = sorted(members_by[sect], key=lambda e: (e.get("kind") != "kindred", e.get("clan") or "", e.get("tier") or "", e.get("display_name") or ""))

        # Leadership heuristics
        leadership = []
        for e in ms:
            r = (e.get("role") or "").lower()
            if any(k in r for k in ["principe", "xerife", "senescal", "harpia", "primogeno", "primógeno", "barão", "barao", "baronesa"]):
                leadership.append(e)

        lines = [f"# {sect}\n"]
        intro = FACTION_INTROS.get(sect)
        if intro:
            lines.append(intro + "\n")

        # Territories
        lines.append("## Territorios (camada macro do mapa)\n")
        if sect in territory_by_faction:
            for t in territory_by_faction[sect]:
                leader = (t.get("leader_label") or "").strip() or "—"
                notes = (t.get("notes") or "").strip()
                districts = ", ".join(t.get("districts") or [])
                lines.append(f"- {t.get('label')} | lideranca: {leader}")
                lines.append(f"  distritos: {districts}")
                if notes:
                    lines.append(f"  nota: {notes}")
        else:
            lines.append("- (Sem macro-territorio definido.)")

        # Leadership list
        lines.append("\n## Lideranca e figuras-chave\n")
        if leadership:
            for e in leadership:
                lines.append(_fmt_entity_line(e))
        else:
            lines.append("- (Nenhuma lideranca marcada por papel; confira roles.)")

        # Member roster (kindred first)
        lines.append("\n## Membros (lista completa)\n")
        for e in ms:
            lines.append(_fmt_entity_line(e))

        _write(os.path.join(OUT_DIR, f"{safe}.md"), "\n".join(lines))

    print(f"[build_faction_dossiers] wrote {len(sects)} dossiers -> {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
