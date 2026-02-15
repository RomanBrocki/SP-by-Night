from __future__ import annotations

import base64
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "tools" / "sp_by_night_source.json"


# 1x1 transparent PNG fallback (if Pillow isn't available).
_PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z/C/HwAF/gL+o0qS7QAAAABJRU5ErkJggg=="
)


def clan_folder(clan: str) -> str:
    return (clan or "Desconhecido").replace(" ", "_").replace("-", "_").replace("/", "_")


def initials(name: str) -> str:
    parts = [p for p in (name or "").replace('"', "").split() if p and p[0].isalnum()]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def try_pillow():
    try:
        from PIL import Image, ImageDraw, ImageFont  # type: ignore

        return Image, ImageDraw, ImageFont
    except Exception:
        return None


def make_png(path: Path, name: str, clan: str) -> None:
    pil = try_pillow()
    if pil is None:
        path.write_bytes(_PNG_1X1)
        return

    Image, ImageDraw, ImageFont = pil
    W = H = 512
    bg = (15, 15, 15)
    ring = (220, 220, 220)
    img = Image.new("RGB", (W, H), bg)
    draw = ImageDraw.Draw(img)

    # Border ring
    draw.ellipse((24, 24, W - 24, H - 24), outline=ring, width=10)

    ini = initials(name)
    try:
        font = ImageFont.truetype("arial.ttf", 150)
        font2 = ImageFont.truetype("arial.ttf", 34)
    except Exception:
        font = ImageFont.load_default()
        font2 = ImageFont.load_default()

    # Center initials
    tw, th = draw.textbbox((0, 0), ini, font=font)[2:]
    draw.text(((W - tw) / 2, (H - th) / 2 - 20), ini, fill=(245, 245, 245), font=font)

    clan_txt = (clan or "").strip() or "Kindred"
    ct = clan_txt[:24]
    tw2, th2 = draw.textbbox((0, 0), ct, font=font2)[2:]
    draw.text(((W - tw2) / 2, H - 110), ct, fill=(190, 190, 190), font=font2)

    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, "PNG")


def main() -> int:
    data = json.loads(SRC.read_text(encoding="utf-8"))
    entities = [e for e in (data.get("entities") or []) if isinstance(e, dict)]
    kindred = [e for e in entities if e.get("kind") == "kindred"]
    ghouls = [e for e in entities if e.get("kind") == "ghoul"]
    mortals = [e for e in entities if e.get("kind") == "mortal"]

    made = 0
    skipped = 0

    def ensure_list(lst: list[dict], folder: Path, clan_label: str) -> None:
        nonlocal made, skipped
        for e in lst:
            stem = e.get("file_stem") or ""
            if not stem:
                continue
            out = folder / f"{stem}.png"
            if out.exists() and out.stat().st_size > 64:
                skipped += 1
                continue
            make_png(out, e.get("display_name") or "", clan_label)
            made += 1

    # Kindred portraits live with NPC files.
    for e in kindred:
        clan = e.get("clan") or "Desconhecido"
        folder = ROOT / "02_NPCS" / clan_folder(clan)
        ensure_list([e], folder, clan)

    # Servants/contacts portraits live with their files.
    ensure_list(ghouls, ROOT / "03_SERVOS_E_CONTATOS" / "ghouls", "Ghoul")
    ensure_list(mortals, ROOT / "03_SERVOS_E_CONTATOS" / "mortais_influentes", "Mortal")

    print(f"placeholders: made={made} skipped={skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
