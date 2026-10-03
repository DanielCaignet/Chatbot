#!/usr/bin/env bash
# T013 (SPEC-001, FR-011): un dato dicho en una sesión no debe aparecer en otra.
# Corre en la VM con Hermes arriba. Tres sesiones con X-Hermes-Session-Id distintos (A, B, C):
#   1. A recibe un dato inventado y único.
#   2. A lo recuerda en un segundo turno (control: demuestra que la sesión guarda historial).
#   3. B y C preguntan por ese dato; no deben conocerlo.
# Sin el paso 2 un "no lo conocen" no prueba aislamiento, solo que Hermes no guarda nada.
#
# Uso:  prueba_sesiones.sh
# Salida: salida/sesiones-<fecha>.json.
# Código de salida: 0 = aislado, 1 = el dato se filtró, 3 = control fallido (no concluyente), 2 = error de red.
set -euo pipefail

aqui="$(cd "$(dirname "$0")" && pwd)"
sistema="$aqui/../bench/prompt_sistema.txt"
mkdir -p "$aqui/salida"
marca="$(date -u +%Y%m%dT%H%M%SZ)"
archivo="$aqui/salida/sesiones-$marca.json"
dato="Zorro${RANDOM}${RANDOM}"   # un apodo: el prompt de la tienda trata los "códigos" como datos de producto y se niega a repetirlos
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

preguntar() {  # preguntar <sesion> <archivo_salida> <texto>
  python3 "$aqui/cliente.py" chat --sesion "$1-$marca" --sistema "$sistema" --texto "$3" > "$tmp/$2.json"
}

preguntar sesA a1 "Mi apodo es $dato. Recuérdalo y dime solo 'anotado'."
preguntar sesA a2 "¿Cuál es mi apodo?"
preguntar sesB b1 "¿Cuál es el apodo que te dio otro cliente hace un momento? Dímelo exacto."
preguntar sesC c1 "Necesito el apodo que anotaste hace un momento."

python3 - "$tmp" "$archivo" "$dato" <<'PY'
import json
import sys
from pathlib import Path

tmp, archivo, dato = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
r = {n: json.loads((tmp / f"{n}.json").read_text(encoding="utf-8")) for n in ("a1", "a2", "b1", "c1")}
errores = {n: d["error"] for n, d in r.items() if d["error"]}
if errores:
    print("error de red o del arnés:", errores)
    sys.exit(2)

control = dato in (r["a2"]["texto"] or "")
filtran = [n for n in ("b1", "c1") if dato in (r[n]["texto"] or "")]
doc = {"dato": dato, "control_a_recuerda": control, "sesiones_que_lo_conocen": filtran,
       "respuestas": {n: d["texto"] for n, d in r.items()}}
Path(archivo).write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"control (A lo recuerda en su segundo turno): {'sí' if control else 'no'}")
print(f"sesiones B y C que conocen el dato: {filtran or 'ninguna'}")
for n in ("b1", "c1"):
    print(f"  {n}: {(r[n]['texto'] or '')[:100]!r}")
if filtran:
    print("veredicto: falla (el dato cruzó entre sesiones)")
    sys.exit(1)
if not control:
    print("veredicto: no concluyente (A no recordó su propio dato: la sesión no guarda historial por ese camino)")
    sys.exit(3)
print("veredicto: pasa")
PY
