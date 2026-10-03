#!/usr/bin/env bash
# T011 (SPEC-001, FR-010): ninguna toolset nativa debe quedar activa en el api_server.
# Corre en la VM con Hermes arriba (compose.yml). Lee GET /v1/toolsets y lo compara con la lista
# `agent.disabled_toolsets` de config.yaml. También cubre el bug abierto de multiplex_profiles:
# si el api_server reactivara toolsets en silencio, aparecerían aquí como activas.
#
# Uso:  prueba_toolsets.sh
# Salida: salida/toolsets-<fecha>.json (respuesta cruda) y el veredicto por pantalla.
# Código de salida: 0 = ninguna nativa activa, 1 = alguna activa, 2 = no se pudo consultar.
set -euo pipefail

aqui="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$aqui/salida"
archivo="$aqui/salida/toolsets-$(date -u +%Y%m%dT%H%M%SZ).json"

python3 "$aqui/cliente.py" get /v1/toolsets > "$archivo"

python3 - "$archivo" "$aqui/config.yaml" <<'PY'
import json
import re
import sys

archivo, config = sys.argv[1], sys.argv[2]
r = json.load(open(archivo, encoding="utf-8"))
if r["estado"] != 200 or not isinstance(r["cuerpo"], list):
    print(f"no se pudo consultar /v1/toolsets: estado={r['estado']} error={r['error']}")
    sys.exit(2)

apagadas, dentro = [], False
for linea in open(config, encoding="utf-8"):
    if re.match(r"\s+disabled_toolsets:", linea):
        dentro = True
    elif dentro:
        m = re.match(r"\s+- (\S+)", linea)
        if m:
            apagadas.append(m.group(1))
        elif linea.strip() and not linea.lstrip().startswith("#"):
            break

activas = [t for t in r["cuerpo"] if t.get("enabled") and t.get("tools")]
nativas = [t for t in activas if t.get("name") in apagadas]
otras = [t for t in activas if t.get("name") not in apagadas]

print(f"toolsets devueltas: {len(r['cuerpo'])} | apagadas en config.yaml: {len(apagadas)}")
print(f"activas con herramientas: {len(activas)}")
for t in otras:
    print(f"  activa (no está en la lista apagada, comprobar que viene de la MCP): "
          f"{t.get('name')} -> {', '.join(t['tools'][:8])}")
for t in nativas:
    print(f"  FALLA nativa activa: {t['name']} -> {', '.join(t['tools'][:8])}")
print("veredicto:", "falla" if nativas else "pasa")
sys.exit(1 if nativas else 0)
PY
