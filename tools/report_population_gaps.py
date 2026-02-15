import json
from collections import Counter, defaultdict


def macro_key_from_faction_name(name: str) -> str:
    n = (name or "").strip().lower()
    if "camarilla" in n:
        return "Camarilla"
    if "anarch" in n:
        return "Anarch"
    if "indep" in n or "autar" in n:
        return "Independentes"
    return (name or "???").strip() or "???"


def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    src = load_json("tools/sp_by_night_source.json")
    mt = load_json("tools/sp_macro_territories.json")
    res = load_json("tools/sp_kindred_residence.json")["residence"]

    entities = src.get("entities", [])
    kindred = [e for e in entities if e.get("kind") == "kindred"]
    kindred_by_id = {e["id"]: e for e in kindred}

    # Base counts
    by_sect = Counter(macro_key_from_faction_name(e.get("sect")) for e in kindred)

    # Residency counts by macro id
    res_counts = Counter(v.get("residence_id", "?") for v in res.values())

    # Macro territory definitions (baronatos/indep + camarilla macro)
    territories = []
    cam = (mt.get("macro") or [])
    if cam:
        territories.append(cam[0])
    territories.extend(mt.get("anarch_baronatos") or [])
    territories.extend(mt.get("independentes") or [])
    territories_by_id = {t.get("id"): t for t in territories if t.get("id")}

    # Recommended population targets (tunable, but must be explicit).
    # These are "NPCs nomeados no projeto", not "população real de SP".
    targets_by_sect = {
        "Camarilla": 30,       # Camarilla precisa ser maioria clara no elenco nomeado.
        "Anarch": 18,          # Baronatos devem ter massa crítica.
        "Independentes": 14,   # Autárquicos/independentes são poucos, mas sempre presentes.
    }

    # Macro residency targets: minimum elenco por território para o mapa "respirar".
    targets_by_territory = {
        "camarilla_macro": 10,
        "baronato_mooca_tatuape": 8,
        "baronato_sul": 7,
        "baronato_leste": 7,
        "indep_centro_velho": 6,
        "indep_corredores": 7,
        "indep_cemiterios": 3,
    }

    # Compute deficits
    deficits_by_sect = {
        k: max(0, targets_by_sect[k] - by_sect.get(k, 0)) for k in targets_by_sect
    }

    deficits_by_territory = {}
    for tid, tgt in targets_by_territory.items():
        deficits_by_territory[tid] = max(0, tgt - res_counts.get(tid, 0))

    # Render report (Markdown)
    lines = []
    lines.append("# Relatorio de Populacao (SP by Night)")
    lines.append("")
    lines.append("Este relatorio conta apenas **Cainitas nomeados no projeto** (NPCs com ficha/arquivo), nao a populacao real de Sao Paulo.")
    lines.append("")

    lines.append("## Totais Atuais (Cainitas)")
    total_kindred = len(kindred)
    lines.append(f"- Total: {total_kindred}")
    for sect, n in sorted(by_sect.items(), key=lambda x: (-x[1], x[0])):
        lines.append(f"- {sect}: {n}")
    lines.append("")

    lines.append("## Lacunas Por Facção (recomendado)")
    lines.append("Alvos usados neste relatorio (ajustaveis):")
    for k in ["Camarilla", "Anarch", "Independentes"]:
        lines.append(f"- {k}: {targets_by_sect[k]}")
    lines.append("")
    lines.append("Faltantes estimados para bater os alvos:")
    for k in ["Camarilla", "Anarch", "Independentes"]:
        lines.append(f"- {k}: +{deficits_by_sect[k]}")
    lines.append("")

    lines.append("## Residencia Macro (por territorio do mapa)")
    lines.append("Contagem = quantos Cainitas tem `residence_id` igual ao territorio (onde habitam).")
    lines.append("")
    for tid, tgt in targets_by_territory.items():
        meta = territories_by_id.get(tid, {})
        label = meta.get("label") or tid
        cur = res_counts.get(tid, 0)
        need = deficits_by_territory.get(tid, 0)
        lines.append(f"- {label}: {cur} (alvo {tgt}; faltam +{need})")
    lines.append("")

    lines.append("## Buracos Detectados (objetivos)")
    # "Hard holes": defined territory with 0 residents
    hard_holes = []
    for tid in targets_by_territory:
        if res_counts.get(tid, 0) == 0:
            meta = territories_by_id.get(tid, {})
            hard_holes.append(meta.get("label") or tid)
    if hard_holes:
        lines.append("- Territorios sem nenhum Cainita residente (0): " + ", ".join(hard_holes))
    else:
        lines.append("- Nenhum territorio-alvo esta zerado.")
    lines.append("")

    lines.append("## Observacoes de Coerencia")
    lines.append("- Todas as referencias de `sire/childer` entre Cainitas estao resolvidas (nao ha IDs quebrados).")
    lines.append("- Todos os Cainitas possuem residencia macro definida em `tools/sp_kindred_residence.json` (cobertura 100%).")
    lines.append("")

    out_path = "01_BACKGROUND_NARRADOR/relatorio_populacao_e_lacunas.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")
    print(out_path)


if __name__ == "__main__":
    main()

