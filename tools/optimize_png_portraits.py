from __future__ import annotations

import os
import tempfile
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
PORTRAITS = ROOT / "05_ASSETS" / "portraits"


def optimize_png_in_place(path: Path) -> tuple[int, int, tuple[int, int]]:
    """
    Lossless-ish re-encode: keep PNG, keep width/height, drop ancillary chunks, maximize deflate.
    Returns (old_bytes, new_bytes, (w,h)). If not improved, returns old==new and leaves file intact.
    """
    old = path.stat().st_size
    with Image.open(path) as im:
        w, h = im.size

        # Normalize load; keep original pixel data. Avoid conversions that change pixels.
        im.load()

        # Write temp file on the same drive so os.replace works on Windows.
        fd, tmp_name = tempfile.mkstemp(suffix=".png", dir=str(path.parent))
        os.close(fd)
        tmp = Path(tmp_name)
        try:
            # Pillow PNG optimize uses a better strategy; compress_level=9 is max zlib.
            # This can strip metadata and recompress without changing dimensions.
            im.save(tmp, format="PNG", optimize=True, compress_level=9)

            new = tmp.stat().st_size
            if new and new < old:
                os.replace(str(tmp), str(path))
                return old, new, (w, h)
            return old, old, (w, h)
        finally:
            if tmp.exists():
                try:
                    tmp.unlink()
                except OSError:
                    pass


def main() -> int:
    if not PORTRAITS.exists():
        print(f"[opt] missing {PORTRAITS}")
        return 1

    files = sorted(PORTRAITS.glob("*.png"))
    total_old = 0
    total_new = 0
    changed = 0

    for p in files:
        old, new, (w, h) = optimize_png_in_place(p)
        total_old += old
        total_new += new
        if new < old:
            changed += 1

    saved = total_old - total_new
    pct = (saved / total_old * 100.0) if total_old else 0.0
    print(f"[opt] files={len(files)} changed={changed} old={total_old} new={total_new} saved={saved} ({pct:.1f}%)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
