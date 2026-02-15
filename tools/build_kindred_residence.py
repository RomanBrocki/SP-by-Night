import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "tools" / "sp_by_night_source.json"
OUT = ROOT / "tools" / "sp_kindred_residence.json"


def _norm(s: str) -> str:
    return (s or "").strip().lower()


def main() -> int:
    if not SRC.exists():
        raise SystemExit(f"missing {SRC}")
    data = json.loads(SRC.read_text(encoding="utf-8"))
    entities = [e for e in (data.get("entities") or []) if isinstance(e, dict)]
    kindred = [e for e in entities if e.get("kind") == "kindred"]

    # Manual overrides to keep the chronicle coherent and explicit.
    # Keys are Kindred ids from tools/sp_by_night_source.json.
    overrides: dict[str, dict] = {
        # Camarilla "lordes"
        "ventrue_artur_macedo": {"id": "paulista_jardins", "label": "Paulista/Jardins"},
        "ventrue_isabel_amaral": {"id": "itaim_berrini", "label": "Itaim/Berrini"},
        "toreador_luiza_salles": {"id": "pinheiros_vila_madalena", "label": "Pinheiros/Vila Madalena"},
        "toreador_helena_vasconcelos": {"id": "liberdade", "label": "Liberdade"},
        "tremere_dario_kron": {"id": "butanta_usp", "label": "Butanta/USP (Torre Tremere)"},
        "banuhaqim_samira_al_haddad": {"id": "santana_tucuruvi", "label": "Santana/Tucuruvi (Xerifado)"},
        "lasombra_padre_miguel_aranha": {"id": "bela_vista_bixiga", "label": "Bela Vista/Bixiga (Confissao)"},
        "nosferatu_nico_sombra": {"id": "bras_pari", "label": "Bras/Pari (Mercado de Sombras)"},
        # Anarch: baronatos (macro)
        "brujah_renata_ferraz": {"id": "baronato_mooca_tatuape", "label": "Baronato Mooca/Tatuape"},
        "brujah_caua_martins": {"id": "baronato_mooca_tatuape", "label": "Baronato Mooca/Tatuape"},
        "ministry_elias_sal": {"id": "baronato_mooca_tatuape", "label": "Baronato Mooca/Tatuape"},
        "malkavian_cecilia_linha_dois": {"id": "baronato_mooca_tatuape", "label": "Baronato Mooca/Tatuape"},
        "caitiff_rafa_ferro": {"id": "baronato_mooca_tatuape", "label": "Baronato Mooca/Tatuape"},
        "nosferatu_ester_gato_preto": {"id": "baronato_mooca_tatuape", "label": "Baronato Mooca/Tatuape"},
        "ravnos_maru_vento": {"id": "baronato_leste", "label": "Baronato Leste (Itaquera/Extremo Leste)"},
        "gangrel_bia_matilha": {"id": "baronato_sul", "label": "Baronato Sul (Capao/Grajau)"},
        "brujah_diego_itaquera": {"id": "baronato_leste", "label": "Baronato Leste (Itaquera/Extremo Leste)"},
        "brujah_novo_11_sabrina_siqueira": {"id": "baronato_sul", "label": "Baronato Sul (Capao/Grajau)"},
        "gangrel_novo_09_jonas_capim": {"id": "baronato_sul", "label": "Baronato Sul (Capao/Grajau)"},
        "ministry_novo_08_vivi_fenda_lacerda": {"id": "baronato_sul", "label": "Baronato Sul (Capao/Grajau)"},
        "thinblood_novo_10_bruna_sinais": {"id": "baronato_sul", "label": "Baronato Sul (Capao/Grajau)"},
        "thinblood_luan_patch": {"id": "baronato_sul", "label": "Baronato Sul (Capao/Grajau)"},
        "thinblood_katia_zero": {"id": "baronato_mooca_tatuape", "label": "Baronato Mooca/Tatuape"},
        "thinblood_ana_carbono": {"id": "baronato_leste", "label": "Baronato Leste (Itaquera/Extremo Leste)"},
        "lasombra_camila_noite_funda": {"id": "indep_corredores", "label": "Independentes: Corredores"},
        # Independentes (macro)
        # Donato controla Centro Velho e o enclave de cemiterios; na pratica ele dorme onde o acordo e mais sensivel.
        "hecata_donato_lazzari": {"id": "indep_cemiterios", "label": "Independentes: Cemiterios/Funerarias (enclave)"},
        "hecata_soraia_nunes": {"id": "indep_cemiterios", "label": "Independentes: Cemiterios/Funerarias (enclave)"},
        "hecata_iago_siqueira": {"id": "indep_centro_velho", "label": "Independentes: Centro Velho"},
        "malkavian_paulo_vidente": {"id": "indep_centro_velho", "label": "Independentes: Centro Velho"},
        "tzimisce_nina_costura": {"id": "indep_centro_velho", "label": "Independentes: Centro Velho"},
        "brujah_joao_do_trem": {"id": "indep_corredores", "label": "Independentes: Corredores"},
        "gangrel_hector_rodoanel": {"id": "indep_corredores", "label": "Independentes: Corredores"},
        "thinblood_dante_fumo": {"id": "indep_corredores", "label": "Independentes: Corredores"},
        "ravnos_ravi_truque": {"id": "indep_corredores", "label": "Independentes: Corredores"},
        "salubri_irene_da_luz": {"id": "indep_corredores", "label": "Independentes: Corredores"},
        "tzimisce_vlado_itapecerica": {"id": "baronato_sul", "label": "Baronato Sul (Capao/Grajau)"},
        "ministry_talita_serpente": {"id": "indep_corredores", "label": "Independentes: Corredores"},
        "banuhaqim_yusuf_rahman": {"id": "indep_corredores", "label": "Independentes: Corredores"},
        # Novo: preencher o enclave explicitamente no mapa.
        "hecata_celia_moura": {"id": "indep_cemiterios", "label": "Independentes: Cemiterios/Funerarias (enclave)"},
    }

    out = {
        "meta": {
            "note": "Fonte de verdade para 'onde este Cainita habita' em termos de camadas macro/domínios expressivos do mapa. Ajuste manualmente se quiser.",
        },
        "residence": {},
    }

    for e in kindred:
        eid = e.get("id") or ""
        if not eid:
            continue
        name = e.get("display_name") or ""
        sect = e.get("sect") or ""
        domain_raw = e.get("domain") or ""

        if eid in overrides:
            out["residence"][eid] = {
                "name": name,
                "sect": sect,
                "residence_id": overrides[eid]["id"],
                "residence_label": overrides[eid]["label"],
                "source": "override",
                "domain_raw": domain_raw,
            }
            continue

        # Default: if nothing explicit, assume the Kindred is "na Camarilla" mas sem territorio expressivo registrado.
        out["residence"][eid] = {
            "name": name,
            "sect": sect,
            "residence_id": "camarilla_macro" if _norm(sect) == "camarilla" else "desconhecido",
            "residence_label": "Camarilla (sem territorio expressivo)" if _norm(sect) == "camarilla" else "Nao definido",
            "source": "default",
            "domain_raw": domain_raw,
        }

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
