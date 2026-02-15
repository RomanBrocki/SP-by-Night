import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "tools" / "sp_by_night_source.json"


APPEARANCE_BY_DISPLAY_NAME = {
    "Artur Macedo": "pessoa branca brasileira (pele clara, tracos euro-brasileiros)",
    "Isabel do Amaral": "pessoa branca brasileira (pele clara, tracos euro-brasileiros)",
    "Mateus Cordeiro": "pessoa parda brasileira (pele marrom media, tracos miscigenados)",
    "Luiza Salles": "pessoa branca brasileira (pele clara)",
    "Helena Vasconcelos": "pessoa branca brasileira (pele clara)",
    "Daniel Sato": "pessoa asiatica brasileira (descendencia japonesa, pele clara a media, tracos japoneses evidentes)",
    "Samira al-Haddad": "pessoa arabe-brasileira (tracos do Oriente Medio, pele oliva)",
    "Yusuf Rahman": "pessoa sul-asiatica (descendencia indiana/paquistanesa, pele marrom media, tracos sul-asiaticos)",
    'Nico "Sombra"': "pessoa parda brasileira (pele marrom media, tracos miscigenados)",
    "Vovo Zilda": "pessoa negra brasileira (pele retinta, tracos negros evidentes)",
    'Ester "Gato-Preto"': "pessoa negra brasileira (pele escura, tracos negros evidentes)",
    "Renata Ferraz": "pessoa parda brasileira (pele marrom clara a media, tracos miscigenados)",
    "Joao do Trem": "pessoa negra brasileira (pele marrom escura a retinta, tracos negros evidentes)",
    "Caua Martins": "pessoa parda brasileira (pele marrom media, tracos miscigenados)",
    'Talita "Serpente"': "pessoa negra brasileira (pele marrom escura, tracos negros evidentes)",
    'Elias "Sal"': "pessoa parda brasileira (pele marrom clara, tracos miscigenados)",
    "Padre Miguel Aranha": "pessoa branca brasileira (pele clara)",
    "Dario Kron": "pessoa branca brasileira (descendencia germanica, pele clara)",
    "Bianca Saramago": "pessoa branca brasileira (pele clara)",
    "Donato Lazzari": "pessoa branca brasileira (descendencia italiana, pele clara)",
    "Soraia Nunes": "pessoa parda brasileira (pele marrom media, tracos miscigenados)",
    "Iago Siqueira": "pessoa parda brasileira (pele marrom media, tracos miscigenados)",
    'Camila "Noite-Funda"': "pessoa negra brasileira (pele retinta, tracos negros evidentes)",
    'Paulo "O Vidente"': "pessoa parda brasileira (pele marrom media, tracos miscigenados)",
    'Cecilia "Linha-Dois"': "pessoa branca brasileira (pele clara)",
    'Bia "Matilha"': "pessoa parda brasileira (pele marrom media, tracos miscigenados)",
    'Hector "Rodoanel"': "pessoa parda brasileira (pele marrom media, tracos miscigenados)",
    'Rafa "Ferro"': "pessoa negra brasileira (pele escura, tracos negros evidentes)",
    'Livia "Sem-Nome"': "pessoa branca brasileira (pele clara)",
    'Ana "Carbono"': "pessoa negra brasileira (pele retinta, tracos negros evidentes)",
    'Dante "Fumo"': "pessoa parda brasileira (pele marrom media, tracos miscigenados)",
    'Katia "Zero"': "pessoa branca brasileira (pele clara)",
    'Luan "Patch"': "pessoa parda brasileira (pele marrom media, tracos miscigenados)",
    'Ravi "Truque"': "pessoa sul-asiatica (descendencia indiana, pele marrom media, tracos sul-asiaticos)",
    'Maru "Vento"': "pessoa asiatica brasileira (descendencia japonesa, pele clara a media, tracos japoneses evidentes)",
    "Irene da Luz": "pessoa negra brasileira (pele marrom escura, tracos negros evidentes)",
    'Nina "Costura"': "pessoa branca brasileira (pele clara)",
    "Vlado de Itapecerica": "pessoa branca (tracos do leste europeu, pele clara)",
    "Mariana Lobo": "pessoa parda brasileira (pele marrom clara a media, tracos miscigenados)",
    "Carla Nogueira": "pessoa branca brasileira (pele clara)",
    "Vitor Kallas": "pessoa branca brasileira (descendencia grega/balca, pele clara)",
    'Rui "Barata"': "pessoa parda brasileira (pele marrom media, tracos miscigenados)",
    "Lia Morais": "pessoa negra brasileira (pele escura, tracos negros evidentes)",
    'Tiago "Tranca"': "pessoa negra brasileira (pele marrom escura, tracos negros evidentes)",
    'Beto "Mecanico"': "pessoa parda brasileira (pele marrom media, tracos miscigenados)",
    "Delegada Helena Pacheco": "pessoa parda brasileira (pele marrom clara a media, tracos miscigenados)",
    "Padre Augusto Faria": "pessoa branca brasileira (pele clara)",
    "Dra. Aline Moretti": "pessoa branca brasileira (descendencia italiana, pele clara)",
    'Jonas "Coro"': "pessoa negra brasileira (pele retinta, tracos negros evidentes)",
    'Leonardo "Aprendiz"': "pessoa branca brasileira (pele clara)",
    "Vivi Lacerda": "pessoa parda brasileira (pele marrom clara a media, tracos miscigenados)",
}


def main() -> None:
    d = json.loads(SRC.read_text(encoding="utf-8"))
    missing = []
    for e in d.get("entities", []):
        dn = e.get("display_name")
        if dn not in APPEARANCE_BY_DISPLAY_NAME:
            missing.append(dn)
            continue
        e["appearance_explicit"] = APPEARANCE_BY_DISPLAY_NAME[dn]

    if missing:
        raise SystemExit("Missing appearance mapping for: " + ", ".join(sorted(missing)))

    SRC.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("OK: wrote appearance_explicit for", len(d.get("entities", [])), "entities")


if __name__ == "__main__":
    main()

