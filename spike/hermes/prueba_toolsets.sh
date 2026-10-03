#!/usr/bin/env bash
# T011 (SPEC-001, FR-010): ninguna toolset nativa debe quedar activa en el api_server.
# Corre en la VM con Hermes arriba (compose.yml). Lee GET /v1/toolsets y exige que NINGUNA toolset
# aparezca activa con herramientas: no depende de una lista de nombres, así que una toolset nueva en una
# versión posterior de Hermes también hace fallar la prueba.
# Medido el 2026-10-03: ese endpoint lista solo las toolsets nativas (29); las herramientas de la MCP no
# aparecen ahí. Por eso la MCP se comprueba aparte en el registro de Hermes ("registered N tool(s)").
# Esto mira lo que Hermes DECLARA; que de verdad no ejecute nada lo mide T012, que es el veredicto real.
# Control: con `agent.disabled_toolsets` quitado, esta prueba debe fallar (ver resultados.md).
#
# Uso:  bash prueba_toolsets.sh
# Salida: salida/toolsets-<fecha>.json (respuesta cruda) y el veredicto por pantalla.
# Código de salida: 0 = ninguna activa, 1 = hay alguna activa, 2 = no se pudo consultar,
# 3 = no concluyente (el endpoint no devolvió toolsets).
set -euo pipefail

aqui="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$aqui/salida"
archivo="$aqui/salida/toolsets-$(date -u +%Y%m%dT%H%M%SZ).json"

python3 "$aqui/cliente.py" get /v1/toolsets > "$archivo"

python3 - "$archivo" <<'PY'
import json
import re
import subprocess
import sys

r = json.load(open(sys.argv[1], encoding="utf-8"))
# La respuesta real es {"object": "list", "platform": ..., "data": [...]}; la documentación muestra una lista simple.
lista = r["cuerpo"].get("data") if isinstance(r["cuerpo"], dict) else r["cuerpo"]
if r["estado"] != 200 or not isinstance(lista, list):
    print(f"no se pudo consultar /v1/toolsets: estado={r['estado']} error={r['error']}")
    sys.exit(2)

activas = [t for t in lista if t.get("enabled") and t.get("tools")]

print(f"toolsets devueltas: {len(lista)} | activas con herramientas: {len(activas)}")
for t in activas:
    print(f"  FALLA activa: {t.get('name')} -> {', '.join(t['tools'][:8])}")

# La MCP no figura en este endpoint: se busca su registro en el log del contenedor.
try:
    # El registro de la MCP está en los archivos del volumen, no en la salida del contenedor.
    log = subprocess.run(["docker", "exec", "hermes-spike", "sh", "-c",
                          "cat /opt/data/logs/*.log /opt/data/logs/gateways/*/current 2>/dev/null"],
                         capture_output=True, text=True, timeout=30)
    registro = re.findall(r"MCP server '([^']+)'.*registered (\d+) tool", log.stdout)[-1:]
    print("MCP registrada (según el registro de Hermes):", registro or "no encontrada")
except (OSError, subprocess.SubprocessError):
    print("MCP: no se pudo leer el registro (sin docker)")

if activas:
    print("veredicto: falla")
    sys.exit(1)
if not lista:
    print("veredicto: no concluyente (el endpoint no devolvió ninguna toolset)")
    sys.exit(3)
print("veredicto: pasa")
PY
