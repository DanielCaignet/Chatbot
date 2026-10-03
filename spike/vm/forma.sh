#!/usr/bin/env bash
# Forma de la VM (T006, SPEC-001, FR-001 y FR-004). Solo lectura: no instala ni cambia nada.
# No imprime IP, nombre del equipo, usuarios ni identificadores: el repositorio es público.
#
# Uso, sin copiar nada a la VM:   ssh <host> 'bash -s' < spike/vm/forma.sh
# Salida: tabla Markdown para pegar en specs/001-spike-viabilidad/resultados.md §1.
set -u

fila() { printf '| %s | %s |\n' "$1" "$2"; }
existe() { command -v "$1" >/dev/null 2>&1; }

arquitectura="$(uname -m 2>/dev/null || echo desconocida)"
nucleos="$(nproc 2>/dev/null || echo desconocido)"

if existe free; then
  mem_total="$(free -m | awk '/^Mem:/ {print $2}')"
  mem_disponible="$(free -m | awk '/^Mem:/ {print $7}')"
  mem_usada="$(free -m | awk '/^Mem:/ {print $3}')"
else
  mem_total=desconocida; mem_disponible=desconocida; mem_usada=desconocida
fi

disco="$(df -h / 2>/dev/null | awk 'NR==2 {print $2 " total, " $4 " libres, " $5 " usado"}')"
sistema="$( . /etc/os-release 2>/dev/null && echo "${PRETTY_NAME:-desconocido}" )"
kernel="$(uname -r 2>/dev/null || echo desconocido)"

# Metadatos de OCI: solo forma, núcleos y memoria nominal (el resto se descarta).
oci=""
if existe curl && existe python3; then
  json="$(curl -s --max-time 3 -H 'Authorization: Bearer Oracle' http://169.254.169.254/opc/v2/instance/ 2>/dev/null)"
  if [ -n "$json" ]; then
    oci="$(printf '%s' "$json" | python3 -c '
import json, sys
d = json.load(sys.stdin)
c = d.get("shapeConfig", {})
print("%s, %s OCPU, %s GB" % (d.get("shape", "?"), c.get("ocpus", "?"), c.get("memoryInGBs", "?")))
' 2>/dev/null)"
  fi
fi
[ -n "$oci" ] || oci="no disponible"

docker_v="no instalado"; compose_v="no instalado"; contenedores="n/d"
if existe docker; then
  docker_v="$(docker --version 2>/dev/null | sed 's/^Docker version //; s/,.*//')"
  compose_v="$(docker compose version --short 2>/dev/null || echo 'no instalado')"
  contenedores="$(docker ps -q 2>/dev/null | wc -l | tr -d ' ')"
fi
python_v="$(python3 --version 2>/dev/null | sed 's/^Python //' || true)"
[ -n "$python_v" ] || python_v="no instalado"

echo '| Dato | Valor |'
echo '|---|---|'
fila "Fecha de medición (UTC)" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
fila "Forma según OCI (metadatos)" "$oci"
fila "Arquitectura" "$arquitectura"
fila "Núcleos visibles" "$nucleos"
fila "Memoria total visible (MiB)" "$mem_total"
fila "Memoria usada al medir (MiB)" "$mem_usada"
fila "Memoria disponible al medir (MiB)" "$mem_disponible"
fila "Disco raíz" "$disco"
fila "Sistema operativo" "$sistema"
fila "Kernel" "$kernel"
fila "Docker" "$docker_v"
fila "Docker Compose" "$compose_v"
fila "Python del sistema" "$python_v"
fila "Contenedores en ejecución (cualquier proyecto)" "$contenedores"
