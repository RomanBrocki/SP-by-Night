import json
import os


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SOURCE_JSON = os.path.join(ROOT, "tools", "sp_by_night_source.json")


def _by_id(entities):
    return {e["id"]: e for e in entities}


def _add_entity(entities, e):
    ids = {x["id"] for x in entities}
    if e["id"] in ids:
        return False
    entities.append(e)
    return True


def main() -> int:
    with open(SOURCE_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    entities = data.get("entities") or []
    idx = _by_id(entities)

    def require(id_):
        if id_ not in idx:
            raise SystemExit(f"missing required entity id: {id_}")
        return id_

    # Masters we are attaching to (must exist).
    artur = require("ventrue_artur_macedo")
    luiza = require("toreador_luiza_salles")
    renata = require("brujah_renata_ferraz")
    diego = require("brujah_diego_itaquera")
    nico = require("nosferatu_nico_sombra")
    celia_moura = require("hecata_celia_moura")

    new_ghouls = [
        {
            "id": "ghoul_victor_pires",
            "kind": "ghoul",
            "display_name": "Victor Pires",
            "file_stem": "Victor_Pires",
            "apparent_age": 38,
            "appearance_explicit": "pessoa branca brasileira (pele clara), cicatriz discreta no queixo; olhar cansado de vigia",
            "signature_style": "terno simples, auricular de seguranca, fala curta",
            "ambition": "aposentar vivo e com nome limpo",
            "fear": "ser descartado como 'dano colateral' em uma crise de Mascara",
            "secret": "Ele guarda uma pasta com provas de suborno em contratos de seguranca, para o caso de precisar fugir.",
            "dangerous_truth": "Ele ja apagou camera e laudo para cobrir um ataque vampirico em local corporativo.",
            "false_rumor": "Dizem que ele e ex-ROTA. (Nao e; so deixa falarem.)",
            "scene_hooks": [
                "Um carro de apoio some com uma maleta; Victor pede ajuda sem envolver a policia.",
                "Victor reconhece um PJ de outra noite e cobra explicacao por 'estar no lugar errado'.",
                "Ele oferece uma saida segura de um predio, mas exige um nome em troca."
            ],
            "links": [
                {"to": artur, "type": "servant", "note": "motorista e seguranca discreto do Principe"},
                {"to": "banuhaqim_samira_al_haddad", "type": "uneasy", "note": "respeita o Xerife e teme auditoria"},
            ],
            "coteries": ["Corte do Elysium"],
            "touchstones": [],
            "tier": "support",
            "full_sheet": False,
            "disciplines_top3": [],
            "domain": "Paulista/Jardins",
            "sect": "Camarilla",
            "role": "Seguranca e motorista (Corte do Elysium)",
            "sire": None,
            "childer": [],
        },
        {
            "id": "ghoul_silvia_kajiki",
            "kind": "ghoul",
            "display_name": "Silvia Kajiki",
            "file_stem": "Silvia_Kajiki",
            "apparent_age": 29,
            "appearance_explicit": "pessoa japonesa-brasileira (pele clara), cabelo liso preto em chanel; batom vinho, delineado marcado",
            "signature_style": "elegancia minimalista; sorriso de recepcao que some quando ninguem ve",
            "ambition": "ser indispensavel para que ninguem aponte arma para ela",
            "fear": "ser gravada dizendo a frase errada (e virar prova)",
            "secret": "Ela mantem uma lista de 'convidados' que nunca deveriam ter entrado no Elysium.",
            "dangerous_truth": "Ela ja marcou encontros com mortais para servirem de refeicao 'sem rastro'.",
            "false_rumor": "Dizem que ela e a amante da Harpia. (Ela deixa a duvida proteger.)",
            "scene_hooks": [
                "Um PJ tenta entrar no Elysium sem convite; Silvia negocia a entrada por um favor claro e mensuravel.",
                "Uma briga estoura no banheiro; Silvia apaga os celulares e escolhe quem sai primeiro.",
                "Ela pede que os PJs escoltem uma influencer mortal que sabe demais."
            ],
            "links": [
                {"to": luiza, "type": "servant", "note": "recepcao, lista e controle social para a Senescal/Harpia"},
                {"to": "toreador_helena_vasconcelos", "type": "ally", "note": "trabalham juntas para manter o Elysium limpo"},
            ],
            "coteries": ["Corte do Elysium"],
            "touchstones": [],
            "tier": "support",
            "full_sheet": False,
            "disciplines_top3": [],
            "domain": "Pinheiros/Vila Madalena",
            "sect": "Camarilla",
            "role": "Recepcao e lista (Elysium de Pinheiros)",
            "sire": None,
            "childer": [],
        },
        {
            "id": "ghoul_douglas_ferraz",
            "kind": "ghoul",
            "display_name": "Douglas Ferraz",
            "file_stem": "Douglas_Ferraz",
            "apparent_age": 33,
            "appearance_explicit": "pessoa parda brasileira (pele marrom media), cabelo raspado; tatuagem antiga de oficina no antebraco",
            "signature_style": "moletom escuro, luvas de mecanico no bolso, cheiro de combustivel",
            "ambition": "virar 'dono de rota' sem precisar pedir permissao a ninguem",
            "fear": "ser pego por camera e virar moeda de chantagem contra a Baronesa",
            "secret": "Ele guarda um 'cemiterio' de veiculos em galpoes abandonados, com placas trocadas e compartimentos.",
            "dangerous_truth": "Ele ja entregou um humano para ser drenado em troca de protecao.",
            "false_rumor": "Dizem que ele e o childe secreto da Baronesa. (Nao e; so e util.)",
            "scene_hooks": [
                "Uma carga desaparece; Douglas aponta um suspeito e pede que os PJs provem antes de executar.",
                "Ele oferece um carro 'limpo' para fuga, mas exige um favor imediato.",
                "Douglas precisa de documentos falsos para um comboio e pressiona os PJs a conseguir."
            ],
            "links": [
                {"to": renata, "type": "servant", "note": "logistica, roubos e carros para o Baronato da Mooca"},
                {"to": "ghoul_beto_mecanico", "type": "ally", "note": "oficina e pecas; parceria tensa"},
            ],
            "coteries": ["Ferrugem"],
            "touchstones": [],
            "tier": "support",
            "full_sheet": False,
            "disciplines_top3": [],
            "domain": "Tatuape/Mooca",
            "sect": "Anarch",
            "role": "Logistica e carros (Baronato da Mooca)",
            "sire": None,
            "childer": [],
        },
        {
            "id": "ghoul_rafaela_novais",
            "kind": "ghoul",
            "display_name": "Rafaela Novais",
            "file_stem": "Rafaela_Novais",
            "apparent_age": 26,
            "appearance_explicit": "pessoa negra brasileira (pele escura), trancas curtas; unhas curtas sempre limpas, olhar focado",
            "signature_style": "mochila de socorro, tenis gasto, fala objetiva",
            "ambition": "criar uma rede de clinicas 'invisiveis' na quebrada",
            "fear": "ser forçada a escolher entre salvar alguem e obedecer ao Barao",
            "secret": "Ela mantem um caderno com nomes de policias e paramedicos comprados, para acionar quando precisa.",
            "dangerous_truth": "Ela ja tratou uma ferida de garras (nao faca), e sabe onde aconteceu.",
            "false_rumor": "Dizem que ela 'cura vampiro'. (Ela so costura e cala.)",
            "scene_hooks": [
                "Rafaela pede protecao para tirar um ferido de um hospital antes que a SI o veja.",
                "Ela precisa de sangue conservado para uma transfusao e faz um acordo direto com os PJs.",
                "Um 'animal grande' ronda a area onde ela atende; ela quer que os PJs confirmem o risco."
            ],
            "links": [
                {"to": diego, "type": "servant", "note": "atendimento, cobertura e rede de socorro do Barao do Leste"},
                {"to": "thin_blood_luan_patch", "type": "ally", "note": "troca de materiais e tecnicas; respeito mutuo"},
            ],
            "coteries": ["Matilha do Sul"],
            "touchstones": [],
            "tier": "support",
            "full_sheet": False,
            "disciplines_top3": [],
            "domain": "Baronato Leste (Itaquera/Extremo Leste)",
            "sect": "Anarch",
            "role": "Socorro e triagem (Itaquera)",
            "sire": None,
            "childer": [],
        },
        {
            "id": "ghoul_jonas_santos",
            "kind": "ghoul",
            "display_name": "Jonas Santos",
            "file_stem": "Jonas_Santos",
            "apparent_age": 41,
            "appearance_explicit": "pessoa branca brasileira (pele clara/oliva), bigode bem aparado; orelha com piercing pequeno",
            "signature_style": "jaqueta de motoboy sem logo, capacete sempre por perto, olhar que mede camera",
            "ambition": "virar o 'nome que resolve' sem aparecer em nenhum lugar",
            "fear": "ser filmado entregando coisa errada e virar ponto de correlacao",
            "secret": "Ele mantem uma rota de entrega que passa por pontos cegos conhecidos da cidade.",
            "dangerous_truth": "Ele ja carregou um corpo em mala de viagem, achando que era 'so encomenda'.",
            "false_rumor": "Dizem que ele trabalha para a policia. (Ele nao; mas vende a ideia.)",
            "scene_hooks": [
                "Jonas entrega um pacote aos PJs e avisa: 'nao abre aqui'. A SI ja esta perto.",
                "Ele pede para os PJs eliminarem uma camera especifica antes do proximo correio.",
                "Um rival tenta roubar a rota; Jonas quer que os PJs decidam o que fazer com o ladrao."
            ],
            "links": [
                {"to": nico, "type": "servant", "note": "correio de dados e pequenas coisas; roda pela Zona Cinza"},
                {"to": "nosferatu_ester_gato_preto", "type": "rival", "note": "disputa de rotas e de confianca"},
            ],
            "coteries": ["Corredores de Sombra"],
            "touchstones": [],
            "tier": "support",
            "full_sheet": False,
            "disciplines_top3": [],
            "domain": "Corredores (Zona Cinza de carga e sumico)",
            "sect": "Zona cinza",
            "role": "Correio (motoboy de rotas)",
            "sire": None,
            "childer": [],
        },
        {
            "id": "ghoul_maria_zelia_ramos",
            "kind": "ghoul",
            "display_name": "Maria Zelia Ramos",
            "file_stem": "Maria_Zelia_Ramos",
            "apparent_age": 52,
            "appearance_explicit": "pessoa parda brasileira (pele marrom clara), cabelo preso com presilha simples; rosto de quem ja viu de tudo",
            "signature_style": "blazer escuro, lencos discretos, voz baixa de secretaria",
            "ambition": "manter a funeraria funcionando sem que 'o mundo de fora' entre",
            "fear": "ser usada como isca por alguem que nao entende o preco dos mortos",
            "secret": "Ela tem chaves e registros de jazigos que nao constam em cartorio nenhum.",
            "dangerous_truth": "Ela ja moveu um corpo 'vivo demais' para longe de um IML.",
            "false_rumor": "Dizem que ela e parente do Primogeno Hecata. (Nao e, mas foi promovida por eficiencia.)",
            "scene_hooks": [
                "Ela pede que os PJs escoltem um caixao ate um jazigo sem placas (nao pode atrasar).",
                "Um parente mortal insiste em abrir o caixao; Maria quer que os PJs resolvam sem escandalo.",
                "Ela encontrou um simbolo estranho gravado em lapide recente e quer identificacao."
            ],
            "links": [
                {"to": celia_moura, "type": "servant", "note": "gestao de funeraria e acesso ao cemiterio"},
                {"to": "hecata_donato_lazzari", "type": "uneasy", "note": "teme o coletor de pedagio e seus 'custos'"},
            ],
            "coteries": ["Porteiros do Centro"],
            "touchstones": [],
            "tier": "support",
            "full_sheet": False,
            "disciplines_top3": [],
            "domain": "Cemiterios (Centro/Oeste)",
            "sect": "Autarquicos",
            "role": "Gestora de funeraria (enclave Hecata)",
            "sire": None,
            "childer": [],
        },
    ]

    added = 0
    for g in new_ghouls:
        added += 1 if _add_entity(entities, g) else 0

    if added:
        with open(SOURCE_JSON, "w", encoding="utf-8", newline="\n") as wf:
            json.dump(data, wf, ensure_ascii=False, indent=2)
            wf.write("\n")

    # Report
    kinds = {}
    for e in entities:
        kinds[e.get("kind")] = kinds.get(e.get("kind"), 0) + 1
    print(f"[expand_ghouls_pack3] added={added}")
    print("[expand_ghouls_pack3] kind counts:", kinds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
