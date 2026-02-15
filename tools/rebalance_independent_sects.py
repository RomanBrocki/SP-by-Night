import json
import os


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SOURCE_JSON = os.path.join(ROOT, "tools", "sp_by_night_source.json")


def main() -> int:
    with open(SOURCE_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    entities = data.get("entities") or []
    by_id = {e.get("id"): e for e in entities if isinstance(e, dict) and e.get("id")}

    def has_coterie(e: dict, cid: str) -> bool:
        return cid in (e.get("coteries") or [])

    changed = 0

    # Heuristic: "Independentes" = zona cinza / corredores / correios e rotas.
    # "Autarquicos" = Centro Velho, cemiterios, pedagio/arquivo/poroes.
    for e in entities:
        if not isinstance(e, dict):
            continue
        if e.get("kind") != "kindred":
            continue

        sect = (e.get("sect") or "").strip()
        if sect != "Autarquicos":
            continue

        role = (e.get("role") or "").lower()
        dom = (e.get("domain") or "").lower()

        # Move these profiles to Independentes.
        independent_signals = [
            "corredores",
            "rodoanel",
            "rotas",
            "entreg",
            "correio",
            "sumico",
            "itiner",
            "carga",
            "doca",
            "despach",
        ]
        autarkis_signals = [
            "centro velho",
            "cemiter",
            "funerar",
            "pedagio",
            "arquivo",
            "cartor",
            "galerias",
            "capela",
        ]

        indep = False
        if has_coterie(e, "assoc_corredores_de_sombra"):
            indep = True
        if any(s in role for s in independent_signals) or any(s in dom for s in independent_signals):
            indep = True
        if any(s in role for s in autarkis_signals) or any(s in dom for s in autarkis_signals):
            # Centro Velho/cemiterios stay Autarquicos even if they also run routes.
            indep = False

        if indep:
            e["sect"] = "Independentes"
            changed += 1

    # After moving masters, ensure ghouls inherit their master's sect (keeps dossiers coherent).
    for e in entities:
        if not isinstance(e, dict):
            continue
        if e.get("kind") != "ghoul":
            continue
        master_id = None
        for l in e.get("links") or []:
            if l.get("type") == "servant" and l.get("to"):
                master_id = l["to"]
                break
        if master_id and master_id in by_id:
            msect = (by_id[master_id].get("sect") or "").strip()
            if msect and e.get("sect") != msect:
                e["sect"] = msect
                changed += 1

    if changed:
        with open(SOURCE_JSON, "w", encoding="utf-8", newline="\n") as wf:
            json.dump(data, wf, ensure_ascii=False, indent=2)
            wf.write("\n")

    print(f"[rebalance_independent_sects] changed={changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

