import json
import os
from collections import Counter, defaultdict


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SOURCE_JSON = os.path.join(ROOT, "tools", "sp_by_night_source.json")
MACRO_JSON = os.path.join(ROOT, "tools", "sp_macro_territories.json")
OUT_PATH = os.path.join(ROOT, "01_BACKGROUND_NARRADOR", "painel_consolidado_faccoes_e_grupos.md")


def _load(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _w(path: str, txt: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(txt.rstrip() + "\n")


def mortal_footprint(e: dict) -> list[str]:
    clan = (e.get("clan") or "").lower()
    role = (e.get("role") or "").lower()
    sect = (e.get("sect") or "").lower()
    out: list[str] = []

    if "ventrue" in clan:
        out += [
            "Financas e imobiliario (fundos, holdings, locacoes estrategicas).",
            "Influencia em seguranca privada e compliance (controle de acesso, camadas de permissao).",
            "Intermediacao via advogados, consultorias e fixers (apagamento de incidentes).",
            "Relacoes com elites corporativas (eventos, conselhos, patrocinios).",
        ]
    elif "toreador" in clan:
        out += [
            "Arte e midia (curadoria, eventos, reputacao e narrativas).",
            "Cenas noturnas (clubes, galerias, circulos VIP).",
            "Intermediacao social (listas, convites, portas que abrem e fecham).",
        ]
    elif "nosferatu" in clan:
        out += [
            "Infra, dados e rotas (camadas de acesso, 'quem sabe o caminho').",
            "Sumicos logisticos (entregas, galpoes, portoes, horarios).",
            "Mercado de informacao (dossies, chantagem, OSINT, vazamentos).",
        ]
    elif "brujah" in clan:
        out += [
            "Movimento de rua e protecao informal (bairro, torcida, sindicato, igreja local).",
            "Crime organizado de baixo perfil (cobranca, seguranca, 'taxa').",
            "Mediacao com liderancas comunitarias (favor por favor).",
        ]
    elif "banu" in clan or "haqim" in clan:
        out += [
            "Rede juridica e de investigacao (advocacia, auditoria, pressao oficial).",
            "Seguranca e resposta (pessoas que chegam rapido demais).",
            "Controle de risco e rastros (apagar evidencia, reescrever narrativa).",
        ]
    elif "tremere" in clan:
        out += [
            "Academia e laboratorios (pesquisa, bolsas, comites de etica como escudo).",
            "Ocultismo de vitrine (livrarias, palestras, grupos de estudo).",
            "Arquivos e burocracia (quem controla o registro controla a versao).",
        ]
    elif "hecata" in clan:
        out += [
            "Funerarias, cemiterios e logistica de corpo (o que some, some direito).",
            "Cartorios e registros (nome, documento, heranca).",
            "Intermediacao de dividas (boons como tabela, cobranca como ritual).",
        ]
    elif "lasombra" in clan:
        out += [
            "Igrejas, filantropia e bastidores (moral como ferramenta).",
            "Acordos de silencio (testemunha vira devota, nao delatora).",
            "Acesso a fundos escuros (quem paga, some).",
        ]
    elif "ministry" in clan:
        out += [
            "Cultos urbanos e recrutamento (influencia, vicio, promessa).",
            "Espacos de festa e culto (boate, after, salas privadas).",
            "Mercado de tentacao (a isca sempre parece escolha).",
        ]
    elif "malkavian" in clan:
        out += [
            "Rumor e previsao (padroes sociais, coincidencias, mensagens).",
            "Intervencoes pequenas com impacto grande (um telefonema muda tudo).",
        ]
    elif "gangrel" in clan:
        out += [
            "Rotas de carga, trilhas e fronteiras (batedores, escoltas, sumicos).",
            "Protecao de borda (onde a cidade vira mata, alguem manda).",
        ]
    else:
        out += [
            "Rede comunitaria e de bairro (associacoes, coletivos, liderancas locais).",
            "Mercado cinza e documentos (identidades descartaveis, sumico digital).",
            "Acesso informal a rotas e portas (segurancas, porteiros, motoristas).",
        ]

    if "principe" in role or "senescal" in role or "xerife" in role:
        out.append("Influencia em politica e protocolo (cadeia de comando, etiqueta, punicao).")
    if "anarch" in sect or "baron" in role or "barao" in role or "baronesa" in role:
        out.append("Controle territorial por lealdade (protecao, punicao, comunidade).")

    return out[:6]


def main() -> int:
    data = _load(SOURCE_JSON)
    macro = _load(MACRO_JSON) if os.path.exists(MACRO_JSON) else {}

    entities = [e for e in (data.get("entities") or []) if isinstance(e, dict)]
    kindred = [e for e in entities if e.get("kind") == "kindred"]
    coteries = [c for c in (data.get("coteries") or []) if isinstance(c, dict)]
    c_by_id = {c.get("id"): c for c in coteries if c.get("id")}

    # Counts
    sect_counts = Counter((e.get("sect") or "Mortal").strip() for e in kindred)
    clan_counts = Counter((e.get("clan") or "-").strip() for e in kindred)

    # Group kindred by sect
    by_sect: dict[str, list[dict]] = defaultdict(list)
    for e in kindred:
        by_sect[(e.get("sect") or "Mortal").strip()].append(e)
    for s in by_sect:
        by_sect[s].sort(key=lambda x: (x.get("tier") != "S", x.get("clan") or "", x.get("display_name") or ""))

    # Territories summary (macro)
    terr: list[dict] = []
    for bucket in ("macro", "anarch_baronatos", "independentes", "contested"):
        terr.extend(list(macro.get(bucket) or []))
    terr_by_faction: dict[str, list[dict]] = defaultdict(list)
    for t in terr:
        terr_by_faction[(t.get("faction") or "").strip()].append(t)

    # Build group (coterie/assoc) summary by faction
    groups_by_faction: dict[str, list[dict]] = defaultdict(list)
    for c in coteries:
        groups_by_faction[(c.get("faction") or "").strip() or "Sem faccao"].append(c)
    for f in groups_by_faction:
        groups_by_faction[f].sort(key=lambda x: x.get("name") or x.get("id") or "")

    lines: list[str] = []
    lines.append("# Painel Consolidado: Faccoes, Grupos e Quem E Quem (Sao Paulo by Night)")
    lines.append("")
    lines.append("Este arquivo e um consolidado do projeto. A ideia e responder, sem misterio:")
    lines.append("- quem e quem (por faccao e por papel)")
    lines.append("- por que esses blocos existem")
    lines.append("- por que a Camarilla tolera (ou nao consegue esmagar) certos enclaves")
    lines.append("")
    lines.append("## Contagem rapida (Cainitas nomeados)")
    lines.append(f"- Total: {len(kindred)}")
    for k in sorted(sect_counts.keys()):
        lines.append(f"- {k}: {sect_counts[k]}")
    lines.append("")
    lines.append("## Contagem por cla (Cainitas nomeados)")
    for k, v in sorted(clan_counts.items(), key=lambda kv: (-kv[1], kv[0])):
        lines.append(f"- {k}: {v}")
    lines.append("")

    lines.append("## O que sao Autarquicos e Independentes (e por que a Camarilla tolera)")
    lines.append("")
    lines.append("### Autarquicos (Centro Velho / cemiterios / pedagio)")
    lines.append("Autarquicos sao o bloco que se formou onde a Camarilla tem menos controle pratico: subsolo antigo, arquivo, cemiterio,")
    lines.append("rotas de passagem e lugares onde a cidade guarda memoria. Eles nao se apresentam como 'seita': se apresentam como servico inevitavel.")
    lines.append("")
    lines.append("Por que a Camarilla tolera Autarquicos (no lore deste projeto):")
    lines.append("- Porque reconquistar Centro Velho e caro e barulhento; barulho puxa a SI e expoe rastros.")
    lines.append("- Porque eles controlam servicos inevitaveis (passagem, registro, sumico de corpo) que a Camarilla precisa para manter a Mascara.")
    lines.append("- Porque o acordo cria previsibilidade: um lugar onde divida e cobrada em forma social, nao em manchete.")
    lines.append("")
    lines.append("O que a Camarilla exige em troca:")
    lines.append("- Nenhuma quebra de Mascara que vire padrao na vitrine.")
    lines.append("- Pedagio cobrado com discricao (sem pilha de corpos, sem video).")
    lines.append("")

    lines.append("### Independentes (Corredores / Zona Cinza de carga e sumico)")
    lines.append("Independentes sao o mercado que todo mundo usa e todo mundo nega: carga, doca, rota, correio e desaparecimento.")
    lines.append("Eles existem porque Sao Paulo e grande demais para um unico protocolo e porque a logistica sempre encontra um buraco.")
    lines.append("")
    lines.append("Por que a Camarilla tolera Independentes (no lore deste projeto):")
    lines.append("- Porque a Camarilla precisa de correio e passagem quando nao pode assinar a operacao.")
    lines.append("- Porque retomar corredores e caro e arriscado; o 'ganho' nao compensa a atencao mortal.")
    lines.append("- Porque corredores funcionam como valvula: trocas, encontros e descarte de evidencia sem amarrar ao Principe.")
    lines.append("")
    lines.append("O que os Independentes evitam para nao virar alvo:")
    lines.append("- Fazer politica aberta contra o Principe na vitrine.")
    lines.append("- Criar padrao de mortes ou sumicos que virem serie policial.")
    lines.append("")

    lines.append("## Territorios macro (mapa)")
    for faction in ["Camarilla", "Anarch", "Autarquicos", "Independentes", "Contestado"]:
        ts = terr_by_faction.get(faction) or []
        if not ts:
            continue
        lines.append("")
        lines.append(f"### {faction}")
        for t in ts:
            districts = ", ".join(t.get("districts") or [])
            leader = (t.get("leader_label") or "").strip() or "-"
            lines.append(f"- {t.get('label')}")
            lines.append(f"  lideranca: {leader}")
            if districts:
                lines.append(f"  distritos: {districts}")
            if (t.get("notes") or "").strip():
                lines.append(f"  nota: {t.get('notes').strip()}")

    lines.append("")
    lines.append("## Grupos (coteries/associacoes) e proposito")
    for faction in sorted(groups_by_faction.keys()):
        lines.append("")
        lines.append(f"### {faction}")
        for c in groups_by_faction[faction]:
            nm = (c.get("name") or c.get("id") or "").strip()
            if not nm:
                continue
            lines.append(f"- {nm}")
            if (c.get("type") or "").strip():
                lines.append(f"  tipo: {c.get('type')}")
            if (c.get("base") or "").strip():
                lines.append(f"  base: {c.get('base')}")
            if (c.get("notes") or "").strip():
                lines.append(f"  proposito: {c.get('notes').strip()}")
            mem = c.get("members") or []
            if mem:
                # show readable names
                names = []
                for mid in mem:
                    me = next((x for x in entities if x.get("id") == mid), None)
                    names.append(me.get("display_name") if me else str(mid))
                names = [n for n in names if n]
                lines.append("  membros:")
                for n in names[:18]:
                    lines.append(f"  - {n}")
                if len(names) > 18:
                    lines.append("  - ...")

    lines.append("")
    lines.append("## Cainitas por faccao (com atuacao e papel)")
    for sect in ["Camarilla", "Anarch", "Autarquicos", "Independentes"]:
        ms = by_sect.get(sect) or []
        if not ms:
            continue
        lines.append("")
        lines.append(f"### {sect} ({len(ms)})")
        for e in ms:
            name = e.get("display_name") or e.get("id")
            clan = e.get("clan") or "-"
            role = e.get("role") or "-"
            dom = e.get("domain") or "-"
            tier = e.get("tier") or "-"
            cids = e.get("coteries") or []
            cnames = []
            for cid in cids:
                meta = c_by_id.get(cid) or {}
                cnames.append((meta.get("name") or cid).strip())
            cnames = [x for x in cnames if x]

            lines.append(f"- {name} ({clan}; tier {tier})")
            lines.append(f"  papel: {role}")
            lines.append(f"  dominio: {dom}")
            fp = mortal_footprint(e)
            if fp:
                lines.append("  atuacao mortal:")
                for x in fp[:4]:
                    lines.append(f"  - {x}")
            if cnames:
                lines.append("  grupos:")
                for x in cnames[:6]:
                    lines.append(f"  - {x}")

    _w(OUT_PATH, "\n".join(lines))
    print(f"[build_city_consolidated_dossier] wrote {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
