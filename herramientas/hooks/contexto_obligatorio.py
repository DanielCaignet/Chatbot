#!/usr/bin/env python3
"""PreToolUse: hace cumplir la regla «context-mode para leer, buscar y traer webs».

Bloquea Grep, WebFetch, Read grande sin rango y los comandos de lectura en Bash/PowerShell,
y redirige a las herramientas ctx_*. Deja pasar lo que muta estado y las salidas cortas y
fijas (git status, pwd, ls sin -R).
Válvula de escape del usuario: crear ~/.claude/hooks/.ctx_off (apaga el hook) y borrarlo después.
"""
import json
import os
import re
import sys

APAGADO = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".ctx_off")
LIMITE_READ_BYTES = 16 * 1024
LIMITE_READ_LINEAS = 400
BINARIOS = {".pdf", ".docx", ".xlsx", ".pptx", ".png", ".jpg", ".jpeg", ".gif", ".webp",
            ".ipynb", ".msg", ".epub"}

CARGAR = (
    "Si las herramientas ctx_* no están cargadas, cárgalas ahora con ToolSearch "
    "(`select:mcp__plugin_context-mode_context-mode__ctx_batch_execute,"
    "mcp__plugin_context-mode_context-mode__ctx_execute,"
    "mcp__plugin_context-mode_context-mode__ctx_execute_file,"
    "mcp__plugin_context-mode_context-mode__ctx_search,"
    "mcp__plugin_context-mode_context-mode__ctx_fetch_and_index`). "
    "No uses este bloqueo como motivo para saltarte la regla."
)
USO = (
    "Regla dura (~/.claude/CLAUDE.md): leer, buscar, grep, diff, inspeccionar repos y traer webs "
    "siempre con context-mode. "
)

# Comandos que leen o buscan y cuya salida entra entera en la conversación.
LECTURA = {
    "cat", "type", "head", "tail", "more", "less", "grep", "egrep", "fgrep", "rg", "ag", "ack",
    "find", "tree", "diff", "fc", "comp", "curl", "wget", "get-content", "gc", "select-string",
    "sls", "invoke-webrequest", "iwr", "invoke-restmethod", "irm", "findstr", "bat", "nl",
}
PREFIJOS = {"&", ".", "then", "do", "else", "{", "env", "command", "time", "exec", "nohup"}
ASIGNACION = re.compile(r"^[A-Za-z_]\w*=")
GIT_LECTURA = {"diff", "log", "show", "grep", "blame", "shortlog", "ls-files", "ls-tree", "cat-file"}
GIT_OPC_CON_VALOR = {"-c", "-C", "--git-dir", "--work-tree", "--namespace"}
GH_LECTURA = {"view", "list", "diff", "api", "search", "status", "checks"}
LISTADO_RECURSIVO = re.compile(r"(^|\s)(-[a-z]*r[a-z]*|-recurse|/s)(\s|$)", re.I)
REDIRIGE = re.compile(r"(^|[^<>2&])>>?(?!&)|\btee\b|\bout-file\b|\bset-content\b|\badd-content\b", re.I)


def denegar(motivo):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse", "permissionDecision": "deny",
        "permissionDecisionReason": USO + motivo + " " + CARGAR}}, ensure_ascii=False))
    return 0


def _nombre(tok):
    tok = tok.strip("\"'").replace("\\", "/").rsplit("/", 1)[-1].lower()
    return tok[:-4] if tok.endswith(".exe") else tok


def _segmentos(cmd):
    """Primer comando de cada sublista (&&, ||, ;, salto de línea); los filtros tras | no cuentan."""
    for sub in re.split(r"&&|\|\||;|\r?\n", cmd):
        yield re.split(r"(?<!\|)\|(?!\|)", sub, maxsplit=1)[0].strip()


def _palabras(seg):
    pal = seg.split()
    while pal and (pal[0].lower() in PREFIJOS or ASIGNACION.match(pal[0])):
        pal = pal[1:]
    return pal


def _git(pal):
    i = 1
    while i < len(pal) and pal[i].startswith("-"):
        i += 2 if pal[i] in GIT_OPC_CON_VALOR else 1
    sub = pal[i].lower() if i < len(pal) else ""
    return sub if sub in GIT_LECTURA else None


def lectura_en(cmd):
    """Devuelve el comando de lectura que contiene `cmd`, o None."""
    for seg in _segmentos(cmd):
        pal = _palabras(seg)
        if not pal:
            continue
        nombre = _nombre(pal[0])
        if nombre in LECTURA:
            if REDIRIGE.search(seg):  # `cat <<EOF > f`: escribe, no lee
                continue
            return nombre
        if nombre == "git" and (sub := _git(pal)):
            return f"git {sub}"
        if nombre == "gh" and len(pal) > 2 and pal[2].lower() in GH_LECTURA:
            return f"gh {pal[1]} {pal[2]}"
        if nombre in {"ls", "dir", "get-childitem", "gci"} and LISTADO_RECURSIVO.search(seg):
            return f"{nombre} recursivo"
    return None


def pre_tool_use(ev):
    tool = ev.get("tool_name", "")
    ent = ev.get("tool_input") or {}
    if tool == "Grep":
        return denegar("Grep directo no: usa ctx_search (si ya está indexado) o ctx_batch_execute "
                       "con un grep dentro del comando y `queries`.")
    if tool == "WebFetch":
        return denegar("WebFetch no: usa ctx_fetch_and_index y luego ctx_search.")
    if tool == "Read":
        ruta = ent.get("file_path") or ""
        if os.path.splitext(ruta)[1].lower() in BINARIOS or ent.get("limit"):
            return 0
        try:
            grande = os.path.getsize(ruta) > LIMITE_READ_BYTES
        except OSError:
            return 0
        if grande:
            return denegar(f"`{os.path.basename(ruta)}` pesa más de {LIMITE_READ_BYTES // 1024}KB: "
                           "analízalo con ctx_execute_file. Si lo vas a editar, lee sólo el tramo "
                           f"con `offset` y `limit` (máx. {LIMITE_READ_LINEAS} líneas).")
        return 0
    if tool in {"Bash", "PowerShell", "mcp__Windows-MCP__PowerShell"}:
        cmd = ent.get("command") or ""
        cmd_ctx = lectura_en(cmd)
        if cmd_ctx:
            return denegar(f"`{cmd_ctx}` es lectura: usa ctx_batch_execute (varios comandos + "
                           "`queries`) o ctx_execute. Bash queda para mutar estado o salidas "
                           "cortas y fijas.")
    return 0


def main():
    if os.path.exists(APAGADO):
        return 0
    try:
        ev = json.loads(sys.stdin.buffer.read().decode("utf-8", "replace"))
    except ValueError:
        return 0
    if ev.get("hook_event_name") != "PreToolUse":
        return 0
    return pre_tool_use(ev)


if __name__ == "__main__":
    sys.exit(main())
