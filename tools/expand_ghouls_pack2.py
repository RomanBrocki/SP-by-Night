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

    PACK = [
        # Camarilla: Isabel e Helena
        {
            "id": "ghoul_marcela_cartorio",
            "display_name": "Marcela \"Cartorio\" Guimaraes",
            "sect": "Camarilla",
            "role": "Escritura e apagamento (cartorio, procuração, 'segunda via')",
            "domain": "Itaim/Berrini",
            "born_year": 1982,
            "signature_style": "Blusa de seda, cabelo preso, caneta de metal; sorriso de quem sabe o atalho.",
            "secret": "Ela tem uma pasta de 'segundas vias' que não existem para a lei, mas existem para a noite.",
            "links": [
                {"to": "ventrue_isabel_amaral", "type": "servant", "note": "Isabel controla nomes; Marcela controla papel"},
                {"to": "ventrue_henrique_valadares", "type": "uneasy", "note": "Henrique tenta compra-la; ela cobra caro demais"},
            ],
            "coteries": ["assoc_chaves_do_morumbi", "assoc_corte_do_elysium"],
            "portrait_prompt": "Retrato realista, meio-corpo, mulher com forma feminina, pessoa branca brasileira (pele clara), 43 anos, bonita e calculista; cabelo preso baixo, batom nude. Blusa de seda e caneta de metal na mao. Fundo: corredor corporativo quente. Sem texto, sem rabiscos nas maos.",
            "appearance_explicit": "pessoa branca brasileira (pele clara)",
        },
        {
            "id": "ghoul_yuri_curador",
            "display_name": "Yuri \"Curador\" Sato",
            "sect": "Camarilla",
            "role": "Equipe de Elysium (cenografia, alcool, saida de emergencia)",
            "domain": "Liberdade",
            "born_year": 1994,
            "signature_style": "Camisa preta, pulseira fina, olhar de quem mede fluxo de gente.",
            "secret": "Ele guarda uma chave de saida que so existe em dias de evento.",
            "links": [
                {"to": "toreador_helena_vasconcelos", "type": "servant", "note": "Helena cuida do Elysium; Yuri cuida do corpo do evento"},
                {"to": "toreador_daniel_sato", "type": "ally", "note": "Daniel planta rumor; Yuri escolhe onde ele cai"},
            ],
            "coteries": ["assoc_salao_pinheiros", "assoc_corte_do_elysium"],
            "portrait_prompt": "Retrato realista, meio-corpo, homem com forma masculina, pessoa japonesa-brasileira (pele clara), 31 anos, atraente; cabelo preto liso medio, sem barba. Camisa preta, pulseira fina, segura uma chave de emergencia vermelha (sem texto). Fundo: luzes vermelhas de saida desfocadas. Sem texto, sem rabiscos nas maos.",
            "appearance_explicit": "pessoa japonesa-brasileira (pele clara)",
        },
        # Anarch: Mooca e Leste
        {
            "id": "ghoul_nando_desmanche",
            "display_name": "Nando \"Desmanche\" Alves",
            "sect": "Anarch",
            "role": "Desmanche e documento (carro quente, placa fria)",
            "domain": "Baronato Mooca/Tatuape",
            "born_year": 1988,
            "signature_style": "Macacao manchado de graxa, chave inglesa, tatuagem no antebraco.",
            "secret": "Ele ja desmontou um carro de viatura descaracterizada; guardou o rastreador.",
            "links": [
                {"to": "caitiff_rafa_ferro", "type": "ally", "note": "Rafa protege; Nando fornece fuga"},
                {"to": "brujah_renata_ferraz", "type": "servant", "note": "taxa em pecas e silencio"},
            ],
            "coteries": ["coterie_ferrugem_mooca"],
            "portrait_prompt": "Retrato realista, meio-corpo, homem com forma masculina, pessoa parda brasileira (pele marrom media), 37 anos, comum; cabelo curto, barba falhada. Macacao manchado de graxa, chave inglesa na mao. Fundo: oficina com luz amarela. Sem texto, sem rabiscos nas maos.",
            "appearance_explicit": "pessoa parda brasileira (pele marrom media)",
        },
        {
            "id": "ghoul_paula_olheira",
            "display_name": "Paula \"Olheira\" Nascimento",
            "sect": "Anarch",
            "role": "Olheira de rua (aviso, filmagem, fuga a pe)",
            "domain": "Baronato Leste (Itaquera/Extremo Leste)",
            "born_year": 2002,
            "signature_style": "Boné, mochila pequena, tenis gasto; celular sempre no modo aviao.",
            "secret": "Ela gravou um caçador mortal em acao e nao contou para ninguem ainda.",
            "links": [
                {"to": "brujah_diego_itaquera", "type": "servant", "note": "Diego manda: Paula ve primeiro"},
                {"to": "thinblood_ana_carbono", "type": "ally", "note": "Ana some gente; Paula some imagem"},
            ],
            "coteries": ["coterie_leste_de_aco"],
            "portrait_prompt": "Retrato realista, meio-corpo, mulher com forma feminina, pessoa negra brasileira (pele escura), 23 anos, bonita; bone preto, mochila pequena, fone no pescoco. Segura celular com tela apagada. Fundo: rua com pichacao desfocada (sem texto legivel). Sem texto, sem rabiscos nas maos.",
            "appearance_explicit": "pessoa negra brasileira (pele escura)",
        },
        # Sul: criminosos/ponte
        {
            "id": "ghoul_wesley_corredor",
            "display_name": "Wesley \"Corredor\" Dias",
            "sect": "Anarch",
            "role": "Motoqueiro de rota (sangue, arma, gente)",
            "domain": "Baronato Sul (Capao/Grajau)",
            "born_year": 1999,
            "signature_style": "Jaqueta de moto com fita refletiva, capacete gasto, luvas.",
            "secret": "Ele tem uma rota que cruza borda verde e nunca contou para a baronia.",
            "links": [
                {"to": "ghoul_marcelo_moto", "type": "rival", "note": "os dois disputam quem entrega primeiro e quem volta vivo"},
                {"to": "gangrel_bia_matilha", "type": "servant", "note": "Bia cobra respeito; Wesley cobra gasolina"},
            ],
            "coteries": ["coterie_matilha_do_sul"],
            "portrait_prompt": "Retrato realista, meio-corpo, homem com forma masculina, pessoa parda brasileira (pele marrom clara), 26 anos, atraente; jaqueta de moto com fita refletiva, capacete na mao. Fundo: posto a noite com chuva. Sem texto, sem rabiscos nas maos.",
            "appearance_explicit": "pessoa parda brasileira (pele marrom clara)",
        },
        # Independentes: mais um da zona cinza
        {
            "id": "ghoul_teresa_balanca",
            "display_name": "Teresa \"Balanca\" Pacheco",
            "sect": "Independentes",
            "role": "Controle de doca (fila, balanca, camera 'cego')",
            "domain": "Corredores (Barra Funda/Lapa)",
            "born_year": 1980,
            "signature_style": "Colete refletivo, prancheta, olhar de quem manda sem parecer.",
            "secret": "Ela sabe a senha de um DVR antigo que guarda meses de imagens.",
            "links": [
                {"to": "ghoul_eli_customs", "type": "ally", "note": "papel e balanca: juntos criam passagem"},
                {"to": "nosferatu_nico_sombra", "type": "client", "note": "vende janela de camera por dado moral"},
            ],
            "coteries": ["assoc_corredores_de_sombra"],
            "portrait_prompt": "Retrato realista, meio-corpo, mulher com forma feminina, pessoa branca brasileira (pele clara), 45 anos, comum; colete refletivo sem texto, prancheta. Fundo: doca com containers desfocados. Sem texto, sem rabiscos nas maos.",
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

