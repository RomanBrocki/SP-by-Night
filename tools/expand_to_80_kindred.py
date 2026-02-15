"""
Expande `tools/sp_by_night_source.json` para um total alvo de 80 Cainitas (kindred),
adicionando NPCs novos de forma deterministica e coerente com o lore do projeto.

Uso:
  python tools/expand_to_80_kindred.py

Depois rode:
  python tools/build_kindred_residence.py
  python tools/build_macro_territories.py
  python tools/generate_sp_by_night.py --all --overwrite
  python tools/validate_project_coherence.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "tools" / "sp_by_night_source.json"


def die(msg: str) -> None:
    raise SystemExit(msg)


def stem(s: str) -> str:
    s = (s or "").strip()
    s = s.replace('"', "").replace("'", "")
    s = re.sub(r"[^A-Za-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "NPC"


def ensure_required(e: dict) -> None:
    if not e.get("id"):
        die("entity missing id")
    if not e.get("kind"):
        die(f"{e['id']}: missing kind")
    if not e.get("display_name"):
        die(f"{e['id']}: missing display_name")
    if not e.get("file_stem"):
        e["file_stem"] = stem(e["display_name"])
    # Keep fields present so downstream writers don't produce weird half-lines.
    for k in [
        "clan",
        "sect",
        "role",
        "domain",
        "sire",
        "disciplines_top3",
        "signature_style",
        "ambition",
        "fear",
        "secret",
        "false_rumor",
        "dangerous_truth",
        "tier",
        "full_sheet",
        "portrait_prompt",
        "appearance_explicit",
    ]:
        e.setdefault(k, "")
    e.setdefault("childer", [])
    e.setdefault("touchstones", [])
    e.setdefault("scene_hooks", [])
    e.setdefault("links", [])


def main() -> int:
    if not SRC.exists():
        die(f"missing {SRC}")

    data = json.loads(SRC.read_text(encoding="utf-8"))
    entities = list(data.get("entities") or [])
    if not isinstance(entities, list):
        die("sp_by_night_source.json: entities must be a list")

    by_id = {e.get("id"): e for e in entities if isinstance(e, dict) and e.get("id")}

    def add(e: dict) -> None:
        ensure_required(e)
        eid = e["id"]
        if eid in by_id:
            die(f"duplicate id: {eid}")
        by_id[eid] = e
        entities.append(e)

    existing_kindred = [e for e in entities if isinstance(e, dict) and e.get("kind") == "kindred"]
    if len(existing_kindred) > 80:
        die(f"already has {len(existing_kindred)} kindred; expected <= 80")

    # Final intended totals after expansion (aligned with lore: SP is Camarilla):
    # - Kindred total: 80
    # - Camarilla: 49
    # - Anarch: 17
    # - Autarquico: 14
    #
    # We add exactly (80 - current_kindred) kindred, and a small set of ghouls for key nodes.

    # "Anchor" ids to keep the teia connected.
    anchors = {
        "Ventrue": "ventrue_artur_macedo",
        "Toreador": "toreador_luiza_salles",
        "Tremere": "tremere_dario_kron",
        "Nosferatu": "nosferatu_nico_sombra",
        "Banu Haqim": "banuhaqim_samira_al_haddad",
        "Lasombra": "lasombra_padre_miguel_aranha",
        "Malkavian": "malkavian_paulo_vidente",
        "Hecata": "hecata_donato_lazzari",
        "Ministry": "ministry_talita_serpente",
        "Brujah": "brujah_renata_ferraz",
        "Gangrel": "gangrel_bia_matilha",
        "Ravnos": "ravnos_maru_vento",
        "Tzimisce": "tzimisce_nina_costura",
        "Caitiff": "caitiff_rafa_ferro",
        "Thin Blood": "thinblood_katia_zero",
        "Salubri": "salubri_irene_da_luz",
    }

    # Handcrafted "high value" NPCs (new leadership + territory holes + barons).
    special_kindred: list[dict] = [
        {
            "id": "malkavian_marcia_falcao",
            "kind": "kindred",
            "clan": "Malkavian",
            "sect": "Camarilla",
            "display_name": "Marcia Falcao",
            "role": "Primogena Malkavian (ouvinte do padrao)",
            "domain": "Consolacao/Higienopolis (consultorios, jornais e bastidores)",
            "apparent_age": 42,
            "embrace_year": 1971,
            "born_year": 1929,
            "tier": "A",
            "links": [
                {"to": "toreador_luiza_salles", "type": "ally", "note": "etiqueta em troca de previsao; controle por vias diferentes"},
                {"to": "ventrue_artur_macedo", "type": "uneasy", "note": "o Principe tolera, mas nao gosta de ser lido"},
            ],
            "full_sheet": "Ficha completa (Primogena Malkavian) - resumo:\n- Disciplinas: Auspex alto; Dominate/Obfuscate moderados.\n- Papel: leitura de risco, contrainteligencia social.\n",
            "portrait_prompt": "Retrato cinematografico, meio-corpo, mulher com forma feminina, pessoa branca brasileira (pele clara), 42 anos aparentes, beleza discreta e inquietante (atraente, mas nao glamour); coque baixo desalinhado, olheiras leves, olhos castanhos muito atentos. Blazer de tweed cinza, gola alta preta, broche pequeno em forma de olho. Luz fria de consultorio a noite, arquivos desfocados ao fundo. Sem texto, sem rabiscos nas maos, sem chaves aleatorias.",
            "appearance_explicit": "pessoa branca brasileira (pele clara)",
        },
        {
            "id": "toreador_clara_montenegro",
            "kind": "kindred",
            "clan": "Toreador",
            "sect": "Camarilla",
            "display_name": "Clara Montenegro",
            "role": "Primogena Toreador (curadora de vitrine e faca)",
            "domain": "Moema/Paraiso (galerias, hospitais e patronato)",
            "apparent_age": 33,
            "embrace_year": 1999,
            "born_year": 1966,
            "sire": "toreador_luiza_salles",
            "tier": "A",
            "links": [
                {"to": "toreador_luiza_salles", "type": "boon_due", "note": "Luiza a elevou; Clara paga com obediencia publica e faca privada"},
                {"to": "ventrue_mateus_cordeiro", "type": "ally", "note": "protocolo e vitrine: o mesmo controle com outra musica"},
            ],
            "full_sheet": "Ficha completa (Primogena Toreador) - resumo:\n- Disciplinas: Presence dominante.\n- Papel: patronato, saude/arte como cobertura.\n",
            "portrait_prompt": "Retrato editorial sofisticado, meio-corpo, mulher com forma feminina, pessoa branca brasileira (pele oliva clara), 33 anos, muito bela (olhar predatorio contido); bob preto liso com franja reta, batom vinho fosco. Vestido preto geometrico, brincos pequenos de ouro. Taca de vinho tinto (sem etiqueta). Fundo de gala noturna desfocado. Sem texto, sem rabiscos nas maos.",
            "appearance_explicit": "pessoa branca brasileira (pele clara/oliva)",
        },
        {
            "id": "nosferatu_raimundo_rato_rei",
            "kind": "kindred",
            "clan": "Nosferatu",
            "sect": "Camarilla",
            "display_name": "Raimundo \"Rato-Rei\"",
            "role": "Primogeno Nosferatu (cartografo do subsolo)",
            "domain": "Perdizes/Barra Funda (dutos e rotas de fuga)",
            "apparent_age": 50,
            "embrace_year": 1964,
            "born_year": 1903,
            "sire": "nosferatu_vovo_zilda",
            "tier": "A",
            "links": [
                {"to": "nosferatu_nico_sombra", "type": "rival", "note": "informacao vs infraestrutura: dois reis no mesmo subsolo"},
                {"to": "ventrue_artur_macedo", "type": "ally", "note": "rotas discretas por favores pesados"},
            ],
            "full_sheet": "Ficha completa (Primogeno Nosferatu) - resumo:\n- Disciplinas: Obfuscate/Animalism.\n- Papel: rotas, sumicos, infra.\n",
            "portrait_prompt": "Retrato sombrio, meio-corpo, homem com forma masculina, pessoa parda/negra brasileira (pele marrom escura), 50 anos, feio memoravel (cicatrizes, nariz quebrado, dentes irregulares), olhos pequenos brilhantes. Capuz impermeavel, luvas grossas, lanterna industrial. Fundo: tunel molhado com canos. Sem texto, sem rabiscos nas maos.",
            "appearance_explicit": "pessoa parda/negra brasileira (pele marrom escura)",
        },
        {
            "id": "banuhaqim_nadia_nasser",
            "kind": "kindred",
            "clan": "Banu Haqim",
            "sect": "Camarilla",
            "display_name": "Nadia Nasser",
            "role": "Primogena Banu Haqim (juiza de protocolo e sangue)",
            "domain": "Ipiranga/Cursino (tribunais, cartorios e segredos)",
            "apparent_age": 38,
            "embrace_year": 2003,
            "born_year": 1979,
            "sire": "banuhaqim_samira_al_haddad",
            "tier": "A",
            "links": [
                {"to": "banuhaqim_samira_al_haddad", "type": "mentor", "note": "Samira a treinou como sucessora segura para a corte"},
                {"to": "ventrue_artur_macedo", "type": "employer", "note": "tribunal quando punicao precisa parecer justa"},
            ],
            "full_sheet": "Ficha completa (Primogena Banu Haqim) - resumo:\n- Disciplinas: Blood Sorcery moderado.\n- Papel: julgamento, execucao limpa.\n",
            "portrait_prompt": "Retrato juridico-noir, meio-corpo, mulher com forma feminina, pessoa brasileira de origem arabe (pele oliva media), 38 anos, bonita e severa; cabelo preto ondulado preso, cicatriz pequena no queixo. Blazer preto, lenco vinho. Segura um selo de cartorio antigo. Fundo: corredor de cartorio antigo. Sem texto, sem rabiscos nas maos.",
            "appearance_explicit": "pessoa brasileira de origem arabe (pele oliva media)",
        },
        {
            "id": "ventrue_henrique_valadares",
            "kind": "kindred",
            "clan": "Ventrue",
            "sect": "Camarilla",
            "display_name": "Henrique Valadares",
            "role": "Primogeno Ventrue (financas de guerra)",
            "domain": "Morumbi/Campo Belo (fundos, seguranca e condominio)",
            "apparent_age": 46,
            "embrace_year": 1984,
            "born_year": 1937,
            "sire": "ventrue_isabel_amaral",
            "tier": "A",
            "links": [
                {"to": "ventrue_isabel_amaral", "type": "boon_due", "note": "Isabel o elevou; ele paga com caixa e obediencia"},
                {"to": "ventrue_artur_macedo", "type": "ally", "note": "caixa e escudo em troca de influencia real"},
            ],
            "full_sheet": "Ficha completa (Primogeno Ventrue) - resumo:\n- Papel: caixa, lavagem, seguranca.\n",
            "portrait_prompt": "Retrato corporativo tenso, meio-corpo, homem com forma masculina, pessoa branca brasileira (pele clara), 46 anos, atraente e frio; cabelo castanho-escuro com grisalho nas temporas, barba curta. Terno grafite fosco. Fundo: sacada de cobertura com chuva e luzes da cidade. Sem texto, sem rabiscos nas maos.",
            "appearance_explicit": "pessoa branca brasileira (pele clara)",
        },
        # Anarch: Barao novo para dar lider claro no Leste.
        {
            "id": "brujah_diego_itaquera",
            "kind": "kindred",
            "clan": "Brujah",
            "sect": "Anarch",
            "display_name": "Diego \"Itaquera\" Nascimento",
            "role": "Barao do Leste (Itaquera e Extremo Leste)",
            "domain": "Baronato Leste (Itaquera/Extremo Leste)",
            "apparent_age": 34,
            "embrace_year": 2012,
            "born_year": 1978,
            "tier": "A",
            "links": [
                {"to": "brujah_renata_ferraz", "type": "ally", "note": "paz entre baronatos enquanto a Camarilla observa"},
                {"to": "ravnos_maru_vento", "type": "employer", "note": "mensagens e rotas; paga com protecao"},
            ],
            "full_sheet": "Ficha completa (Barao do Leste) - resumo:\n- Disciplinas: Celerity/Potence.\n- Papel: territorio, comunidade, fronteira.\n",
            "portrait_prompt": "Retrato de rua, meio-corpo, homem com forma masculina, pessoa parda brasileira (pele marrom media), 34 anos, bonito de forma dura; cicatriz na sobrancelha. Jaqueta esportiva preta com detalhes vermelhos. Taco de madeira no ombro (sem logos). Fundo: arquibancada vazia sob luz de refletor. Sem texto, sem rabiscos nas maos.",
            "appearance_explicit": "pessoa parda brasileira (pele marrom media)",
        },
        # Independentes: preencher enclave de cemiterios (1 novo Hecata).
        {
            "id": "hecata_celia_moura",
            "kind": "kindred",
            "clan": "Hecata",
            "sect": "Autarquico",
            "display_name": "Celia Moura",
            "role": "Agente funeraria (enclave de cemiterio)",
            "domain": "Consolacao (cemiterios, funerarias e chaves)",
            "apparent_age": 41,
            "embrace_year": 2008,
            "born_year": 1967,
            "sire": "hecata_donato_lazzari",
            "tier": "B",
            "links": [
                {"to": "hecata_donato_lazzari", "type": "servant", "note": "operadora do enclave; ela faz o acordo valer na pratica"},
                {"to": "salubri_irene_da_luz", "type": "ally", "note": "cura e morte conversam no mesmo corredor"},
            ],
            "portrait_prompt": "Retrato atmosferico, meio-corpo, mulher com forma feminina, pessoa parda brasileira (pele marrom media), 41 anos, bonita triste; trança baixa, luvas finas. Sobretudo preto, lenço cinza. Fundo: portao do cemiterio da Consolacao com neblina. Sem texto, sem rabiscos nas maos.",
            "appearance_explicit": "pessoa parda brasileira (pele marrom media)",
        },
    ]

    # Deterministic roster generator for "corpo de cidade" NPCs:
    # Enough to reach exactly 80 kindred while keeping prompts individualized and diverse.
    roster: list[dict] = []
    roster.extend(special_kindred)

    # Build additional kindred until we hit 80 total kindred.
    def cur_kindred_count() -> int:
        return len([e for e in entities if isinstance(e, dict) and e.get("kind") == "kindred"]) + len(
            [e for e in roster if e.get("kind") == "kindred"]
        )

    def mk_body(
        idx: int,
        clan: str,
        sect: str,
        name: str,
        role: str,
        domain: str,
        skin: str,
        gender: str,
        beauty: str,
    ) -> dict:
        slug = clan.lower().replace(" ", "")
        eid = f"{slug}_novo_{idx:02d}_{stem(name).lower()}"
        g = "mulher com forma feminina" if gender == "mulher" else "homem com forma masculina"
        prompt = (
            f"Retrato individual realista, meio-corpo, {g}, {skin}, {beauty}; rosto e expressao unicos; "
            f"roupa e acessorios coerentes com {role}. Fundo coerente com {domain}. "
            "Sem texto na imagem, sem rabiscos nas maos, sem chaves aleatorias."
        )
        return {
            "id": eid,
            "kind": "kindred",
            "clan": clan,
            "sect": sect,
            "display_name": name,
            "role": role,
            "domain": domain,
            "apparent_age": 26 + (idx % 20),
            "embrace_year": 2005 + (idx % 20),
            "born_year": 1975 + (idx % 25),
            "tier": "C" if idx % 5 else "B",
            "links": [{"to": anchors.get(clan, "ventrue_artur_macedo"), "type": "contact", "note": "ponte para a politica local"}],
            "portrait_prompt": prompt,
            "appearance_explicit": skin,
        }

    # Curated entries (names chosen to match ethnicity cues; enough diversity for SP).
    curated = [
        ("Camarilla", "Toreador", "Aiko Tanaka", "Harpia de bairro (Pinheiros)", "Pinheiros/Vila Madalena", "pessoa japonesa-brasileira (pele clara)", "mulher", "muito bela"),
        ("Camarilla", "Nosferatu", "Leandro Batista", "Operador de cameras (Paulista)", "Paulista/Jardins", "pessoa negra brasileira (pele escura)", "homem", "comum"),
        ("Camarilla", "Tremere", "Maira Koehler", "Guardia de grimorios (USP)", "Butanta/USP", "pessoa branca brasileira (pele clara; tracos germano-brasileiros)", "mulher", "bonita"),
        ("Camarilla", "Lasombra", "Irma Beatriz Lemos", "Confessora auxiliar (Bixiga)", "Bela Vista/Bixiga", "pessoa negra brasileira (pele escura)", "mulher", "bonita"),
        ("Camarilla", "Ventrue", "Eduardo Nogueira", "Fornecedor de Elysium (Paulista)", "Paulista", "pessoa branca brasileira (pele clara)", "homem", "atraente"),
        ("Camarilla", "Malkavian", "Miriam Kwon", "Leitora de padroes (bolsa)", "Itaim Bibi", "pessoa coreano-brasileira (pele clara)", "mulher", "bonita"),
        ("Camarilla", "Gangrel", "Bruno Arantes", "Batedor de borda (parques)", "Alto de Pinheiros/Butanta", "pessoa parda brasileira (pele marrom media)", "homem", "atraente"),
        ("Anarch", "Ministry", "Vivi \"Fenda\" Lacerda", "Recrutadora (Sul)", "Baronato Sul (Capao/Grajau)", "pessoa branca brasileira (pele clara)", "mulher", "muito bela"),
        ("Anarch", "Gangrel", "Jonas \"Capim\"", "Batedor (Sul)", "Baronato Sul (Capao/Grajau)", "pessoa parda brasileira (pele marrom media)", "homem", "comum"),
        ("Anarch", "Thin Blood", "Bruna \"Sinais\"", "Correio e drone (Sul)", "Baronato Sul (Capao/Grajau)", "pessoa negra brasileira (pele escura)", "mulher", "bonita"),
        ("Anarch", "Brujah", "Sabrina Siqueira", "Organizadora de ocupacao (Sul)", "Baronato Sul (Capao/Grajau)", "pessoa parda brasileira (pele marrom clara)", "mulher", "atraente"),
    ]

    idx = 1
    for sect, clan, name, role, domain, skin, gender, beauty in curated:
        roster.append(mk_body(idx, clan, sect, name, role, domain, skin, gender, beauty))
        idx += 1

    # Fill remaining slots as Camarilla neonates/ancillae, anchored to the court.
    filler_specs = [
        ("Ventrue", "Camarilla", "Raul Marques", "Hound do Xerife (cobrador)", "Santana/Tucuruvi", "pessoa parda brasileira (pele marrom media)", "homem", "atraente"),
        ("Banu Haqim", "Camarilla", "Farid Alvim", "Auditor de sangue (campo)", "Ipiranga/Cursino", "pessoa brasileira de origem arabe (pele oliva)", "homem", "bonito"),
        ("Toreador", "Camarilla", "Renata Freire", "Produtora de moda (noite)", "Jardim Paulista", "pessoa branca brasileira (pele clara)", "mulher", "muito bela"),
        ("Nosferatu", "Camarilla", "Taina Aruana", "Sondadora de redes (subsolo)", "Perdizes/Barra Funda", "pessoa indigena brasileira (pele bronze/cobre)", "mulher", "bonita"),
        ("Caitiff", "Camarilla", "Caio \"Papel\"", "Portador de recados (util)", "Centro Expandido", "pessoa parda brasileira (pele marrom clara)", "homem", "comum"),
    ]

    for clan, sect, name, role, domain, skin, gender, beauty in filler_specs:
        roster.append(mk_body(idx, clan, sect, name, role, domain, skin, gender, beauty))
        idx += 1

    # Now add deterministic generic Camarilla bodies until we hit 80.
    generic_names = [
        ("Ventrue", "Camarilla", "Helio Barros", "Gestor de predio (fachada)", "Morumbi/Campo Belo", "pessoa branca brasileira (pele clara)", "homem"),
        ("Toreador", "Camarilla", "Sofia Pires", "Curadora de sala (Elysium)", "Liberdade", "pessoa parda brasileira (pele marrom media)", "mulher"),
        ("Nosferatu", "Camarilla", "Nara Sato", "Sombra de entrega (correio)", "Bras/Pari", "pessoa japonesa-brasileira (pele clara)", "mulher"),
        ("Tremere", "Camarilla", "Igor Menezes", "Analista de risco (oculto)", "Butanta/USP", "pessoa negra brasileira (pele escura)", "homem"),
        ("Lasombra", "Camarilla", "Severino Carmo", "Advogado da confissao", "Bela Vista/Bixiga", "pessoa branca brasileira (pele clara)", "homem"),
        ("Malkavian", "Camarilla", "Celia Andrade", "Cinegrafista de rumor", "Paulista", "pessoa parda brasileira (pele marrom media)", "mulher"),
    ]

    gn = 0
    while cur_kindred_count() < 80:
        clan, sect, name, role, domain, skin, gender = generic_names[gn % len(generic_names)]
        beauty = ["comum", "bonito", "bonita", "feio memoravel"][gn % 4]
        roster.append(mk_body(idx, clan, sect, f"{name} {gn+1}", role, domain, skin, gender, beauty))
        idx += 1
        gn += 1
        if idx > 300:
            die("safety stop: too many iterations building roster")

    if cur_kindred_count() != 80:
        die(f"kindred count mismatch after build: {cur_kindred_count()} (expected 80)")

    for e in roster:
        add(e)

    # Minimal ghouls for the new primogenes/barons (teia needs servants too).
    new_ghouls = [
        {
            "id": "ghoul_damiao_portaria",
            "kind": "ghoul",
            "sect": "Camarilla",
            "display_name": "Damiao \"Portaria\"",
            "role": "Retentor (seguranca e acesso em condominios)",
            "domain": "Morumbi/Campo Belo",
            "born_year": 1983,
            "tier": "C",
            "links": [{"to": "ventrue_henrique_valadares", "type": "servant", "note": "acesso, vigilância, chaves-mestras"}],
            "portrait_prompt": "Retrato realista, meio-corpo, homem com forma masculina, pessoa parda brasileira (pele marrom media), 52 anos, uniforme escuro sem insignia, radio no ombro. Fundo: portaria com luz fria. Sem texto, sem rabiscos nas maos.",
            "appearance_explicit": "pessoa parda brasileira (pele marrom media)",
        },
        {
            "id": "ghoul_sonia_atelie",
            "kind": "ghoul",
            "sect": "Camarilla",
            "display_name": "Sonia \"Atelie\"",
            "role": "Retentora (figurinista e disfarces)",
            "domain": "Moema/Paraiso",
            "born_year": 1991,
            "tier": "C",
            "links": [{"to": "toreador_clara_montenegro", "type": "servant", "note": "disfarces, figurino, identidades de evento"}],
            "portrait_prompt": "Retrato realista, meio-corpo, mulher com forma feminina, pessoa negra brasileira (pele escura), 44 anos, fita metrica no pescoco, tesoura pequena fechada. Fundo: atelie com tecidos desfocados. Sem texto, sem rabiscos nas maos.",
            "appearance_explicit": "pessoa negra brasileira (pele escura)",
        },
    ]

    for g in new_ghouls:
        add(g)

    data["entities"] = entities
    SRC.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {SRC}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
