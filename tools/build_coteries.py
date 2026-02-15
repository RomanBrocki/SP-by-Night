from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "tools" / "sp_by_night_source.json"
OUT_MD = ROOT / "01_BACKGROUND_NARRADOR" / "coteries_e_associacoes.md"


def die(msg: str) -> None:
    raise SystemExit(msg)


def main() -> int:
    if not SRC.exists():
        die(f"missing {SRC}")

    data = json.loads(SRC.read_text(encoding="utf-8"))
    entities = [e for e in (data.get("entities") or []) if isinstance(e, dict)]
    by_id = {e.get("id"): e for e in entities if e.get("id")}

    def must(ids: list[str]) -> list[str]:
        bad = [i for i in ids if i not in by_id]
        if bad:
            die("unknown entity ids in coteries: " + ", ".join(bad))
        return ids

    # "Coterie" aqui = grupo pequeno que opera junto.
    # "Associacao" = rede maior, com etiqueta e pedágio.
    coteries = [
        {
            "id": "assoc_corte_do_elysium",
            "name": "Corte do Elysium (Camarilla)",
            "type": "associacao",
            "faction": "Camarilla",
            "base": "Paulista/Jardins + salas de protocolo (Elysium e satelites)",
            "notes": (
                "Nao e uma coterie, e a maquina politica da Camarilla. "
                "Aqui favor vira norma, e norma vira sentenca. Quem entra aprende etiqueta ou vira exemplo."
            ),
            "members": must(
                [
                    "ventrue_artur_macedo",
                    "toreador_luiza_salles",
                    "banuhaqim_samira_al_haddad",
                    "ventrue_mateus_cordeiro",
                    "ventrue_henrique_valadares",
                    "tremere_dario_kron",
                    "nosferatu_nico_sombra",
                    "malkavian_marcia_falcao",
                    "toreador_clara_montenegro",
                    "banuhaqim_nadia_nasser",
                    "nosferatu_raimundo_rato_rei",
                    "lasombra_padre_miguel_aranha",
                    "ghoul_mariana_lobo",
                    "ghoul_ricardo_protocolos",
                    "ghoul_igor_motorista",
                    "ghoul_paula_compliance",
                    "ghoul_lara_contencao",
                    "ghoul_vitor_kallas",
                    "ghoul_carla_nogueira",
                    "ghoul_yuri_curador",
                ]
            ),
        },
        {
            "id": "coterie_ferrugem_mooca",
            "name": "Coterie Ferrugem (Mooca/Tatuape)",
            "type": "coterie",
            "faction": "Anarch",
            "base": "Mooca/Tatuape (bares, oficinas, ruas e estacoes)",
            "notes": (
                "O coracao politico do baronato da Renata: gente que resolve na rua e cobra em lealdade. "
                "Eles chamam de 'protecao comunitaria'; a Camarilla chama de extorsao com narrativa."
            ),
            "members": must(
                [
                    "brujah_renata_ferraz",
                    "brujah_caua_martins",
                    "ministry_elias_sal",
                    "caitiff_rafa_ferro",
                    "nosferatu_ester_gato_preto",
                    "malkavian_cecilia_linha_dois",
                    "thinblood_katia_zero",
                    "ghoul_tiago_tranca",
                    "ghoul_rodrigo_fiel",
                    "ghoul_maya_hacker",
                ]
            ),
        },
        {
            "id": "coterie_matilha_do_sul",
            "name": "Matilha do Sul (Capao/Grajau)",
            "type": "coterie",
            "faction": "Anarch",
            "base": "Capao Redondo / Grajau (bordas, quebradas e rotas verdes)",
            "notes": (
                "A unidade que faz o baronato Sul existir na pratica: escolta, aviso, resgate e represalia. "
                "Quando a cidade 'acaba', eles ainda estao andando."
            ),
            "members": must(
                [
                    "gangrel_bia_matilha",
                    "thinblood_luan_patch",
                    "tzimisce_vlado_itapecerica",
                    "brujah_novo_11_sabrina_siqueira",
                    "gangrel_novo_09_jonas_capim",
                    "ministry_novo_08_vivi_fenda_lacerda",
                    "thinblood_novo_10_bruna_sinais",
                    "ghoul_marcelo_moto",
                    "ghoul_jessica_biqueira",
                    "ghoul_wesley_corredor",
                ]
            ),
        },
        {
            "id": "coterie_leste_de_aco",
            "name": "Leste de Aco (Itaquera/Extremo Leste)",
            "type": "coterie",
            "faction": "Anarch",
            "base": "Itaquera e rotas do Extremo Leste",
            "notes": (
                "Rede de rota e abrigo do Baronato Leste. Funciona como guarda territorial e como correio: "
                "quem atravessa o Leste sem avisar vira assunto."
            ),
            "members": must(
                [
                    "brujah_diego_itaquera",
                    "ravnos_maru_vento",
                    "thinblood_ana_carbono",
                    "ghoul_lia_comunidade",
                    "ghoul_paula_olheira",
                ]
            ),
        },
        {
            "id": "assoc_corredores_de_sombra",
            "name": "Corredores de Sombra (conselho de corretores)",
            "type": "associacao",
            "faction": "Independentes",
            "base": "Barra Funda/Lapa e eixos de carga (zona cinza)",
            "notes": (
                "Nao e uma coterie, e um mercado: corretores, 'fixers' e gente de rota. "
                "Territorio aqui nao e bairro, e janela: hora, camera, cracha e nota fiscal. "
                "Eles vendem passagem, sumico e atraso planejado."
            ),
            "members": must(
                [
                    "banuhaqim_yusuf_rahman",
                    "brujah_joao_do_trem",
                    "gangrel_hector_rodoanel",
                    "ministry_talita_serpente",
                    "ravnos_ravi_truque",
                    "thinblood_dante_fumo",
                    "lasombra_camila_noite_funda",
                    "ghoul_beto_mecanico",
                    "ghoul_eli_customs",
                    "ghoul_teresa_balanca",
                ]
            ),
        },
        {
            "id": "assoc_enclave_cemiterios",
            "name": "Enclave dos Cemiterios (Hecata)",
            "type": "associacao",
            "faction": "Independentes",
            "base": "Consolacao (cemiterio, funerarias e capelas de servico)",
            "notes": (
                "Um acordo escrito sem papel: a Camarilla tolera porque precisa. "
                "Aqui o pedagio e memoria, nome e segredo. Quebrar o acordo vira exemplo."
            ),
            "members": must(
                [
                    "hecata_donato_lazzari",
                    "hecata_soraia_nunes",
                    "hecata_celia_moura",
                    "hecata_iago_siqueira",
                    "ghoul_lia_morais",
                    "ghoul_silvia_funebre",
                ]
            ),
        },
        {
            "id": "assoc_correios_do_subsolo",
            "name": "Correios do Subsolo (rede Nosferatu)",
            "type": "associacao",
            "faction": "Camarilla",
            "base": "Esgotos, galerias e salas tecnicas (Bras/Pari, Perdizes, Centro)",
            "notes": (
                "Rede de mensagens e rotas: bilhetes, pendrives, pessoas. "
                "O pagamento raramente e dinheiro; e silencio, acesso e uma porta aberta na hora certa."
            ),
            "members": must(
                [
                    "nosferatu_raimundo_rato_rei",
                    "nosferatu_nico_sombra",
                    "nosferatu_vovo_zilda",
                    "nosferatu_ester_gato_preto",
                    "nosferatu_novo_19_nara_sato_3",
                    "nosferatu_novo_25_nara_sato_9",
                    "ghoul_pedro_manutencao",
                ]
            ),
        },
        {
            "id": "assoc_confissao_preta",
            "name": "A Confissao Preta (Lasombra)",
            "type": "associacao",
            "faction": "Camarilla",
            "base": "Bela Vista/Bixiga (salas privadas, igrejas e advocacia)",
            "notes": (
                "Eles chamam de confissao. A cidade chama de chantagem com liturgia. "
                "Serve a Camarilla porque transforma pecado em protocolo e inimigo em penitente."
            ),
            "members": must(
                [
                    "lasombra_padre_miguel_aranha",
                    "lasombra_novo_04_irma_beatriz_lemos",
                    "lasombra_novo_27_severino_carmo_11",
                    "ghoul_jonas_coro",
                ]
            ),
        },
        {
            "id": "assoc_salao_pinheiros",
            "name": "Salao de Pinheiros (Toreador)",
            "type": "associacao",
            "faction": "Camarilla",
            "base": "Pinheiros/Vila Madalena + Elysium satelite (Liberdade)",
            "notes": (
                "Patronato, fofoca e convite. Quem entra tem vitrine; quem cai vira piada eterna. "
                "E onde a politica vira 'evento'."
            ),
            "members": must(
                [
                    "toreador_luiza_salles",
                    "toreador_clara_montenegro",
                    "toreador_helena_vasconcelos",
                    "toreador_daniel_sato",
                ]
            ),
        },
        {
            "id": "assoc_torre_usp",
            "name": "Torre da USP (Tremere)",
            "type": "associacao",
            "faction": "Camarilla",
            "base": "Butanta/USP (laboratorios, bibliotecas e salas trancadas)",
            "notes": (
                "Nao e piramide como antes, mas ainda e torre: arquivos, selos e contramedidas. "
                "A Camarilla tolera porque precisa de gente que apague rastros 'impossiveis'."
            ),
            "members": must(["tremere_dario_kron", "tremere_bianca_saramago", "tremere_novo_03_maira_koehler"]),
        },
        {
            "id": "assoc_chaves_do_morumbi",
            "name": "Chaves do Morumbi (Ventrue)",
            "type": "associacao",
            "faction": "Camarilla",
            "base": "Morumbi/Campo Belo (condominios e seguranca privada)",
            "notes": (
                "Controle por acesso. Aqui a Mascarada nao e misterio, e catraca: quem entra, quem sai, "
                "quem vira 'visitante'."
            ),
            "members": must(["ventrue_henrique_valadares", "ventrue_novo_17_helio_barros_1", "ventrue_novo_23_helio_barros_7", "ghoul_damiao_portaria"]),
        },
        {
            "id": "assoc_sangue_e_selo",
            "name": "Sangue e Selo (Banu Haqim)",
            "type": "associacao",
            "faction": "Camarilla",
            "base": "Ipiranga/Cursino + Santana (juridico e execucao)",
            "notes": (
                "Um tribunal ambulante: investigar, julgar, executar. "
                "Nao com teatro; com dossie, precedente e exemplo."
            ),
            "members": must(["banuhaqim_samira_al_haddad", "banuhaqim_nadia_nasser", "banuhaqim_novo_13_farid_alvim", "ghoul_samir_escrivao"]),
        },
        {
            "id": "assoc_ouvidores",
            "name": "Os Ouvidores (Malkavian)",
            "type": "associacao",
            "faction": "Camarilla",
            "base": "Consolacao/Republica (clinicas, midia, metro)",
            "notes": (
                "Nao e uma seita secreta: e uma forma de sobreviver. Eles trocam padroes, alertas e lapsos. "
                "O custo e sempre um nome, uma lembranca ou uma verdade que voce nao queria dizer."
            ),
            "members": must(["malkavian_marcia_falcao", "malkavian_novo_06_miriam_kwon", "malkavian_paulo_vidente", "malkavian_cecilia_linha_dois"]),
        },
    ]

    # Apply membership to entities.
    membership: dict[str, set[str]] = {}
    for c in coteries:
        cid = c["id"]
        for mid in c.get("members") or []:
            membership.setdefault(mid, set()).add(cid)

    for e in entities:
        eid = e.get("id") or ""
        if not eid:
            continue
        cur = e.get("coteries")
        if cur is None:
            cur_list: list[str] = []
        elif isinstance(cur, list):
            cur_list = [str(x) for x in cur if x]
        else:
            cur_list = [str(cur)]
        merged = set(cur_list) | membership.get(eid, set())
        e["coteries"] = sorted(merged)

    # Persist to source (coteries definitions + memberships).
    data["coteries"] = coteries
    data["entities"] = entities
    SRC.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Write a narrator-facing markdown.
    lines: list[str] = []
    lines.append("# Coteries e Associacoes (Sao Paulo by Night)")
    lines.append("")
    lines.append("Este arquivo define grupos recorrentes citados nos NPCs e no mapa.")
    lines.append("Regra de ouro: **coterie** = equipe pequena que age junta; **associacao** = rede/mercado com pedagio.")
    lines.append("")

    for c in coteries:
        lines.append(f"## {c['name']}")
        lines.append(f"- Tipo: {c['type']}")
        lines.append(f"- Faccao: {c['faction']}")
        lines.append(f"- Base: {c['base']}")
        lines.append("")
        lines.append("Descricao:")
        lines.append(str(c.get("notes") or "-"))
        lines.append("")
        lines.append("Membros (atuais, nomeados no projeto):")
        for mid in c.get("members") or []:
            m = by_id.get(mid) or {}
            nm = m.get("display_name") or mid
            clan = m.get("clan") or "-"
            sect = m.get("sect") or "-"
            role = m.get("role") or "-"
            lines.append(f"- {nm} ({clan}; {sect}) - {role}")
        lines.append("")
        lines.append("Como isso entra em mesa (ganchos claros):")
        if c["id"] == "assoc_corredores_de_sombra":
            lines.append("- Pedido de passagem: um PJ precisa cruzar com um corpo/objeto sem camera. O 'conselho' cobra horario, placa e um favor.")
            lines.append("- Sumiço vendido: um mortal some por 12h; a devolucao custa uma entrega no dia seguinte.")
        elif c["id"] == "assoc_correios_do_subsolo":
            lines.append("- Um bilhete chega sem remetente. Se for aberto fora do lugar certo, vira prova contra os PJ.")
            lines.append("- A rota mais segura exige que os PJ levem algo junto (uma encomenda).")
        elif c["id"] == "assoc_enclave_cemiterios":
            lines.append("- Um corpo aparece com marca errada; o enclave exige que os PJ corrijam antes do amanhecer.")
            lines.append("- Um acordo quebrado: alguem caçou em capela proibida. O enclave quer exemplo.")
        else:
            lines.append("- Um favor pequeno vira cadeia: convite, acesso, informacao ou abrigo com custo social.")
        lines.append("")

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"wrote {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
