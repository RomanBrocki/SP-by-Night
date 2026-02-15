from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "tools" / "sp_by_night_source.json"


def stem(s: str) -> str:
    s = (s or "").strip()
    s = s.replace('"', "").replace("'", "")
    s = re.sub(r"[^A-Za-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "NPC"


RENAMES = {
    # Remove numeric suffixes in display_name (more natural NPC list).
    "ventrue_novo_17_helio_barros_1": "Helio Barros",
    "toreador_novo_18_sofia_pires_2": "Sofia Pires",
    "nosferatu_novo_19_nara_sato_3": "Nara Sato",
    "tremere_novo_20_igor_menezes_4": "Igor Menezes",
    "lasombra_novo_21_severino_carmo_5": "Severino Carmo",
    "malkavian_novo_22_celia_andrade_6": "Celia Andrade",
    "ventrue_novo_23_helio_barros_7": "Otavio Braga",
    "toreador_novo_24_sofia_pires_8": "Beatriz Pires",
    "nosferatu_novo_25_nara_sato_9": "Keiko Sato",
    "tremere_novo_26_igor_menezes_10": "Rafael Menezes",
    "lasombra_novo_27_severino_carmo_11": "Afonso Carmo",
    "malkavian_novo_28_celia_andrade_12": "Regina Andrade",
    "ventrue_novo_29_helio_barros_13": "Renato Vianna",
    "toreador_novo_30_sofia_pires_14": "Larissa Prado",
    "nosferatu_novo_31_nara_sato_15": "Hiroko Sato",
    "tremere_novo_32_igor_menezes_16": "Caio Menezes",
    "lasombra_novo_33_severino_carmo_17": "Bento Carmo",
    "malkavian_novo_34_celia_andrade_18": "Patricia Andrade",
    "ventrue_novo_35_helio_barros_19": "Augusto Brito",
}


def main() -> int:
    data = json.loads(SRC.read_text(encoding="utf-8"))
    entities = [e for e in (data.get("entities") or []) if isinstance(e, dict)]
    by_id = {e.get("id"): e for e in entities if e.get("id")}

    for eid, new_name in RENAMES.items():
        e = by_id.get(eid)
        if not e:
            raise SystemExit(f"missing entity id: {eid}")
        e["display_name"] = new_name
        e["file_stem"] = stem(new_name)

    data["entities"] = entities
    SRC.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {SRC}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

