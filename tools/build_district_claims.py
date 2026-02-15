import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GEOJSON_PATH = ROOT / "06_MAPA_SP" / "data" / "distritos-sp.geojson"
OUT_PATH = ROOT / "tools" / "sp_district_claims.json"


def _load_district_names() -> list[str]:
    gj = json.loads(GEOJSON_PATH.read_text(encoding="utf-8"))
    names = sorted({ft["properties"]["ds_nome"] for ft in gj.get("features", [])})
    return names


def main() -> int:
    if not GEOJSON_PATH.exists():
        raise SystemExit(f"missing: {GEOJSON_PATH}")

    districts = _load_district_names()
    dset = set(districts)

    # Dominant control is one label per district. Claims can have 2+ factions for contested districts.
    # Notes are intentionally explicit, so the ST can use them as-is.
    #
    # This is homebrew geopolitics tailored for this chronicle. It is not canon city material.
    dominant: dict[str, str] = {d: "Zona cinza" for d in districts}
    claims: dict[str, list[str]] = {d: [] for d in districts}
    disputes: dict[str, dict] = {}
    pressures: dict[str, list[str]] = {d: [] for d in districts}  # overlays that are not "control"

    def set_dom(ds: list[str], faction: str) -> None:
        for d in ds:
            if d not in dset:
                raise SystemExit(f"unknown district name: {d}")
            dominant[d] = faction

    def add_claim(ds: list[str], faction: str) -> None:
        for d in ds:
            if d not in dset:
                raise SystemExit(f"unknown district name: {d}")
            if faction not in claims[d]:
                claims[d].append(faction)

    def add_pressure(ds: list[str], pressure: str) -> None:
        for d in ds:
            if d not in dset:
                raise SystemExit(f"unknown district name: {d}")
            if pressure not in pressures[d]:
                pressures[d].append(pressure)

    def dispute(d: str, a: str, b: str, note: str) -> None:
        if d not in dset:
            raise SystemExit(f"unknown district name: {d}")
        disputes[d] = {"between": [a, b], "note": note}
        add_claim([d], a)
        add_claim([d], b)

    # Rebalance macro-politics: Camarilla holds the majority of districts (the city's "default" order).
    # Others hold a few strongholds, corridors, and edges.
    set_dom(districts, "Camarilla")
    add_claim(districts, "Camarilla")

    # Risco lupino: NAO e dominio de lobisomem. Sao distritos/areas onde a presenca foi registrada e a
    # predacao repetida costuma resultar em retaliação. Tratamos como "zona proibida" (overlay), mantendo
    # o controle politico Cainita como Camarilla no macro.
    add_pressure(["MARSILAC", "PARELHEIROS", "JARAGUA", "PERUS", "ANHANGUERA", "TREMEMBE", "JACANA"], "Risco lupino")

    # Autarquicos: Centro Velho e zonas onde "o nome pesa mais que o documento".
    aut = ["SE", "REPUBLICA", "SANTA CECILIA", "BOM RETIRO", "CAMBUCI"]
    set_dom(aut, "Autarquicos")
    add_claim(aut, "Autarquicos")

    # Zona cinza: logistica, cargas, sumicos e intermediarios (ninguem admite, todo mundo usa).
    zc = ["BARRA FUNDA", "LAPA", "VILA LEOPOLDINA", "JAGUARE", "JAGUARA", "RIO PEQUENO"]
    set_dom(zc, "Zona cinza")
    add_claim(zc, "Zona cinza")

    # Anarch: baronatos periféricos (Leste + Sul + bolsões no Norte). Controle se mede por rua e lealdade.
    # Keep Anarch as a set of clear baronies, not a majority.
    anarch_core = [
        "MOOCA",
        "TATUAPE",
        "ITAQUERA",
        "GUAIANASES",
        "CIDADE TIRADENTES",
        "SAO MATEUS",
        "SAPOPEMBA",
        "CAPAO REDONDO",
        "CAMPO LIMPO",
        "GRAJAU",
        "JARDIM ANGELA",
        "JARDIM SAO LUIS",
    ]
    set_dom(anarch_core, "Anarch")
    add_claim(anarch_core, "Anarch")

    # Disputas: onde o controle muda de mao "por semana" e qualquer erro vira incidente de Mascara.
    dispute(
        "BRAS",
        "Autarquicos",
        "Camarilla",
        "O Bras e corredor de carga e gente. Autarquicos cobram 'passagem' nas galerias; Camarilla tenta comprar portas e impor 'ordem'. Quando os dois cobram na mesma noite, sobra sangue no asfalto.",
    )
    dispute(
        "MOOCA",
        "Anarch",
        "Autarquicos",
        "A Mooca e disputa por rotas e abrigo: Anarch controlam quarteiroes; Autarquicos controlam portas (cartorios, arquivos, poroes). Quem nao tem guia, se perde.",
    )
    dispute(
        "TATUAPE",
        "Anarch",
        "Camarilla",
        "Tatuape e vitrine de consumo com periferia ao redor. Camarilla quer etiqueta e 'ordem'; Anarch querem rua e autonomia. A guerra aqui e de reputacao e desaparecimentos.",
    )
    dispute(
        "BUTANTA",
        "Camarilla",
        "Anarch",
        "Butanta mistura campus, pesquisa e bolsoes populares. Camarilla quer a fachada academica; Anarch querem as rotas e os corpos. Segredos de laboratorio viram moeda.",
    )
    dispute(
        "JABAQUARA",
        "Camarilla",
        "Anarch",
        "Jabaquara e no de transito, hotel e contrabando. Camarilla compra portas; Anarch controlam quem entra e sai. O que some aqui raramente reaparece inteiro.",
    )
    dispute(
        "IPIRANGA",
        "Autarquicos",
        "Anarch",
        "No Ipiranga a historia vira arma. Autarquicos manipulam memoria e patrimonio; Anarch inflamam rua e torcida. Qualquer ritual antigo aqui chama atencao errada.",
    )
    dispute(
        "VILA PRUDENTE",
        "Autarquicos",
        "Anarch",
        "Vila Prudente e fronteira viva. O lado que controla a estacao controla a noite. Quando muda, muda rapido e com testemunhas mortais demais.",
    )
    dispute(
        "LAPA",
        "Camarilla",
        "Zona cinza",
        "A Lapa e dinheiro e logistica. Camarilla quer estabilidade e contratos; a Zona cinza vende sumico e acesso. A disputa e silenciosa: auditoria, chantagem, incendio 'acidental'.",
    )

    # Pressoes (overlays): Segunda Inquisicao e pulsos Sabbat. Nao e "dominio"; e risco.
    add_pressure(["BELA VISTA", "CONSOLACAO", "REPUBLICA", "SE", "CAMPO BELO", "SANTO AMARO"], "Segunda Inquisicao")
    add_pressure(["VILA LEOPOLDINA", "BARRA FUNDA", "JAGUARE"], "Sabbat")

    # Ensure every district has at least one claim: default to its dominant controller.
    for d in districts:
        if not claims[d]:
            claims[d] = [dominant[d]]

    out = {
        "meta": {
            "note": "Geopolitica por distritos (HOME BREW) para o mapa real. Nomes batem com distritos-sp.geojson (ds_nome, uppercase).",
            "source_geojson": "06_MAPA_SP/data/distritos-sp.geojson",
        },
        "dominant": dominant,
        "claims": claims,
        "disputes": disputes,
        "pressures": pressures,
    }
    OUT_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
