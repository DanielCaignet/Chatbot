#!/usr/bin/env bash
# T011 (SPEC-001, FR-010): ninguna toolset nativa debe quedar activa en el api_server.
# Corre en la VM con Hermes arriba (compose.yml). Lee GET /v1/toolsets y exige que toda toolset
# activa con herramientas sea de la MCP (nombre que empieza por `mcp`). Cualquier otra, nativa o
# nueva en una versión posterior de Hermes, hace fallar la prueba: no depende de una lista de nombres.
# Esto mira lo que Hermes DECLARA; que de verdad no ejecute nada lo mide T012, que es el veredicto real.
# [Adivinando] que `enabled` ya descuente `agent.disabled_toolsets`: si no, un "falla" aquí puede ser
# falso y se contrasta con T012.
#
# Uso:  bash prueba_toolsets.sh
# Salida: salida/toolsets-<fecha>.json (respuesta cruda) y el veredicto por pantalla.
# Código de salida: 0 = solo la MCP activa, 1 = hay otra activa, 2 = no se pudo consultar,
# 3 = no concluyente (no hay ninguna activa).
set -euo pipefail

aqui="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$aqui/salida"
archivo="$aqui/salida/toolsets-$(date -u +%Y%m%dT%H%M%SZ).json"

python3 "$aqui/cliente.py" get /v1/toolsets > "$archivo"

python3 - "$archivo" <<'PY'
import json
import sys

r = json.load(open(sys.argv[1], encoding="utf-8"))
if r["estado"] != 200 or not isinstance(r["cuerpo"], list):
    print(f"no se pudo consultar /v1/toolsets: estado={r['estado']} error={r['error']}")
    sys.exit(2)

activas = [t for t in r["cuerpo"] if t.get("enabled") and t.get("tools")]
no_mcp = [t for t in activas if not str(t.get("name", "")).startswith("mcp")]

print(f"toolsets devueltas: {len(r['cuerpo'])} | activas con herramientas: {len(activas)}")
for t in activas:
    marca = "FALLA no es de la MCP" if t in no_mcp else "ok (MCP)"
    print(f"  {marca}: {t.get('name')} -> {', '.join(t['tools'][:8])}")
if no_mcp:
    print("veredicto: falla")
    sys.exit(1)
if not activas:
    print("veredicto: no concluyente (ninguna toolset activa: la MCP no está conectada, revisar T029)")
    sys.exit(3)
print("veredicto: pasa")
PY
