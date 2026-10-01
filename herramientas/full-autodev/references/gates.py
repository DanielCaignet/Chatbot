#!/usr/bin/env python3
"""
gates.py - Compuertas deterministas para un proyecto full-autodev.

Sin LLM, sin red, sin estado. Parsea markdown y el sistema de archivos, y
devuelve hallazgos con codigo de salida != 0 si alguna compuerta 'block' dispara.

Uso:
    python gates.py                 # reporte humano, exit 1 si bloquea
    python gates.py --json          # salida JSON
    python gates.py --gate G-EARS   # solo una compuerta
    python gates.py --no-history    # no registrar la corrida

Configuracion: gates.toml en la raiz del proyecto. Si no existe, se usan los
valores por defecto de DEFAULT_CONFIG (convencion generica de la plantilla).
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tomllib
import unicodedata
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


# --------------------------------------------------------------------------
# configuracion
# --------------------------------------------------------------------------

DEFAULT_CONFIG: dict = {
    "project": {"name": "", "root": "."},
    "conventions": {
        "specs_glob": "specs/**/*.md",
        "skip_prefixes": ["_"],
        "req_pattern": r"RQ-[A-Z0-9]+-\d+",
        "closed_states": ["cerrada", "cerrado", "vigente", "aprobada", "aprobado"],
        "state_line": r"\*\*Estado:\*\*\s*(.+)",
        "ears_verb": r"EL SISTEMA DEBER[ÁA]",
        "probe_pattern": r"V-\d+",
        "maturity_file": "",
        "maturity_levels": ["N0", "N1", "N2", "N3"],
        "maturity_needs_limit": ["N1"],
        "references_file": "",
        "ref_cite_pattern": r"\[EXT:(\d+)\]",
        "ref_entry_pattern": r"EXT-(\d+)",
        "decisions_file": "",
        "dec_cite_pattern": r"\bDE-(\d+)\b",
        "dec_entry_pattern": r"DE-(\d+)",
        "state_file": "STATE.md",
        "sprawl_patterns": ["*handoff*.md", "*estado*.md", "*context*.md", "*traspaso*.md"],
        "slop_exclude": [],          # prefijos de ruta que SLOP-SCAN no juzga (artefactos de terceros)
        "sprawl_exempt_dirs": [".git", "vault/Decisiones", "graphify-out"],
        "slop_scanner": "",          # vacio = autodetectar el plugin anti-slop instalado
        "slop_fail_on": "high",      # high | medium | low: severidad minima que se reporta
        "slop_exts": [".py", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".go", ".rs",
                      ".java", ".kt", ".cs", ".rb", ".php", ".swift", ".vue", ".svelte",
                      ".html", ".css", ".scss", ".sql", ".sh", ".ps1"],
        # docs/ queda fuera por defecto: ahi conviven registros historicos (respuestas, revisiones,
        # bitacoras) que no se leen para operar y no ganan nada partidos. Medido 2026-09-29 en
        # CristalChile: 17 avisos, casi todos registros. Cada proyecto agrega sus docs operativos.
        "doc_size_globs": ["vault/**/*.md", "CLAUDE.md"],
        "doc_max_lines": 200,
        "doc_size_exempt": [],       # rutas que crecen por diseno; decisions_file se exime solo
        "orphan_globs": ["vault/**/*.md", "docs/**/*.md"],
        "orphan_exempt": ["AGENT-INDEX.md", "README.md"],
    },
    "gates": {
        "G-REF":       {"enabled": True,  "severity": "block"},
        "G-EARS":      {"enabled": True,  "severity": "block"},
        "G-VERIF":     {"enabled": True,  "severity": "block"},
        "G-N1":        {"enabled": False, "severity": "warn"},
        "TRAZA":       {"enabled": False, "severity": "warn"},
        "REF-DANGLING": {"enabled": False, "severity": "warn"},
        "DE-DANGLING": {"enabled": False, "severity": "warn"},
        "STATE-SPRAWL": {"enabled": True, "severity": "warn"},
        "GRAPH-MISSING": {"enabled": True, "severity": "warn"},
        "DERIVED-COMMITTED": {"enabled": True, "severity": "warn"},
        "SLOP-SCAN":   {"enabled": False, "severity": "warn"},
        "WIKI-DANGLING": {"enabled": True, "severity": "warn"},
        "DOC-SIZE":    {"enabled": True, "severity": "warn"},
        "DOC-ORPHAN":  {"enabled": True, "severity": "warn"},
    },
}


def deep_merge(base: dict, over: dict) -> dict:
    out = dict(base)
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_config(root: Path) -> dict:
    cfg_path = root / "gates.toml"
    if not cfg_path.exists():
        return DEFAULT_CONFIG
    with cfg_path.open("rb") as fh:
        user = tomllib.load(fh)
    return deep_merge(DEFAULT_CONFIG, user)


# --------------------------------------------------------------------------
# modelo
# --------------------------------------------------------------------------

@dataclass
class Finding:
    gate: str
    severity: str
    file: str
    line: int
    message: str
    fix: str = ""


@dataclass
class Spec:
    path: Path
    text: str
    lines: list[str] = field(default_factory=list)
    state: str = ""
    closed: bool = False


def read_specs(root: Path, conv: dict) -> list[Spec]:
    specs: list[Spec] = []
    skip = tuple(conv["skip_prefixes"])
    state_re = re.compile(conv["state_line"], re.IGNORECASE)
    closed_words = [w.lower() for w in conv["closed_states"]]
    for p in sorted(root.glob(conv["specs_glob"])):
        if not p.is_file() or p.name.startswith(skip):
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        state = ""
        for ln in lines[:20]:
            m = state_re.search(ln)
            if m:
                state = m.group(1).strip()
                break
        closed = any(w in state.lower() for w in closed_words)
        specs.append(Spec(path=p, text=text, lines=lines, state=state, closed=closed))
    return specs


def table_rows(lines: list[str]) -> list[tuple[int, list[str]]]:
    """Filas de tabla markdown: (nro de linea 1-based, celdas)."""
    out = []
    for i, ln in enumerate(lines, start=1):
        s = ln.strip()
        if not s.startswith("|") or not s.endswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
            continue  # separador
        out.append((i, cells))
    return out


# --------------------------------------------------------------------------
# compuertas
# --------------------------------------------------------------------------

def gate_ref(root: Path, conv: dict, specs: list[Spec], sev: str) -> list[Finding]:
    """G-REF: una spec cerrada no puede conservar [INT?] sin una sonda V-NN."""
    probe_re = re.compile(conv["probe_pattern"])
    out = []
    for sp in specs:
        if not sp.closed:
            continue
        has_probe = bool(probe_re.search(sp.text))
        for i, ln in enumerate(sp.lines, start=1):
            if "[INT?]" not in ln:
                continue
            if has_probe:
                continue
            out.append(Finding(
                "G-REF", sev, str(sp.path), i,
                f"spec cerrada (Estado: {sp.state}) conserva [INT?] y no declara ninguna sonda "
                f"que lo convierta en [MEDIDO]",
                "agregar una sonda V-NN que lo mida, o eliminar la afirmacion",
            ))
    return out


def gate_ears(root: Path, conv: dict, specs: list[Spec], sev: str) -> list[Finding]:
    """G-EARS: todo RQ- debe estar en una forma EARS reconocible."""
    req_re = re.compile(conv["req_pattern"])
    verb_re = re.compile(conv["ears_verb"])
    out = []
    for sp in specs:
        for lineno, cells in table_rows(sp.lines):
            if not cells:
                continue
            ident = cells[0]
            if not req_re.search(ident):
                continue
            body = cells[1] if len(cells) > 1 else ""
            if "<" in body and ">" in body and len(body) < 90:
                continue  # fila de ejemplo con placeholders
            if not verb_re.search(body):
                out.append(Finding(
                    "G-EARS", sev, str(sp.path), lineno,
                    f"{ident} no usa una forma EARS: falta 'EL SISTEMA DEBERA'",
                    "reescribir como Ubicuo/CUANDO/MIENTRAS/DONDE/SI-ENTONCES",
                ))
                continue
            head = body.strip().upper()
            if head.startswith("SI ") and "ENTONCES" not in head:
                out.append(Finding(
                    "G-EARS", sev, str(sp.path), lineno,
                    f"{ident} empieza con SI pero no tiene ENTONCES",
                    "patron no deseado: SI <condicion> ENTONCES EL SISTEMA DEBERA <respuesta>",
                ))
    return out


def gate_verif(root: Path, conv: dict, specs: list[Spec], sev: str) -> list[Finding]:
    """G-VERIF: un requisito sin verificacion declarada no es un requisito."""
    req_re = re.compile(conv["req_pattern"])
    out = []
    for sp in specs:
        for lineno, cells in table_rows(sp.lines):
            if not cells or not req_re.search(cells[0]):
                continue
            body = cells[1] if len(cells) > 1 else ""
            if "<" in body and ">" in body and len(body) < 90:
                continue
            verif = cells[2].strip() if len(cells) > 2 else ""
            verif = verif.strip("`* ")
            if not verif or verif in {"-", "—", "tbd", "TBD", "?"}:
                out.append(Finding(
                    "G-VERIF", sev, str(sp.path), lineno,
                    f"{cells[0]} no declara metodo de verificacion (test o eval con umbral)",
                    "declarar test/eval, o mover el requisito a BACKLOG.md",
                ))
    return out


def gate_traza(root: Path, conv: dict, specs: list[Spec], sev: str) -> list[Finding]:
    """TRAZA: el artefacto de verificacion citado por un RQ- existe en disco."""
    req_re = re.compile(conv["req_pattern"])
    out = []
    for sp in specs:
        for lineno, cells in table_rows(sp.lines):
            if not cells or not req_re.search(cells[0]):
                continue
            art = cells[3].strip("`* ") if len(cells) > 3 else ""
            if not art or "<" in art:
                continue
            cand = root / art.replace("\\", "/")
            if not cand.exists():
                out.append(Finding(
                    "TRAZA", sev, str(sp.path), lineno,
                    f"{cells[0]} apunta a un artefacto inexistente: {art}",
                    "crear el artefacto, o corregir la ruta",
                ))
    return out


def _head(cell: str) -> str:
    """Encabezado normalizado: sin enfasis, sin tildes, en minusculas."""
    s = unicodedata.normalize("NFKD", cell.strip("*_ `"))
    return "".join(ch for ch in s if not unicodedata.combining(ch)).lower()


_SEP_ROW = re.compile(r"\|(\s*:?-{2,}:?\s*\|)+")


def gate_n1(root: Path, conv: dict, specs: list[Spec], sev: str) -> list[Finding]:
    """G-N1: toda pieza en un nivel que exige limite lo tiene escrito.

    El archivo de madurez es el dueno unico del nivel (por defecto, el MOC de specs).
    Si la tabla tiene columnas `Nivel` y `Limite`, se leen por nombre. Si no
    (convencion propia del proyecto), heuristica: el nivel es cualquier token de la
    fila y el limite cualquier celda de >= 6 palabras.
    """
    mfile = conv.get("maturity_file") or ""
    if not mfile:
        return []
    p = root / mfile
    if not p.exists():
        return [Finding("G-N1", sev, mfile, 0, "no existe el archivo de madurez", "")]
    lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    needs = set(conv["maturity_needs_limit"])
    level_res = [(lv, re.compile(rf"\b{re.escape(lv)}\b")) for lv in conv["maturity_levels"]]
    out = []
    col_lvl = col_lim = None
    prev = 0
    for lineno, cells in table_rows(lines):
        # una linea que no es fila ni separador entre dos filas = tabla nueva
        if any(not _SEP_ROW.fullmatch(b.strip()) for b in lines[prev:lineno - 1]):
            col_lvl = col_lim = None
        prev = lineno
        heads = [_head(c) for c in cells]
        if "nivel" in heads and "limite" in heads:
            col_lvl, col_lim = heads.index("nivel"), heads.index("limite")
            continue
        by_col = col_lvl is not None and max(col_lvl, col_lim) < len(cells)
        lvl_text = cells[col_lvl] if by_col else " ".join(cells)
        lvl = next((lv for lv, rx in level_res if rx.search(lvl_text)), None)
        if lvl not in needs:
            continue
        if by_col:
            has_limit = len(cells[col_lim].split()) >= 6
        else:
            has_limit = any(len(c.split()) >= 6 for c in cells[1:])
        if not has_limit:
            out.append(Finding(
                "G-N1", sev, mfile, lineno,
                f"capa declarada {lvl} sin frase de limite falsable: {cells[0]}",
                "escribir el limite como una frase refutable, o bajar el nivel",
            ))
    return out


def _dangling(root: Path, cite_pat: str, entry_pat: str, registry: str,
              specs: list[Spec], gate: str, sev: str) -> list[Finding]:
    if not registry:
        return []
    reg_path = (root / registry).resolve()
    if not reg_path.exists():
        return [Finding(gate, sev, registry, 0, "registro no encontrado", "")]
    reg_text = reg_path.read_text(encoding="utf-8", errors="replace")
    known = set(re.findall(entry_pat, reg_text))
    cite_re = re.compile(cite_pat)
    out = []
    for sp in specs:
        for i, ln in enumerate(sp.lines, start=1):
            for m in cite_re.finditer(ln):
                if m.group(1) not in known:
                    out.append(Finding(
                        gate, sev, str(sp.path), i,
                        f"cita {m.group(0)} que no existe en {registry}",
                        f"agregar la entrada en {registry} o corregir la cita",
                    ))
    return out


def gate_state_sprawl(root: Path, conv: dict, sev: str) -> list[Finding]:
    """STATE-SPRAWL: reaparecio el piloncito de handoffs numerados."""
    exempt = [root / d for d in conv["sprawl_exempt_dirs"]]
    found = []
    for pat in conv["sprawl_patterns"]:
        for p in root.rglob(pat):
            if not p.is_file():
                continue
            if any(str(p).startswith(str(e)) for e in exempt):
                continue
            if p.name == conv["state_file"]:
                continue
            found.append(p)
    if len(found) < 2:
        return []
    return [Finding(
        "STATE-SPRAWL", sev, str(found[0].parent), 0,
        f"{len(found)} archivos de estado/handoff coexisten: "
        + ", ".join(sorted(p.name for p in found)[:6]),
        f"consolidar en {conv['state_file']} (se sobreescribe) y mover la historia a decisiones",
    )]


def gate_graph(root: Path, sev: str) -> list[Finding]:
    if (root / "graphify-out" / "graph.json").exists():
        return []
    return [Finding(
        "GRAPH-MISSING", sev, "graphify-out/graph.json", 0,
        "no hay grafo: la puerta de consumo no puede cerrarse y el agente vuelve a leer fuentes en bloque",
        "construir el grafo con la skill graphify sobre la raiz",
    )]


def gate_derived_committed(root: Path, sev: str) -> list[Finding]:
    gi = root / ".gitignore"
    if not (root / ".git").exists():
        return []
    ignored = gi.exists() and "graphify-out" in gi.read_text(encoding="utf-8", errors="replace")
    if ignored:
        return []
    return [Finding(
        "DERIVED-COMMITTED", sev, ".gitignore", 0,
        "graphify-out/ no esta en .gitignore: un indice derivado versionado genera "
        "conflictos de merge y se lee como fuente",
        "agregar graphify-out/ a .gitignore",
    )]


_WIKILINK = re.compile(r"\[\[([^\]|#]+)(?:[#|][^\]]*)?\]\]")
_CODE = re.compile(r"```.*?```|`[^`\n]*`", re.S)


def gate_wiki(root: Path, conv: dict, sev: str) -> list[Finding]:
    """WIKI-DANGLING: todo [[enlace]] resuelve a una nota. La raiz ES el vault (Obsidian y
    graphify resuelven por nombre de archivo exacto), asi que [[SPEC-002]] exige SPEC-002.md.
    Un enlace roto es una arista que el grafo no tiene: el agente no encuentra lo enlazado."""
    skip_dirs = {".git", "graphify-out", "node_modules", ".specify"}
    stems = {p.stem for p in root.rglob("*.md") if not skip_dirs & set(p.parts)}
    out = []
    for g in conv.get("wiki_globs", ["vault/**/*.md", "specs/**/*.md", "STATE.md"]):
        for p in sorted(root.glob(g)):
            if not p.is_file() or p.name.startswith("_"):
                continue  # plantillas: sus enlaces son marcadores
            text = _CODE.sub("", p.read_text(encoding="utf-8", errors="replace"))
            for lineno, ln in enumerate(text.splitlines(), start=1):
                for m in _WIKILINK.finditer(ln):
                    t = m.group(1).strip()
                    if t not in stems:
                        out.append(Finding("WIKI-DANGLING", sev, p.relative_to(root).as_posix(), lineno,
                                           f"[[{t}]] no resuelve a ninguna nota",
                                           f"crear {t}.md, renombrar la nota al ID exacto, o corregir el enlace"))
    return out


_DOC_SKIP_DIRS = {".git", "graphify-out", "node_modules", ".specify", ".gates", ".claude"}


def _doc_candidates(root: Path, globs: list[str]) -> list[Path]:
    seen: dict[Path, None] = {}
    for g in globs:
        for p in sorted(root.glob(g)):
            rel = p.relative_to(root)
            if p.is_file() and not p.name.startswith("_") and not _DOC_SKIP_DIRS & set(rel.parts):
                seen[p] = None
    return list(seen)


def gate_doc_size(root: Path, conv: dict, sev: str) -> list[Finding]:
    """DOC-SIZE: un documento paso de doc_max_lines. No prueba que haya que partirlo: pide
    mirar si tiene partes que se leen en momentos distintos (SKILL.md, Archivos modulares)."""
    limit = int(conv["doc_max_lines"])
    exempt = {e.replace("\\", "/") for e in conv["doc_size_exempt"]}
    if conv.get("decisions_file"):
        exempt.add(conv["decisions_file"].replace("\\", "/"))
    out = []
    for p in _doc_candidates(root, conv["doc_size_globs"]):
        rel = p.relative_to(root).as_posix()
        if rel in exempt:
            continue
        n = len(p.read_text(encoding="utf-8", errors="replace").splitlines())
        if n > limit:
            out.append(Finding("DOC-SIZE", sev, rel, 0,
                               f"{n} lineas (limite {limit})",
                               "si tiene partes que se leen en momentos distintos, dividirlo y enlazar "
                               "cada pieza desde un indice; si se lee siempre entero, sumarlo a doc_size_exempt"))
    return out


def gate_doc_orphan(root: Path, conv: dict, sev: str) -> list[Finding]:
    """DOC-ORPHAN: una nota que ningun otro .md enlaza ([[nombre]]) ni nombra (nombre.md).
    El agente llega a las notas siguiendo enlaces desde STATE.md y AGENT-INDEX.md: una nota
    sin enlace entrante no existe para el."""
    texts: dict[Path, str] = {}
    for p in root.rglob("*.md"):
        if p.is_file() and not _DOC_SKIP_DIRS & set(p.relative_to(root).parts):
            texts[p] = p.read_text(encoding="utf-8", errors="replace")
    incoming: dict[Path, set[str]] = {}
    for p, t in texts.items():
        targets = {m.group(1).strip().rsplit("/", 1)[-1].removesuffix(".md") for m in _WIKILINK.finditer(t)}
        incoming[p] = targets
    exempt = set(conv["orphan_exempt"])
    out = []
    for p in _doc_candidates(root, conv["orphan_globs"]):
        if p.name in exempt:
            continue
        linked = any(q != p and (p.stem in incoming[q] or p.name in t) for q, t in texts.items())
        if not linked:
            out.append(Finding("DOC-ORPHAN", sev, p.relative_to(root).as_posix(), 0,
                               "ninguna otra nota la enlaza ni la nombra",
                               "enlazarla desde su indice (AGENT-INDEX.md, un MOC o el documento padre), "
                               "o borrarla si quedo obsoleta"))
    return out


_SLOP_RANK = {"low": 1, "medium": 2, "high": 3}


def _find_slop_scanner(conv: dict) -> Path | None:
    if conv.get("slop_scanner"):
        p = Path(conv["slop_scanner"]).expanduser()
        return p if p.exists() else None
    cache = Path.home() / ".claude" / "plugins" / "cache" / "anti-slop" / "anti-slop"
    found = sorted(cache.glob("*/scripts/slop-scanner.mjs"),
                   key=lambda p: [int(x) if x.isdigit() else 0 for x in p.parts[-3].split(".")])
    return found[-1] if found else None


def _changed_files(root: Path) -> list[str]:
    """Staged + no staged + no rastreados, sin borrados. Sin HEAD (repo nuevo) no falla."""
    def git(*a: str) -> list[str]:
        try:
            out = subprocess.run(["git", *a], cwd=root, capture_output=True, text=True, timeout=30)
        except (OSError, subprocess.TimeoutExpired):
            return []
        return out.stdout.splitlines() if out.returncode == 0 else []
    names = set(git("diff", "--name-only", "--diff-filter=d", "--cached"))
    names |= set(git("diff", "--name-only", "--diff-filter=d", "HEAD"))
    names |= set(git("ls-files", "--others", "--exclude-standard"))
    return sorted(n for n in names if n)


def gate_slop(root: Path, conv: dict, sev: str) -> list[Finding]:
    """SLOP-SCAN: el scanner determinista del plugin anti-slop sobre lo que cambio.

    Solo la capa regex del catalogo: un scan limpio es un piso, no una revision de
    seguridad. La revision semantica es `/slop-check diff` y `/thermos`, fuera de aca.
    Si falta el scanner o node, avisa y nunca bloquea: una maquina sin el plugin no
    debe quedar sin poder commitear.
    """
    if not (root / ".git").exists():
        return []
    scanner, node = _find_slop_scanner(conv), shutil.which("node")
    if not scanner or not node:
        falta = "el plugin anti-slop" if not scanner else "node"
        return [Finding("SLOP-SCAN", "warn", "gates.toml", 0,
                        f"no se puede correr el scanner: falta {falta}",
                        "claude plugin install anti-slop@anti-slop, o fijar conventions.slop_scanner")]
    exts = tuple(conv["slop_exts"])
    skip = ("graphify-out/", ".gates/", *conv.get("slop_exclude", []))
    files = [f for f in _changed_files(root) if f.endswith(exts) and not f.startswith(skip)]
    floor = _SLOP_RANK.get(conv.get("slop_fail_on", "high"), 3)
    out: list[Finding] = []
    for i in range(0, len(files), 50):  # lotes: la linea de comandos de Windows tiene tope
        chunk = files[i:i + 50]
        try:
            res = subprocess.run([node, str(scanner), "scan", "--format", "json", "--fail-on", "none",
                                  *chunk], cwd=root, capture_output=True, text=True, timeout=120,
                                 encoding="utf-8", errors="replace")
            data = json.loads(res.stdout or "{}")
        except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as e:
            return out + [Finding("SLOP-SCAN", "warn", str(scanner), 0,
                                  f"el scanner fallo: {type(e).__name__}", "correrlo a mano para ver el error")]
        for f in data.get("files", []):
            rel = Path(f.get("file", "")).resolve()
            try:
                rel = rel.relative_to(root.resolve())
            except ValueError:
                pass
            for v in f.get("violations", []):
                if _SLOP_RANK.get(v.get("severity", ""), 0) < floor:
                    continue
                out.append(Finding("SLOP-SCAN", sev, rel.as_posix(), int(v.get("line") or 0),
                                   f"[{v.get('severity')}] {v.get('name')}: {v.get('desc', '')}",
                                   v.get("fix", "")))
    return out


# --------------------------------------------------------------------------
# runner
# --------------------------------------------------------------------------

def run(root: Path, cfg: dict, only: str | None) -> list[Finding]:
    conv = cfg["conventions"]
    gates = cfg["gates"]
    specs = read_specs(root, conv)
    findings: list[Finding] = []

    def on(name: str) -> tuple[bool, str]:
        g = gates.get(name, {})
        if not g.get("enabled", False):
            return False, ""
        if only and only != name:
            return False, ""
        return True, g.get("severity", "warn")

    ok, sev = on("G-REF")
    if ok: findings += gate_ref(root, conv, specs, sev)
    ok, sev = on("G-EARS")
    if ok: findings += gate_ears(root, conv, specs, sev)
    ok, sev = on("G-VERIF")
    if ok: findings += gate_verif(root, conv, specs, sev)
    ok, sev = on("TRAZA")
    if ok: findings += gate_traza(root, conv, specs, sev)
    ok, sev = on("G-N1")
    if ok: findings += gate_n1(root, conv, specs, sev)
    ok, sev = on("REF-DANGLING")
    if ok:
        findings += _dangling(root, conv["ref_cite_pattern"], conv["ref_entry_pattern"],
                              conv.get("references_file", ""), specs, "REF-DANGLING", sev)
    ok, sev = on("DE-DANGLING")
    if ok:
        findings += _dangling(root, conv["dec_cite_pattern"], conv["dec_entry_pattern"],
                              conv.get("decisions_file", ""), specs, "DE-DANGLING", sev)
    ok, sev = on("STATE-SPRAWL")
    if ok: findings += gate_state_sprawl(root, conv, sev)
    ok, sev = on("GRAPH-MISSING")
    if ok: findings += gate_graph(root, sev)
    ok, sev = on("DERIVED-COMMITTED")
    if ok: findings += gate_derived_committed(root, sev)
    ok, sev = on("SLOP-SCAN")
    if ok: findings += gate_slop(root, conv, sev)
    ok, sev = on("WIKI-DANGLING")
    if ok: findings += gate_wiki(root, conv, sev)
    ok, sev = on("DOC-SIZE")
    if ok: findings += gate_doc_size(root, conv, sev)
    ok, sev = on("DOC-ORPHAN")
    if ok: findings += gate_doc_orphan(root, conv, sev)

    return findings


def record_history(root: Path, findings: list[Finding], nspecs: int) -> None:
    """Linea de mejora: cada corrida deja rastro para poder optimizar las reglas."""
    d = root / ".gates"
    d.mkdir(exist_ok=True)
    counts: dict[str, int] = {}
    for f in findings:
        counts[f.gate] = counts.get(f.gate, 0) + 1
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "specs": nspecs,
        "total": len(findings),
        "by_gate": counts,
    }
    with (d / "history.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def show_stats(root: Path, cfg: dict) -> int:
    """Linea de mejora: que reglas trabajan, cuales estan muertas, que empeora."""
    hist = root / ".gates" / "history.jsonl"
    if not hist.exists():
        print("\nsin historial todavia: corre gates.py al menos una vez\n")
        return 0
    runs = []
    for line in hist.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                runs.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    if not runs:
        print("\nhistorial vacio\n")
        return 0

    enabled = {g for g, v in cfg["gates"].items() if v.get("enabled")}
    fired: dict[str, int] = {}
    for r in runs:
        for g, n in r.get("by_gate", {}).items():
            fired[g] = fired.get(g, 0) + n

    print(f"\ngates --stats · {len(runs)} corridas")
    print(f"  primera : {runs[0]['ts']}")
    print(f"  ultima  : {runs[-1]['ts']}")
    print(f"  hallazgos: {runs[0]['total']} -> {runs[-1]['total']}")

    print("\nreglas que trabajan")
    for g, n in sorted(fired.items(), key=lambda kv: -kv[1]):
        print(f"  {g:<20} {n:>5} hallazgos acumulados")

    dead = sorted(enabled - set(fired))
    if dead:
        print("\nreglas que nunca dispararon (candidatas a revisar o retirar)")
        for g in dead:
            print(f"  {g}")

    if len(runs) >= 2 and runs[-1]["total"] > runs[-2]["total"]:
        delta = runs[-1]["total"] - runs[-2]["total"]
        print(f"\nREGRESION: {delta} hallazgos mas que la corrida anterior")

    fb = root / ".gates" / "feedback.md"
    if fb.exists():
        pend = [l for l in fb.read_text(encoding="utf-8").splitlines()
                if l.strip().startswith("- [ ]")]
        if pend:
            print(f"\nretroalimentacion pendiente ({len(pend)})")
            for l in pend[:8]:
                print(f"  {l.strip()}")
    print()
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Compuertas deterministas full-autodev")
    ap.add_argument("--root", default=".", help="raiz del proyecto")
    ap.add_argument("--json", action="store_true", help="salida JSON")
    ap.add_argument("--gate", default=None, help="correr solo esta compuerta")
    ap.add_argument("--no-history", action="store_true", help="no registrar la corrida")
    ap.add_argument("--stats", action="store_true",
                    help="resumen del historial: que reglas trabajan y cuales estan muertas")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    cfg = load_config(root)

    if args.stats:
        return show_stats(root, cfg)
    findings = run(root, cfg, args.gate)
    nspecs = len(read_specs(root, cfg["conventions"]))

    if not args.no_history:
        record_history(root, findings, nspecs)

    blocking = [f for f in findings if f.severity == "block"]

    if args.json:
        print(json.dumps({
            "root": str(root),
            "specs": nspecs,
            "findings": [asdict(f) for f in findings],
            "blocking": len(blocking),
        }, ensure_ascii=False, indent=2))
        return 1 if blocking else 0

    name = cfg["project"].get("name") or root.name
    print(f"\ngates · {name}")
    print(f"  specs analizadas: {nspecs}")
    if not findings:
        print("  sin hallazgos\n")
        return 0

    by_gate: dict[str, list[Finding]] = {}
    for f in findings:
        by_gate.setdefault(f.gate, []).append(f)

    print()
    for gate in sorted(by_gate, key=lambda g: (by_gate[g][0].severity != "block", g)):
        items = by_gate[gate]
        mark = "BLOQUEA" if items[0].severity == "block" else "avisa"
        print(f"{gate} [{mark}] ({len(items)})")
        for f in items[:10]:
            loc = f"{f.file}:{f.line}" if f.line else f.file
            print(f"  {loc}")
            print(f"    {f.message}")
            if f.fix:
                print(f"    -> {f.fix}")
        if len(items) > 10:
            print(f"  ... y {len(items) - 10} mas")
        print()

    print(f"total: {len(findings)} hallazgos, {len(blocking)} bloqueantes\n")
    return 1 if blocking else 0


if __name__ == "__main__":
    raise SystemExit(main())
