#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
import ast
import json
import sys
import time

ROOT = Path("/root/mrd")
OUT_JSON = ROOT / "MRD_INDEX.json"
OUT_MD = ROOT / "MRD_INDEX.md"

EXCLUDE_DIRS = {
    ".venv", "venv", "node_modules", "__pycache__", ".git",
    ".mypy_cache", ".pytest_cache", ".idea", ".vscode",
}

LLM_PARAM_HINTS = {"messages", "model", "temperature", "top_p", "stream", "max_tokens", "tools", "tool_choice", "prompt"}
LLM_FN_NAME_HINTS = {"call", "chat", "completion", "complete", "invoke", "generate", "ask"}

MEM_METHOD_HINTS = {"search_hybrid", "search", "query", "retrieve", "vector_search", "similarity_search", "ltm_search_hybrid"}
INNER_METHOD_HINTS = {"process_natural_language_input", "process_natural_language", "analyze", "analyze_intent", "parse_intent"}
RERANK_METHOD_HINTS = {"rerank", "rank", "score", "compress", "compress_text", "compress_knowledge"}

def iter_py_files(root: Path) -> Iterable[Path]:
    for p in root.rglob("*.py"):
        parts = set(p.parts)
        if parts & EXCLUDE_DIRS:
            continue
        yield p

def modpath_from_file(py: Path) -> Optional[str]:
    try:
        rel = py.relative_to(ROOT)
    except Exception:
        return None
    if rel.suffix != ".py":
        return None
    parts = list(rel.parts)
    parts[-1] = parts[-1][:-3]
    if parts[-1] == "__init__":
        parts = parts[:-1]
    if not parts:
        return None
    return ".".join(parts)

def safe_read(p: Path) -> Optional[str]:
    try:
        return p.read_text(encoding="utf-8")
    except Exception:
        try:
            return p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return None

def node_docstring(node: ast.AST) -> str:
    try:
        ds = ast.get_docstring(node)
        return ds.strip() if isinstance(ds, str) else ""
    except Exception:
        return ""

def fn_params(fn: ast.AST) -> List[str]:
    if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return []
    out: List[str] = []
    try:
        args = fn.args
        for a in getattr(args, "posonlyargs", []):
            out.append(a.arg)
        for a in args.args:
            out.append(a.arg)
        if args.vararg is not None:
            out.append("*" + args.vararg.arg)
        for a in args.kwonlyargs:
            out.append(a.arg)
        if args.kwarg is not None:
            out.append("**" + args.kwarg.arg)
    except Exception:
        return []
    return out

def import_reprs(tree: ast.AST) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for n in getattr(tree, "body", []):
        if isinstance(n, ast.Import):
            for a in n.names:
                out.append({"kind": "import", "module": a.name, "as": a.asname, "lineno": int(getattr(n, "lineno", 0) or 0)})
        elif isinstance(n, ast.ImportFrom):
            mod = n.module or ""
            out.append({
                "kind": "from",
                "module": mod,
                "level": int(getattr(n, "level", 0) or 0),
                "names": [{"name": a.name, "as": a.asname} for a in n.names],
                "lineno": int(getattr(n, "lineno", 0) or 0),
            })
    return out

@dataclass
class DefRec:
    name: str
    kind: str  # class/def/async
    lineno: int
    params: List[str]
    doc: str
    methods: List[str]

def class_methods(cls: ast.ClassDef) -> List[str]:
    ms: List[str] = []
    for n in cls.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            ms.append(n.name)
    return ms

def looks_like_llm_fn(name: str, params: List[str]) -> bool:
    low = (name or "").lower()
    pset = {p.lstrip("*").lower() for p in params}
    if (pset & LLM_PARAM_HINTS):
        return True
    if any(h in low for h in LLM_FN_NAME_HINTS) and ("messages" in pset or "prompt" in pset or "text" in pset):
        return True
    return False

def score_capability(defrec: DefRec) -> Dict[str, bool]:
    mset = {m.lower() for m in defrec.methods}
    pset = {p.lstrip("*").lower() for p in defrec.params}
    low = defrec.name.lower()

    is_llm = defrec.kind in ("def", "async") and looks_like_llm_fn(defrec.name, defrec.params)
    is_memory = defrec.kind == "class" and bool(mset & MEM_METHOD_HINTS)
    is_inner = (defrec.kind == "class" and bool(mset & INNER_METHOD_HINTS)) or (defrec.kind in ("def", "async") and any(h in low for h in ("inner", "language", "intent", "analyz", "analiz")))
    is_rerank = defrec.kind == "class" and bool(mset & RERANK_METHOD_HINTS)

    if defrec.kind in ("def", "async") and ("query" in pset or "q" in pset) and any(x in low for x in ("search", "retrieve", "rerank", "rank", "score")):
        is_rerank = is_rerank or ("rank" in low or "rerank" in low or "score" in low)
        is_memory = is_memory or ("search" in low or "retrieve" in low)

    return {"llm": is_llm, "memory": is_memory, "inner": is_inner, "rerank": is_rerank}

def make_md(index: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("# MRD repo index")
    lines.append("")
    lines.append(f"- generated_at: `{index.get('generated_at')}`")
    lines.append(f"- root: `{index.get('root')}`")
    st = index.get("stats", {})
    lines.append(f"- files_scanned: `{st.get('files_scanned')}`")
    lines.append(f"- modules: `{st.get('modules')}`")
    lines.append(f"- defs_total: `{st.get('defs_total')}`")
    lines.append(f"- dur_s: `{st.get('dur_s')}`")
    lines.append("")

    caps = index.get("capabilities", {})

    def sec(title: str, arr_key: str) -> None:
        arr = caps.get(arr_key, [])
        lines.append(f"## {title} ({len(arr)})")
        lines.append("")
        if not arr:
            lines.append("(none)")
            lines.append("")
            return
        for it in arr:
            lines.append(f"- `{it['module']}` :: {it['kind']} `{it['name']}` @ {it['file']}:{it['lineno']}")
            if it.get("methods"):
                ms = it["methods"][:60]
                lines.append(f"  - methods: {', '.join(ms)}")
            if it.get("params"):
                ps = it["params"][:60]
                lines.append(f"  - params: {', '.join(ps)}")
        lines.append("")

    sec("LLM callable candidates", "llm")
    sec("Memory class candidates", "memory")
    sec("Inner language candidates", "inner")
    sec("Reranker / compressor candidates", "rerank")

    lines.append("## All modules")
    lines.append("")
    for m in sorted(index.get("modules", {}).keys()):
        md = index["modules"][m]
        lines.append(f"- `{m}`  ({md.get('file')})  defs={len(md.get('defs', []))} imports={len(md.get('imports', []))} parse_error={md.get('parse_error')}")
    lines.append("")
    return "\n".join(lines)

def main() -> int:
    if not ROOT.exists():
        print(f"[ERR] missing root: {ROOT}", file=sys.stderr)
        return 2

    t0 = time.time()
    modules: Dict[str, Any] = {}
    caps: Dict[str, List[Dict[str, Any]]] = {"llm": [], "memory": [], "inner": [], "rerank": []}
    files_scanned = 0
    defs_total = 0

    for py in iter_py_files(ROOT):
        mp = modpath_from_file(py)
        if not mp:
            continue
        src = safe_read(py)
        if src is None:
            continue
        files_scanned += 1

        try:
            tree = ast.parse(src, filename=str(py))
        except Exception:
            modules[mp] = {"file": str(py), "parse_error": True, "imports": [], "defs": []}
            continue

        imports = import_reprs(tree)
        defs: List[Dict[str, Any]] = []

        for n in getattr(tree, "body", []):
            if isinstance(n, ast.ClassDef):
                rec = DefRec(
                    name=n.name,
                    kind="class",
                    lineno=int(getattr(n, "lineno", 0) or 0),
                    params=[],
                    doc=node_docstring(n),
                    methods=class_methods(n),
                )
                defs_total += 1
                defs.append(asdict(rec))
                cap = score_capability(rec)
                if cap["memory"] or cap["inner"] or cap["rerank"]:
                    entry = {"module": mp, "file": str(py), "lineno": rec.lineno, "kind": rec.kind, "name": rec.name, "params": rec.params, "methods": rec.methods}
                    if cap["memory"]:
                        caps["memory"].append(entry)
                    if cap["inner"]:
                        caps["inner"].append(entry)
                    if cap["rerank"]:
                        caps["rerank"].append(entry)

            elif isinstance(n, ast.FunctionDef):
                rec = DefRec(
                    name=n.name,
                    kind="def",
                    lineno=int(getattr(n, "lineno", 0) or 0),
                    params=fn_params(n),
                    doc=node_docstring(n),
                    methods=[],
                )
                defs_total += 1
                defs.append(asdict(rec))
                cap = score_capability(rec)
                if cap["llm"] or cap["inner"]:
                    entry = {"module": mp, "file": str(py), "lineno": rec.lineno, "kind": rec.kind, "name": rec.name, "params": rec.params, "methods": rec.methods}
                    if cap["llm"]:
                        caps["llm"].append(entry)
                    if cap["inner"]:
                        caps["inner"].append(entry)

            elif isinstance(n, ast.AsyncFunctionDef):
                rec = DefRec(
                    name=n.name,
                    kind="async",
                    lineno=int(getattr(n, "lineno", 0) or 0),
                    params=fn_params(n),
                    doc=node_docstring(n),
                    methods=[],
                )
                defs_total += 1
                defs.append(asdict(rec))
                cap = score_capability(rec)
                if cap["llm"] or cap["inner"]:
                    entry = {"module": mp, "file": str(py), "lineno": rec.lineno, "kind": rec.kind, "name": rec.name, "params": rec.params, "methods": rec.methods}
                    if cap["llm"]:
                        caps["llm"].append(entry)
                    if cap["inner"]:
                        caps["inner"].append(entry)

        modules[mp] = {"file": str(py), "parse_error": False, "imports": imports, "defs": defs}

    index: Dict[str, Any] = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "root": str(ROOT),
        "stats": {
            "files_scanned": files_scanned,
            "modules": len(modules),
            "defs_total": defs_total,
            "dur_s": round(time.time() - t0, 3),
        },
        "capabilities": caps,
        "modules": modules,
    }

    OUT_JSON.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(make_md(index), encoding="utf-8")

    print(f"[OK] wrote {OUT_JSON} and {OUT_MD}")
    print(json.dumps(index["stats"], ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
