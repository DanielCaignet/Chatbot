#!/usr/bin/env bash
# T014 (SPEC-001, FR-012, R10): comprobar DESDE DENTRO del contenedor de Hermes que
#   1) no hay montajes del host,
#   2) una conexión directa a Internet falla,
#   3) un destino no permitido falla también por el proxy,
#   4) el proveedor de modelos sí responde por el proxy (control: sin él, los fallos anteriores no prueban nada).
# Corre en la VM con la contención levantada (compose.red.yml).
#
# Uso:  bash red/prueba_contencion.sh
# Salida: ../salida/contencion-<fecha>.txt.
# Código de salida: 0 pasa, 1 falla, 2 no se pudo ejecutar, 3 no concluyente.
set -euo pipefail

aqui="$(cd "$(dirname "$0")" && pwd)"
contenedor="hermes-spike"   # nombre fijo en compose.yml
mkdir -p "$aqui/../salida"
archivo="$aqui/../salida/contencion-$(date -u +%Y%m%dT%H%M%SZ).txt"
command -v docker >/dev/null || { echo "falta docker en el PATH" >&2; exit 2; }
docker inspect "$contenedor" >/dev/null 2>&1 || { echo "el contenedor $contenedor no existe o no está levantado" >&2; exit 2; }

# -i es imprescindible: sin él docker exec no reenvía el script por stdin y python no ejecuta nada.
dentro() { docker exec -i "$contenedor" sh -c 'py=$(command -v python3 || command -v python) || { echo "error:sin-python"; exit 0; }; "$py" - "$@"' _ "$@"; }

# Cada comprobación imprime una sola palabra: ok | bloqueado | error:<detalle>
probar() {  # probar <descripcion> <url> <usar_proxy 0|1>
  dentro "$2" "$3" <<'PY' 2>&1 | tail -1
import sys, urllib.request
url, usar = sys.argv[1], sys.argv[2] == "1"
try:
    # Sin proxy: ProxyHandler({}) ignora las variables HTTPS_PROXY del contenedor.
    abrir = urllib.request.build_opener(urllib.request.ProxyHandler() if usar else urllib.request.ProxyHandler({}))
    r = abrir.open(url, timeout=10)
    print("ok" if r.status < 400 else f"error:HTTP {r.status}")
except Exception as e:
    texto = str(e)
    # Por el proxy, solo el 403 de Squid cuenta como bloqueo; un tiempo agotado puede ser un proxy lento.
    # Sin proxy no hay ruta: red inalcanzable, sin resolución de nombres o tiempo agotado.
    if usar:
        print("bloqueado" if "403" in texto else f"error:{type(e).__name__}")
    else:
        print("bloqueado" if any(s in texto.lower() for s in ("unreachable", "name or service", "timed out", "refused", "temporary failure")) else f"error:{type(e).__name__}")
PY
}

montajes="$(docker inspect -f '{{range .Mounts}}{{.Type}}:{{.Destination}} {{end}}' "$contenedor")"
bind="$(grep -o 'bind:[^ ]*' <<<"$montajes" || true)"
directo="$(probar directo https://1.1.1.1 0)"
otro="$(probar otro-destino-por-proxy https://example.com 1)"
proveedor="$(probar proveedor-por-proxy https://openrouter.ai/api/v1/models 1)"

{
  echo "montajes de Hermes: ${montajes:-ninguno}"
  echo "montajes del host (bind): ${bind:-ninguno}"
  echo "conexión directa a https://1.1.1.1: $directo"
  echo "https://example.com por el proxy: $otro"
  echo "https://openrouter.ai por el proxy (control): $proveedor"
} | tee "$archivo"

if [[ "$proveedor" != ok ]]; then
  echo "veredicto: no concluyente (el proveedor no responde por el proxy: ¿Hermes no usa HTTPS_PROXY, lista blanca mal escrita o sin Internet?)" | tee -a "$archivo"
  exit 3
fi
if [[ -n "$bind" || "$directo" != bloqueado || "$otro" != bloqueado ]]; then
  echo "veredicto: falla" | tee -a "$archivo"
  exit 1
fi
echo "veredicto: pasa" | tee -a "$archivo"
