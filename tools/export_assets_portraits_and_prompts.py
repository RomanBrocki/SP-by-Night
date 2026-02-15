import json
import os
import shutil


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SOURCE_JSON = os.path.join(ROOT, "tools", "sp_by_night_source.json")
FROZEN_STEMS_PATH = os.path.join(ROOT, "tools", "frozen_portrait_stems.txt")

ASSETS_PORTRAITS_DIR = os.path.join(ROOT, "05_ASSETS", "portraits")
ASSETS_PROMPTS_DIR = os.path.join(ROOT, "05_ASSETS", "portrait_prompts")
# Alias requested by user: sometimes they refer to "portraits_prompts".
ASSETS_PROMPTS_ALIAS_DIR = os.path.join(ROOT, "05_ASSETS", "portraits_prompts")


def _ensure_dir(p: str) -> None:
    os.makedirs(p, exist_ok=True)


def _load_frozen_stems() -> set[str]:
    if not os.path.exists(FROZEN_STEMS_PATH):
        return set()
    out: set[str] = set()
    with open(FROZEN_STEMS_PATH, "r", encoding="utf-8") as f:
        for line in f.read().splitlines():
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            out.add(s)
    return out


def _canonical_portrait_path(entity: dict) -> str:
    stem = entity["file_stem"]
    kind = entity.get("kind")

    if kind == "kindred":
        clan = entity.get("clan") or "Sem_Cla"
        # Project convention: clan folders use underscores (e.g. "Banu_Haqim", "Thin_Blood").
        clan_dir = clan.replace(" ", "_")
        return os.path.join(ROOT, "02_NPCS", clan_dir, f"{stem}.png")
    if kind == "ghoul":
        return os.path.join(ROOT, "03_SERVOS_E_CONTATOS", "ghouls", f"{stem}.png")
    if kind == "mortal":
        return os.path.join(
            ROOT, "03_SERVOS_E_CONTATOS", "mortais_influentes", f"{stem}.png"
        )
    # Fallback (shouldn't happen): keep in assets only.
    return os.path.join(ASSETS_PORTRAITS_DIR, f"{stem}.png")


def main() -> int:
    _ensure_dir(ASSETS_PORTRAITS_DIR)
    _ensure_dir(ASSETS_PROMPTS_DIR)
    _ensure_dir(ASSETS_PROMPTS_ALIAS_DIR)

    frozen = _load_frozen_stems()
    prompts_only = os.environ.get("PROMPTS_ONLY", "").strip() in ("1", "true", "TRUE", "yes", "YES")

    with open(SOURCE_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    entities = data.get("entities") or []

    copied_png = 0
    wrote_txt = 0
    missing_png_sources = []

    for e in entities:
        stem = e["file_stem"]

        # Portrait PNG
        if not prompts_only:
            src_png = _canonical_portrait_path(e)
            dst_png = os.path.join(ASSETS_PORTRAITS_DIR, f"{stem}.png")
            if os.path.exists(src_png):
                # Overwrite to keep assets in sync with canonical sources.
                shutil.copyfile(src_png, dst_png)
                copied_png += 1
            else:
                missing_png_sources.append(src_png)

        # Prompt TXT (always write, source is the JSON)
        if stem in frozen:
            continue
        prompt = (e.get("portrait_prompt") or "").strip()
        if not prompt:
            # Should not happen; keep file for tooling consistency.
            prompt = f"[PROMPT AUSENTE] {e.get('display_name','(sem nome)')}"

        for out_dir in (ASSETS_PROMPTS_DIR, ASSETS_PROMPTS_ALIAS_DIR):
            out_txt = os.path.join(out_dir, f"{stem}.txt")
            with open(out_txt, "w", encoding="utf-8", newline="\n") as wf:
                wf.write(prompt)
                wf.write("\n")
        wrote_txt += 1

    print(f"[assets] entities={len(entities)}")
    if prompts_only:
        print(f"[assets] portraits copied=0 (PROMPTS_ONLY=1) -> {ASSETS_PORTRAITS_DIR}")
    else:
        print(f"[assets] portraits copied={copied_png} -> {ASSETS_PORTRAITS_DIR}")
    print(f"[assets] prompts written={wrote_txt} -> {ASSETS_PROMPTS_DIR} (+ alias)")
    if missing_png_sources:
        print(f"[assets] missing portrait sources={len(missing_png_sources)} (run ensure_portrait_placeholders)")
        for p in missing_png_sources[:20]:
            print(" -", os.path.relpath(p, ROOT))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
