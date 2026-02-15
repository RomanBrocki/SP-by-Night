import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLAIMS = ROOT / "tools" / "sp_district_claims.json"
OUT = ROOT / "tools" / "sp_macro_territories.json"


def main() -> int:
    if not CLAIMS.exists():
        raise SystemExit(f"missing {CLAIMS}")
    data = json.loads(CLAIMS.read_text(encoding="utf-8"))
    dominant = data.get("dominant", {})
    disputes = data.get("disputes", {})
    pressures = data.get("pressures", {})

    districts = sorted(dominant.keys(), key=lambda x: x.lower())
    disputed_districts = sorted(disputes.keys(), key=lambda x: x.lower())

    anarch = {d for d, f in dominant.items() if f == "Anarch"}
    indep = {d for d, f in dominant.items() if f in ("Autarquicos", "Zona cinza")}

    # Camarilla macro: "a cidade e da Camarilla", exceto:
    # - bolsos Anarch/Independentes onde a Camarilla NAO domina
    # - disputas que NAO envolvem Camarilla (ex: Anarch vs Autarquicos)
    #
    # Regra da cronica:
    # - disputas Camarilla vs (outro) contam como Camarilla "ate nao serem mais"
    # - disputas entre terceiros nao viram territorio Camarilla por padrao
    cam = {d for d in districts if d not in anarch and d not in indep}

    for d in disputed_districts:
        meta = (disputes or {}).get(d) or {}
        between = meta.get("between", [])
        between = between if isinstance(between, list) else []
        if "Camarilla" in between:
            cam.add(d)
            anarch.discard(d)
            indep.discard(d)
        else:
            cam.discard(d)

    # Sub-territories (HOME BREW but aligned with current lore and district_claims):
    # - Anarch baronies
    baronatos = [
        {
            "id": "baronato_mooca_tatuape",
            "label": "Baronato Anarch: Mooca/Tatuape",
            "faction": "Anarch",
            "districts": ["MOOCA", "TATUAPE"],
            "leader_entity_id": "brujah_renata_ferraz",
            "leader_label": "Renata Ferraz (Baronesa da Mooca)",
            "notes": "Baronato estruturado. Protecao comunitaria com custo. Rotas e estacoes sao moeda.",
        },
        {
            "id": "baronato_sul",
            "label": "Baronato Anarch: Sul (Capao/Grajau)",
            "faction": "Anarch",
            "districts": ["CAPAO REDONDO", "CAMPO LIMPO", "GRAJAU", "JARDIM ANGELA", "JARDIM SAO LUIS"],
            "leader_entity_id": "gangrel_bia_matilha",
            "leader_label": "Bia \"Matilha\" (Baronesa do Sul, de fato)",
            "notes": "Zona que a Camarilla evita reconquistar: custo alto, risco alto, pouca vitrine. Paz tenue.",
        },
        {
            "id": "baronato_leste",
            "label": "Baronato Anarch: Leste (Itaquera/Extremo Leste)",
            "faction": "Anarch",
            "districts": ["ITAQUERA", "GUAIANASES", "CIDADE TIRADENTES", "SAO MATEUS", "SAPOPEMBA"],
            "leader_entity_id": "brujah_diego_itaquera",
            "leader_label": "Diego \"Itaquera\" Nascimento (Barao do Leste)",
            "notes": "Controle por rota e lealdade. O que vale aqui e quem chega primeiro e quem fica.",
        },
    ]

    independentes = [
        {
            "id": "indep_centro_velho",
            "label": "Independentes: Centro Velho (subsolo e eco)",
            "faction": "Independentes",
            "districts": ["SE", "REPUBLICA", "SANTA CECILIA", "BOM RETIRO", "CAMBUCI"],
            "leader_entity_id": "hecata_donato_lazzari",
            "leader_label": "Donato Lazzari (Hecata)",
            "notes": "Acordos de passagem, pedagios e rotas. O custo e sempre social antes de ser dinheiro.",
        },
        {
            "id": "indep_corredores",
            "label": "Independentes: Corredores (Zona Cinza de carga e sumico)",
            "faction": "Independentes",
            "districts": ["BARRA FUNDA", "LAPA", "VILA LEOPOLDINA", "JAGUARE", "JAGUARA", "RIO PEQUENO"],
            "leader_entity_id": "",
            "leader_label": "Conselho de corretores (acordo informal)",
            "notes": "Ninguem admite que manda. Todo mundo usa. Aqui territorio e horario, camera e cracha.",
        },
        {
            "id": "indep_cemiterios",
            "label": "Independentes: Cemiterios e funerarias (enclave)",
            "faction": "Independentes",
            "districts": ["CONSOLACAO"],
            "leader_entity_id": "hecata_donato_lazzari",
            "leader_label": "Donato Lazzari (Hecata)",
            "notes": "Enclave por acordo. A Camarilla tolera porque precisa. Quem quebra o acordo vira exemplo.",
        },
    ]

    contested = []
    for d, meta in (disputes or {}).items():
        between = (meta or {}).get("between", [])
        note = (meta or {}).get("note", "")
        contested.append(
            {
                "id": f"contestado_{d.lower()}",
                "label": f"Territorio contestado: {d} ({' vs '.join(between) if isinstance(between, list) else '-'})",
                "faction": "Contestado",
                "districts": [d],
                "between": between,
                "notes": note,
            }
        )
    contested = sorted(contested, key=lambda x: x["label"].lower())

    # Lupine risk is pressure, not ownership.
    lup = sorted([d for d, pr in (pressures or {}).items() if isinstance(pr, list) and "Risco lupino" in pr], key=lambda x: x.lower())

    out = {
        "meta": {
            "note": "Macro-territorios para o mapa (HOME BREW alinhado com o lore do projeto). Distritos usam ds_nome do GeoJSON oficial.",
        },
        "macro": [
            {
                "id": "camarilla_macro",
                "label": "Camarilla (macro): Marca d'agua da cidade",
                "faction": "Camarilla",
                "districts": sorted(cam, key=lambda x: x.lower()),
                "leader_entity_id": "ventrue_artur_macedo",
                "leader_label": "Artur Macedo (Principe)",
                "notes": "A Camarilla e o default: protocolo, acesso e silencio. Onde ela nao controla, ela ainda taxa.",
            }
        ],
        "anarch_baronatos": baronatos,
        "independentes": independentes,
        "contested": contested,
        "alerts": [
            {
                "id": "risco_lupino",
                "label": "Risco lupino (zonas de perigo; evitar predacao repetida)",
                "faction": "Risco lupino",
                "districts": lup,
                "notes": "Nao e dominio: e presenca registrada. Predacao repetida costuma virar retaliação.",
            }
        ],
    }

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
