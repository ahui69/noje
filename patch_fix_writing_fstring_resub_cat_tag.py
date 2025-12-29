#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from datetime import datetime
import re
import sys

P = Path("/root/mrd/core/writing.py")

def backup(path: Path) -> Path:
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    b = Path(str(path) + f".bak.{ts}")
    b.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    return b

def ensure_import_re(text: str) -> str:
    if re.search(r"(?m)^\s*import\s+re\s*$", text) or re.search(r"(?m)^\s*from\s+re\s+import\s+", text):
        return text

    lines = text.splitlines(True)
    insert_at = 0

    # shebang / encoding
    while insert_at < len(lines) and (lines[insert_at].startswith("#!") or "coding" in lines[insert_at]):
        insert_at += 1

    # future imports
    while insert_at < len(lines) and re.match(r"^\s*from\s+__future__\s+import\b", lines[insert_at]):
        insert_at += 1

    # module docstring
    if insert_at < len(lines) and lines[insert_at].lstrip().startswith(('"""', "'''")):
        q = lines[insert_at].lstrip()[:3]
        insert_at += 1
        while insert_at < len(lines) and q not in lines[insert_at]:
            insert_at += 1
        if insert_at < len(lines):
            insert_at += 1

    lines.insert(insert_at, "import re\n")
    return "".join(lines)

def main() -> int:
    if not P.exists():
        print(f"[ERR] missing file: {P}", file=sys.stderr)
        return 2

    original = P.read_text(encoding="utf-8")
    text = ensure_import_re(original)
    lines = text.splitlines(True)

    # pattern: #{re.sub(r'\\W+', '', cat_tag)}  or any re.sub(..., cat_tag) inside #{...}
    expr_pat = re.compile(
        r"#\{re\.sub\(\s*r[\"'].*?[\"']\s*,\s*[\"'].*?[\"']\s*,\s*cat_tag\s*\)\}",
        re.M,
    )

    out: list[str] = []
    changed = 0

    for ln in lines:
        if "lines.append" in ln and "Hashtagi:" in ln and "#{re.sub(" in ln and "cat_tag" in ln and expr_pat.search(ln):
            indent = re.match(r"^(\s*)", ln).group(1)

            # precompute: always correct regex \W+ (single backslash) and empty replacement
            out.append(f'{indent}cat_tag_clean = re.sub(r"\\W+", "", cat_tag)\n')

            # replace the whole #{re.sub(...)} with #{cat_tag_clean}
            ln2 = expr_pat.sub("#{cat_tag_clean}", ln)

            if ln2 != ln:
                out.append(ln2)
                changed += 1
            else:
                # safety: if something weird, keep original line (no silent corruption)
                out.append(ln)
            continue

        out.append(ln)

    if changed == 0:
        print("[OK] nothing to patch (no matching f-string re.sub(..., cat_tag) pattern found)")
        return 0

    b = backup(P)
    P.write_text("".join(out), encoding="utf-8")
    print(f"[OK] patched {P} (backup: {b}) fixes={changed}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
