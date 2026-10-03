#!/usr/bin/env bash
# Mide memoria y CPU por contenedor (T009, SPEC-001). Corre en la VM; requiere docker.
#
# Uso:  memoria.sh <etiqueta> [muestras] [intervalo_s]
#   etiqueta     reposo | banco | rafaga | cualquier palabra sin espacios
#   muestras     cuántas veces medir (por defecto 6)
#   intervalo_s  segundos entre muestras (por defecto 5)
#
# Salida: spike/measure/salida/memoria-<etiqueta>-<fecha>.csv
#   columnas: etiqueta,marca_tiempo,origen,memoria_bytes,limite_bytes,cpu_pct
#   origen = nombre del contenedor, o "host" para la memoria usada de todo el servidor
#   (en "host", limite_bytes es la memoria total y cpu_pct queda vacío).
#
# Nota: la memoria de `docker stats` descuenta la caché de archivos. Sirve para comparar
# componentes entre sí; el margen real contra el límite de la VM lo da la fila "host".
set -euo pipefail

etiqueta="${1:-}"
muestras="${2:-6}"
intervalo="${3:-5}"

if [[ ! "$etiqueta" =~ ^[A-Za-z0-9_-]+$ ]]; then
  echo "uso: memoria.sh <etiqueta> [muestras] [intervalo_s]  (etiqueta: letras, números, - y _)" >&2
  exit 2
fi
if [[ ! "$muestras" =~ ^[0-9]+$ || ! "$intervalo" =~ ^[0-9]+$ || "$muestras" -lt 1 ]]; then
  echo "muestras e intervalo_s deben ser números enteros, muestras >= 1" >&2
  exit 2
fi
command -v docker >/dev/null || { echo "falta docker en el PATH" >&2; exit 1; }

directorio="$(cd "$(dirname "$0")" && pwd)/salida"
mkdir -p "$directorio"
archivo="$directorio/memoria-${etiqueta}-$(date -u +%Y%m%dT%H%M%SZ).csv"
echo "etiqueta,marca_tiempo,origen,memoria_bytes,limite_bytes,cpu_pct" > "$archivo"

convertir='
function bytes(s,   n, u) {
  match(s, /[0-9.]+/); n = substr(s, RSTART, RLENGTH); u = substr(s, RSTART + RLENGTH)
  if (u == "B") return n
  if (u == "KiB") return n * 1024
  if (u == "MiB") return n * 1048576
  if (u == "GiB") return n * 1073741824
  if (u == "kB") return n * 1000
  if (u == "MB") return n * 1000000
  if (u == "GB") return n * 1000000000
  return n
}
BEGIN { FS = "|" }
{
  split($2, m, " / ")
  cpu = $3; sub(/%$/, "", cpu)
  printf "%s,%s,%s,%.0f,%.0f,%s\n", et, ts, $1, bytes(m[1]), bytes(m[2]), cpu
}'

for ((i = 1; i <= muestras; i++)); do
  ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  docker stats --no-stream --format '{{.Name}}|{{.MemUsage}}|{{.CPUPerc}}' \
    | awk -v et="$etiqueta" -v ts="$ts" "$convertir" >> "$archivo"
  free -b | awk -v et="$etiqueta" -v ts="$ts" '/^Mem:/ { printf "%s,%s,host,%s,%s,\n", et, ts, $3, $2 }' >> "$archivo"
  [[ "$i" -lt "$muestras" ]] && sleep "$intervalo"
done

echo "guardado en $archivo"
