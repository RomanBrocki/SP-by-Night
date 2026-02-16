from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
PORTRAITS = ROOT / "05_ASSETS" / "portraits"

MAX_BYTES = 500 * 1024  # 500 KB
BG = (12, 12, 16)  # dark background to replace transparency, matches site vibe


@dataclass
class Result:
    stem: str
    old_png: int
    new_jpg: int
    quality: int
    exceeded: bool


def to_rgb(im: Image.Image) -> Image.Image:
    # Preserve pixels as much as possible while removing alpha (JPEG has no alpha).
    if im.mode in ("RGBA", "LA") or ("transparency" in im.info):
        base = Image.new("RGB", im.size, BG)
        base.paste(im.convert("RGBA"), mask=im.convert("RGBA").split()[-1])
        return base
    if im.mode != "RGB":
        return im.convert("RGB")
    return im


def save_try(im: Image.Image, out_path: Path, quality: int) -> int:
    im.save(
        out_path,
        format="JPEG",
        quality=int(quality),
        optimize=True,
        progressive=True,
        subsampling=2,  # 4:2:0
    )
    return out_path.stat().st_size


def convert_one(png: Path) -> Result | None:
    stem = png.stem
    jpg = png.with_suffix(".jpg")
    old = png.stat().st_size

    with Image.open(png) as im0:
        im = to_rgb(im0)

        # Write into the same folder so replace/remove is atomic-ish on Windows.
        tmp = png.with_name(stem + ".tmp.jpg")
        if tmp.exists():
            tmp.unlink()

        best_size = None
        best_q = None

        for q in list(range(85, 19, -5)) + [15]:
            size = save_try(im, tmp, q)
            if best_size is None or size < best_size:
                best_size, best_q = size, q
            if size <= MAX_BYTES:
                best_size, best_q = size, q
                break

        assert best_size is not None and best_q is not None

        # Move into final name, then delete PNG to actually reduce repo size.
        os.replace(str(tmp), str(jpg))
        png.unlink()

        return Result(stem=stem, old_png=old, new_jpg=best_size, quality=best_q, exceeded=(best_size > MAX_BYTES))


def main() -> int:
    if not PORTRAITS.exists():
        print(f"[jpg] missing {PORTRAITS}")
        return 1

    pngs = sorted(PORTRAITS.glob("*.png"))
    if not pngs:
        print("[jpg] no .png portraits found (nothing to do).")
        return 0

    results: list[Result] = []
    failed: list[str] = []

    for png in pngs:
        try:
            r = convert_one(png)
            if r:
                results.append(r)
        except Exception as e:
            failed.append(f"{png.name}: {e}")

    old_total = sum(r.old_png for r in results)
    new_total = sum(r.new_jpg for r in results)
    saved = old_total - new_total
    pct = (saved / old_total * 100.0) if old_total else 0.0

    exceeded = [r for r in results if r.exceeded]

    print(f"[jpg] converted={len(results)} failed={len(failed)}")
    print(f"[jpg] old_png_total={old_total} new_jpg_total={new_total} saved={saved} ({pct:.1f}%)")
    print(f"[jpg] max_target={MAX_BYTES} bytes; exceeded={len(exceeded)}")
    if exceeded:
        # show worst offenders
        worst = sorted(exceeded, key=lambda r: r.new_jpg, reverse=True)[:10]
        for r in worst:
            print(f"[jpg] exceeded: {r.stem}.jpg size={r.new_jpg} q={r.quality}")
    if failed:
        print("[jpg] failures (first 10):")
        for x in failed[:10]:
            print("[jpg]  " + x)

    return 0 if not failed else 2


if __name__ == "__main__":
    raise SystemExit(main())

