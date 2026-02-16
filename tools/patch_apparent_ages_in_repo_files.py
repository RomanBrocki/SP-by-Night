from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

TARGET_DIRS = [
    ROOT / "02_NPCS",
    ROOT / "03_SERVOS_E_CONTATOS",
    ROOT / "01_BACKGROUND_NARRADOR",
    ROOT / "00_BACKGROUND_JOGADORES",
    ROOT / "04_ANTAGONISTAS_V5",
]


def clamp_num(n: int) -> int:
    return 40 if n > 40 else n


def patch_text(path: Path, txt: str) -> str:
    is_nos = "nosferatu" in str(path).lower().replace("\\", "/").split("/")

    lines = txt.splitlines()
    out: list[str] = []
    for line in lines:
        # Remove/Clamp explicit "Idade aparente:" lines
        if re.match(r"(?i)^\s*idade aparente\s*:", line):
            if is_nos:
                continue
            m = re.search(r"(?i)\bidade aparente\s*:\s*(\d+)", line)
            if m:
                n = int(m.group(1))
                if n > 40:
                    line = re.sub(r"(?i)(\bidade aparente\s*:\s*)\d+", r"\g<1>40", line, count=1)
            out.append(line)
            continue

        # In histories, age often appears as a segment: " | Idade aparente: N"
        if is_nos and re.search(r"(?i)\bidade aparente\b", line):
            # Remove only the age segment, keep the rest.
            line2 = re.sub(r"(?i)\s*\|\s*idade aparente\s*:\s*[^|]+", "", line).rstrip()
            # If line is only about age, drop it
            line2 = re.sub(r"(?i)^\s*idade aparente\s*:\s*.*$", "", line2).rstrip()
            if not line2:
                continue
            out.append(line2)
            continue

        # Non-Nosferatu: clamp any inline "Idade aparente: N"
        def repl(m: re.Match) -> str:
            n = int(m.group(1))
            return f"Idade aparente: {clamp_num(n)}"

        line2 = re.sub(r"Idade aparente:\s*(\d+)", repl, line)
        out.append(line2)

    # Preserve trailing newline
    return "\n".join(out).rstrip() + "\n"


def main() -> int:
    patched = 0
    scanned = 0
    for base in TARGET_DIRS:
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if not p.is_file():
                continue
            if p.suffix.lower() not in {".txt", ".md", ".html", ".yml", ".yaml", ".json"}:
                continue
            scanned += 1
            try:
                raw = p.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                # Fall back to cp1252 for some Windows-authored text.
                raw = p.read_text(encoding="cp1252")
            new = patch_text(p, raw)
            if new != raw:
                p.write_text(new, encoding="utf-8", newline="\n")
                patched += 1
    print(f"[ages-files] scanned={scanned} patched={patched}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

