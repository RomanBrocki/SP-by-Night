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


def normalize_entity(e: dict) -> dict:
    e.setdefault("kind", "ghoul")
    e.setdefault("clan", "")
    e.setdefault("sect", "")
    e.setdefault("role", "")
    e.setdefault("domain", "")
    e.setdefault("apparent_age", None)
    e.setdefault("embrace_year", None)
    e.setdefault("born_year", None)
    e.setdefault("sire", "")
    e.setdefault("childer", [])
    e.setdefault("disciplines_top3", "")
    e.setdefault("signature_style", "")
    e.setdefault("touchstones", [])
    e.setdefault("scene_hooks", [])
    e.setdefault("ambition", "")
    e.setdefault("fear", "")
    e.setdefault("secret", "")
    e.setdefault("false_rumor", "")
    e.setdefault("dangerous_truth", "")
    e.setdefault("tier", "C")
    e.setdefault("links", [])
    e.setdefault("full_sheet", "")
    e.setdefault("portrait_prompt", "")
    e.setdefault("appearance_explicit", "")
    e.setdefault("coteries", [])
    if not e.get("file_stem"):
        e["file_stem"] = stem(e.get("display_name") or "")
    return e


def main() -> int:
    if not SRC.exists():
        die(f"missing {SRC}")

    data = json.loads(SRC.read_text(encoding="utf-8"))
    entities = [e for e in (data.get("entities") or []) if isinstance(e, dict)]
    by_id = {e.get("id") for e in entities if e.get("id")}

    def add(e: dict) -> None:
        if not e.get("id"):
            die("new ghoul missing id")
        if not e.get("display_name"):
            die(f"{e['id']}: missing display_name")
        if e["id"] in by_id:
            return
        entities.append(normalize_entity(e))
        by_id.add(e["id"])

    # Add a "color pass" of relevant ghouls: politics, crime, logistics, cults, and enforcement.
    PACK = [
        # Camarilla: corte, Elysium, finanças, protocolo
        {
            "id": "ghoul_ricardo_protocolos",
            "display_name": "Ricardo \"Protocolos\" Nery",
            "sect": "Camarilla",
            "role": "Maitre de Elysium (lista, convite, humilhacao elegante)",
            "domain": "Paulista/Jardins",
            "born_year": 1986,
            "signature_style": "Terno preto impecavel, luvas finas, prancheta sem logo; sorriso que mede hierarquia.",
            "secret": "Ele mantem uma copia paralela da lista de entrada do Elysium com 'erros' propositais para identificar vazadores.",
            "links": [
                {"to": "ventrue_mateus_cordeiro", "type": "servant", "note": "executa protocolo e seleciona quem pode humilhar quem"},
                {"to": "toreador_luiza_salles", "type": "uneasy", "note": "Luiza o usa como instrumento; Ricardo nao esquece ser usado"},
            ],
            "coteries": ["assoc_corte_do_elysium"],
            "portrait_prompt": "Retrato realista, meio-corpo, homem com forma masculina, pessoa branca brasileira (pele clara), 39 anos, atraente de forma fria; cabelo castanho penteado, barba muito curta. Terno preto impecavel, luvas finas, prancheta discreta sem texto. Fundo: hall noturno com luz quente e cordao de isolamento. Sem texto, sem rabiscos nas maos.",
            "appearance_explicit": "pessoa branca brasileira (pele clara)",
        },
        {
            "id": "ghoul_lara_contencao",
            "display_name": "Lara \"Contencao\" Tavares",
            "sect": "Camarilla",
            "role": "Seguranca de Elysium (contencao sem sangue, camera sem prova)",
            "domain": "Liberdade/Paulista",
            "born_year": 1993,
            "signature_style": "Corte militar, jaqueta tatica sem insignia, olhar seco; fala pouco e move gente.",
            "secret": "Ela tem um acordo com um investigador mortal: entrega suspeitos para o Estado em troca de sumir com imagens.",
            "links": [
                {"to": "banuhaqim_samira_al_haddad", "type": "ally", "note": "Samira a usa como mao limpa fora da cadeia oficial"},
                {"to": "toreador_helena_vasconcelos", "type": "servant", "note": "Helena confia nela para proteger eventos sem virar escandalo"},
            ],
            "coteries": ["assoc_corte_do_elysium", "assoc_salao_pinheiros"],
            "portrait_prompt": "Retrato realista, meio-corpo, mulher com forma feminina, pessoa parda brasileira (pele marrom media), 32 anos, bonita de forma dura; cabelo raspado lateral com topo curto. Jaqueta tatica preta sem logos, luvas. Coldre discreto. Fundo: rua molhada com luz fria e reflexos. Sem texto, sem rabiscos nas maos.",
            "appearance_explicit": "pessoa parda brasileira (pele marrom media)",
        },
        {
            "id": "ghoul_paula_compliance",
            "display_name": "Paula \"Compliance\" Azevedo",
            "sect": "Camarilla",
            "role": "Advogada de crise (NDA, sumico, acordo extrajudicial)",
            "domain": "Morumbi/Campo Belo",
            "born_year": 1990,
            "signature_style": "Blazer claro, pasta de couro, oculos de aro fino; voz calma demais para a situacao.",
            "secret": "Ela sabe que uma empresa de vigilância atende sem perceber um grupo caçador; usa isso como alavanca dupla.",
            "links": [
                {"to": "ventrue_henrique_valadares", "type": "servant", "note": "tapa buracos juridicos e compra silencio em lote"},
                {"to": "ventrue_novo_12_raul_marques", "type": "uneasy", "note": "Raul prefere pancada; Paula prefere papel. Os dois se odeiam e se precisam"},
            ],
            "coteries": ["assoc_chaves_do_morumbi", "assoc_corte_do_elysium"],
            "portrait_prompt": "Retrato realista, meio-corpo, mulher com forma feminina, pessoa negra brasileira (pele escura), 35 anos, bonita e severa; cabelo preso baixo, oculos de aro fino. Blazer bege, pasta de couro sem marca. Fundo: sala de reuniao escura com luz lateral. Sem texto, sem rabiscos nas maos.",
            "appearance_explicit": "pessoa negra brasileira (pele escura)",
        },
        {
            "id": "ghoul_igor_motorista",
            "display_name": "Igor \"Sombra\" Camargo",
            "sect": "Camarilla",
            "role": "Motorista (rota, placa, porta traseira)",
            "domain": "Paulista/Jardins",
            "born_year": 1981,
            "signature_style": "Camisa social cinza, jaqueta discreta, luvas de motorista; olhar de retrovisor.",
            "secret": "Ele mantem um segundo carro sem documento, usado quando a noite vira investigacao mortal.",
            "links": [
                {"to": "ventrue_artur_macedo", "type": "servant", "note": "leva mensagens e pessoas; nunca pergunta o nome verdadeiro"},
                {"to": "ghoul_mariana_lobo", "type": "ally", "note": "ela controla a agenda; ele controla a rota"},
            ],
            "coteries": ["assoc_corte_do_elysium"],
            "portrait_prompt": "Retrato realista, meio-corpo, homem com forma masculina, pessoa parda brasileira (pele marrom clara), 44 anos, comum; cabelo curto, barba rala. Camisa social cinza e luvas de motorista; segura um chaveiro simples (1 chave) e um radio pequeno. Fundo: interior de carro com luz de rua. Sem texto, sem rabiscos nas maos.",
            "appearance_explicit": "pessoa parda brasileira (pele marrom clara)",
        },
        # Tremere: laboratório e contramedidas mortais
        {
            "id": "ghoul_renato_laboratorio",
            "display_name": "Renato \"Bico\" Sampaio",
            "sect": "Camarilla",
            "role": "Tecnico de laboratorio (amostras, descarte, chave de sala)",
            "domain": "Butanta/USP",
            "born_year": 1996,
            "signature_style": "Jaleco sujo, cracha virado, luvas nitrilicas; sempre cheira a alcool.",
            "secret": "Ele vende micro-informacao (horario, sala, nome) para quem pagar com coisa que nao e dinheiro.",
            "links": [
                {"to": "tremere_dario_kron", "type": "servant", "note": "faz a torre funcionar sem deixar rastro mortal"},
                {"to": "tremere_bianca_saramago", "type": "pressure", "note": "Bianca o pressiona por nomes e horarios"},
            ],
            "coteries": ["assoc_torre_usp"],
            "portrait_prompt": "Retrato realista, meio-corpo, homem com forma masculina, pessoa branca brasileira (pele clara), 29 anos, comum; cabelo curto baguncado. Jaleco amassado, luvas azuis, segura um saco de descarte biologico fechado (sem simbolos legiveis). Fundo: corredor de laboratorio frio. Sem texto, sem rabiscos nas maos.",
            "appearance_explicit": "pessoa branca brasileira (pele clara)",
        },
        # Toreador: midia, evento, vitrine
        {
            "id": "ghoul_camila_fotografa",
            "display_name": "Camila \"Flash\" Siqueira",
            "sect": "Camarilla",
            "role": "Fotografa de evento (imagem, corte, prova)",
            "domain": "Pinheiros/Moema",
            "born_year": 1999,
            "signature_style": "Camera pendurada, jaqueta jeans, brincos pequenos; sorriso facil e memoria perfeita.",
            "secret": "Ela tem fotos que podem derrubar um Primogeno, mas ainda nao decidiu por quem vender.",
            "links": [
                {"to": "toreador_luiza_salles", "type": "servant", "note": "transforma politica em imagem e imagem em arma"},
                {"to": "toreador_clara_montenegro", "type": "ally", "note": "hospitalidade e vitrine: Clara a protege quando convem"},
            ],
            "coteries": ["assoc_salao_pinheiros", "assoc_corte_do_elysium"],
            "portrait_prompt": "Retrato realista, meio-corpo, mulher com forma feminina, pessoa parda brasileira (pele marrom media), 26 anos, bonita; cabelo cacheado solto curto, brincos pequenos. Camera fotografica na mao (sem marca), jaqueta jeans com um patch discreto. Fundo: luzes de evento desfocadas. Sem texto, sem rabiscos nas maos.",
            "appearance_explicit": "pessoa parda brasileira (pele marrom media)",
        },
        # Lasombra: confissao e rede humana
        {
            "id": "ghoul_marcos_sacristao",
            "display_name": "Marcos \"Sacristao\" Vieira",
            "sect": "Camarilla",
            "role": "Sacristao e logistica (chaves, horarios, sala dos fundos)",
            "domain": "Bela Vista/Bixiga",
            "born_year": 1978,
            "signature_style": "Camisa branca simples, terco no bolso, maos manchadas de cera; olhar que evita camera.",
            "secret": "Ele sabe onde um confessor escondeu provas fisicas de uma quebra de Mascarada.",
            "links": [
                {"to": "lasombra_padre_miguel_aranha", "type": "servant", "note": "abre portas e fecha bocas na mesma noite"},
                {"to": "lasombra_novo_04_irma_beatriz_lemos", "type": "ally", "note": "ela cuida da culpa; ele cuida do corredor"},
            ],
            "coteries": ["assoc_confissao_preta", "assoc_corte_do_elysium"],
            "portrait_prompt": "Retrato realista, meio-corpo, homem com forma masculina, pessoa negra brasileira (pele escura), 47 anos, comum; cabelo raspado, barba curta. Camisa branca simples, terco discreto no bolso, segura um molho pequeno de chaves (3 chaves). Fundo: corredor antigo com luz amarela. Sem texto, sem rabiscos nas maos.",
            "appearance_explicit": "pessoa negra brasileira (pele escura)",
        },
        # Anarch: gangues, correios, crime e base territorial
        {
            "id": "ghoul_jessica_biqueira",
            "display_name": "Jessica \"Biqueira\" Ramos",
            "sect": "Anarch",
            "role": "Gerente de esquina (boca, aviso, caixa)",
            "domain": "Baronato Sul (Capao/Grajau)",
            "born_year": 1997,
            "signature_style": "Unhas longas pintadas, moletom largo, olhar rapido; sempre com dois celulares.",
            "secret": "Ela paga taxa dupla (baronato e policia) e usa os recibos como chantagem.",
            "links": [
                {"to": "gangrel_bia_matilha", "type": "ally", "note": "a rua sustenta a matilha; a matilha protege a rua"},
                {"to": "ministry_novo_08_vivi_fenda_lacerda", "type": "uneasy", "note": "culto quer tomar a esquina; Jessica nao aceita perder caixa"},
            ],
            "coteries": ["coterie_matilha_do_sul"],
            "portrait_prompt": "Retrato realista, meio-corpo, mulher com forma feminina, pessoa negra brasileira (pele escura), 28 anos, bonita e agressiva; cabelo preso em rabo alto, argola pequena. Moletom largo, unhas pintadas de vermelho escuro, dois celulares (um em cada mao) sem logos. Fundo: rua de noite com luz de poste. Sem texto, sem rabiscos nas maos.",
            "appearance_explicit": "pessoa negra brasileira (pele escura)",
        },
        {
            "id": "ghoul_rodrigo_fiel",
            "display_name": "Rodrigo \"Fiel\" Santana",
            "sect": "Anarch",
            "role": "Capanga (cobranca e 'resolucao')",
            "domain": "Baronato Mooca/Tatuape",
            "born_year": 1991,
            "signature_style": "Jaqueta de torcida, corrente simples, nariz quebrado; ri quando devia ficar quieto.",
            "secret": "Ele matou um homem errado por engano e a baronia apagou o caso; alguem tem o video.",
            "links": [
                {"to": "brujah_renata_ferraz", "type": "servant", "note": "faz cobranca e protege a imagem da baronia"},
                {"to": "ghoul_tiago_tranca", "type": "ally", "note": "Tiago manda; Rodrigo executa (e exagera)"},
            ],
            "coteries": ["coterie_ferrugem_mooca"],
            "portrait_prompt": "Retrato realista, meio-corpo, homem com forma masculina, pessoa parda brasileira (pele marrom media), 34 anos, feio memoravel; nariz quebrado, cicatriz na bochecha. Jaqueta de torcida sem logo, corrente simples. Segura um bastao telescopico fechado. Fundo: escadaria de estacao desfocada. Sem texto, sem rabiscos nas maos.",
            "appearance_explicit": "pessoa parda brasileira (pele marrom media)",
        },
        {
            "id": "ghoul_maya_hacker",
            "display_name": "Maya \"Backdoor\" Costa",
            "sect": "Anarch",
            "role": "Hacker e camera (apaga, injeta, rastreia)",
            "domain": "Baronato Mooca/Tatuape",
            "born_year": 2001,
            "signature_style": "Moletom com capuz, oculos redondos, fone; dedos com esmalte preto descascado.",
            "secret": "Ela vendeu um acesso antigo para um corretor independente e se arrependeu tarde.",
            "links": [
                {"to": "thinblood_katia_zero", "type": "ally", "note": "duas redes que se respeitam porque precisam"},
                {"to": "nosferatu_ester_gato_preto", "type": "uneasy", "note": "Ester tenta compra-la; Maya tenta nao virar propriedade"},
            ],
            "coteries": ["coterie_ferrugem_mooca"],
            "portrait_prompt": "Retrato realista, meio-corpo, mulher com forma feminina, pessoa branca brasileira (pele clara), 24 anos, bonita; cabelo curto descolorido, oculos redondos. Moletom preto, fone no pescoco, unhas pintadas de preto (descascado). Segura um notebook fechado sem logo. Fundo: luz de neon azul desfocada. Sem texto, sem rabiscos nas maos.",
            "appearance_explicit": "pessoa branca brasileira (pele clara)",
        },
        # Independentes: corredores (zona cinza) e Hecata
        {
            "id": "ghoul_eli_customs",
            "display_name": "Eli \"Despacho\" Araujo",
            "sect": "Independentes",
            "role": "Despachante (nota fiscal, placa e horario)",
            "domain": "Corredores (Barra Funda/Lapa)",
            "born_year": 1989,
            "signature_style": "Camisa social aberta, cracha velho, pasta plastica; fala rapido e some cedo.",
            "secret": "Ele forja documento para duas faccoes e mantem copia para se proteger.",
            "links": [
                {"to": "brujah_joao_do_trem", "type": "ally", "note": "Joao fornece rota; Eli fornece papel"},
                {"to": "nosferatu_nico_sombra", "type": "uneasy", "note": "Nico compra 'verdade de papel' quando precisa"},
            ],
            "coteries": ["assoc_corredores_de_sombra"],
            "portrait_prompt": "Retrato realista, meio-corpo, homem com forma masculina, pessoa parda brasileira (pele marrom clara), 36 anos, comum; cabelo curto, bigode fino. Camisa social aberta sem gravata, cracha velho sem texto legivel, pasta plastica na mao. Fundo: doca/galpao com luz fria. Sem texto, sem rabiscos nas maos.",
            "appearance_explicit": "pessoa parda brasileira (pele marrom clara)",
        },
        {
            "id": "ghoul_silvia_funebre",
            "display_name": "Silvia \"Funebre\" Prado",
            "sect": "Independentes",
            "role": "Diretora de funeraria (agenda, sala, 'preparo')",
            "domain": "Consolacao (cemiterios/funerarias)",
            "born_year": 1975,
            "signature_style": "Tailleur preto, lenço cinza, perfume de formol disfarçado; olhar sem pressa.",
            "secret": "Ela guarda um corpo que nao pode ser enterrado nem queimado, por ordem dos Hecata.",
            "links": [
                {"to": "hecata_donato_lazzari", "type": "servant", "note": "faz o enclave funcionar e apaga rastros no mundo mortal"},
                {"to": "hecata_celia_moura", "type": "ally", "note": "Celia cuida das chaves; Silvia cuida do calendario"},
            ],
            "coteries": ["assoc_enclave_cemiterios"],
            "portrait_prompt": "Retrato realista, meio-corpo, mulher com forma feminina, pessoa branca brasileira (pele clara), 50 anos, beleza fria (bonita, mas assustadora); cabelo castanho preso, batom vinho. Tailleur preto, lenço cinza. Segura um caderno de agenda fechado sem texto. Fundo: sala de funeraria com luz amarela e cortina pesada. Sem texto, sem rabiscos nas maos.",
            "appearance_explicit": "pessoa branca brasileira (pele clara)",
        },
    ]

    for e in PACK:
        add(e)

    data["entities"] = entities
    SRC.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"added={len(PACK)} (skips possible if ids existed)")
    print(f"wrote {SRC}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

