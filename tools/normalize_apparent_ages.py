from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "tools" / "sp_by_night_source.json"


def clamp_age(v) -> tuple[str | None, bool]:
    """
    Return (new_value, changed?). Keeps original string if <=40, clamps to "40" if >40.
    If v is missing/unparseable, returns (None, False) meaning "leave as-is".
    """
    if v is None:
        return None, False
    s = str(v).strip()
    m = re.search(r"\d+", s)
    if not m:
        return None, False
    n = int(m.group(0))
    if n > 40:
        return "40", True
    # Preserve original formatting but normalize to digits string (project uses strings mostly)
    if s != str(n):
        return str(n), True
    return s, False


def patch_ficha(txt: str, clan: str | None) -> tuple[str, bool]:
    if not txt:
        return txt, False
    changed = False
    lines = txt.splitlines()
    out: list[str] = []
    for line in lines:
        if line.strip().lower().startswith("idade aparente:"):
            if (clan or "").lower() == "nosferatu":
                changed = True
                continue  # remove line entirely
            newv, ch = clamp_age(line)
            if ch and newv:
                # Replace the first number after "Idade aparente:" with newv
                line2 = re.sub(r"(?i)(idade aparente:\s*)\d+", r"\g<1>" + newv, line, count=1)
                if line2 != line:
                    line = line2
                    changed = True
            out.append(line)
            continue
        out.append(line)
    return "\n".join(out).rstrip() + "\n", changed


def patch_historia(txt: str, clan: str | None) -> tuple[str, bool]:
    if not txt:
        return txt, False
    changed = False
    lines = txt.splitlines()
    out: list[str] = []
    for line in lines:
        # common pattern in our histories: "- Dominio: X | Idade aparente: N"
        if (clan or "").lower() == "nosferatu":
            if re.search(r"(?i)\\bidade aparente\\b", line):
                # remove the " | Idade aparente: N" segment, or drop the whole line if it's only that
                line2 = re.sub(r"(?i)\\s*\\|\\s*idade aparente\\s*:\\s*[^|]+", "", line).rstrip()
                line2 = re.sub(r"(?i)^\\s*idade aparente\\s*:\\s*.*$", "", line2).rstrip()
                if not line2:
                    changed = True
                    continue
                if line2 != line:
                    changed = True
                out.append(line2)
                continue
        # non-nosferatu: clamp any explicit "Idade aparente: N"
        if re.search(r"(?i)\\bidade aparente\\s*:\\s*\\d+", line):
            m = re.search(r"(?i)\\bidade aparente\\s*:\\s*(\\d+)", line)
            if m:
                n = int(m.group(1))
                if n > 40:
                    line2 = re.sub(r"(?i)(\\bidade aparente\\s*:\\s*)\\d+", r"\\g<1>40", line, count=1)
                    if line2 != line:
                        line = line2
                        changed = True
        out.append(line)
    return "\n".join(out).rstrip() + "\n", changed


def main() -> int:
    data = json.loads(SRC.read_text(encoding="utf-8"))
    ents = data.get("entities") or []
    changed_entities = 0
    removed_nos_age = 0
    clamped = 0

    for e in ents:
        clan = (e.get("clan") or "").strip()
        is_nos = clan.lower() == "nosferatu" and (e.get("kind") == "kindred")

        if is_nos:
            if "apparent_age" in e:
                e.pop("apparent_age", None)
                removed_nos_age += 1
        else:
            newv, ch = clamp_age(e.get("apparent_age"))
            if ch and newv is not None:
                e["apparent_age"] = newv
                clamped += 1

        docs = (e.get("docs") or {}).get("files") or {}
        if isinstance(docs, dict):
            if "ficha_resumida" in docs:
                newtxt, ch2 = patch_ficha(docs.get("ficha_resumida") or "", clan if is_nos else clan)
                if ch2:
                    docs["ficha_resumida"] = newtxt
                    changed_entities += 1
            if "historia" in docs:
                newtxt, ch3 = patch_historia(docs.get("historia") or "", clan if is_nos else clan)
                if ch3:
                    docs["historia"] = newtxt
                    changed_entities += 1

    SRC.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[ages] clamped_non_nosferatu={clamped} removed_nosferatu_field={removed_nos_age} docs_patched={changed_entities}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

