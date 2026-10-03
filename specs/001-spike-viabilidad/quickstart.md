# Quickstart: repetir las verificaciones

Cada paso termina escribiendo una fila en `resultados.md` (formato en `contracts/resultados-tabla.md`).
Los scripts son desechables y viven en `spike/`. Orden y dependencias: `plan.md`.

## Antes de empezar
1. Acceso SSH a la VM, llave de OpenRouter (modelo `:free`), y para V5 un número de WhatsApp dedicado no VoIP. Sin alguno, el paso queda `bloqueada` con su causa (FR-027).
2. Solo datos sintéticos. Nada de datos reales de nadie.

## V0 — Forma de la VM
Ejecutar el script de `spike/vm/`; guarda arquitectura, núcleos, memoria, disco, sistema operativo y versiones de Docker, Python y cada pieza. **Pasa** si queda registrado y se contrasta con 2 OCPU / 12 GB.

## V1 — Antigravity
1. Leer los términos y citar el texto del criterio 6 en una ficha (`vault/Fuentes/Antigravity terminos.md`, ya creada).
2. Si el criterio 6 falla: descartado; se anota qué criterios quedan sin probar.
3. Si sigue: criterios 1 y 5 (invocar sin pantalla y sin sesión interactiva), luego 2, 3 y 4 con el banco.

## V2 — Herramientas de lectura
1. Levantar Postgres con el esquema sintético de `data-model.md`.
2. Generar `tools.yaml` desde la descripción del esquema.
3. Correr los ataques de `research.md` R7. **Pasa** si ninguno altera la consulta, el SQL libre no existe y el rol de lectura no puede escribir.

## V3 — Arnés
1. Levantar Hermes en un contenedor sin montajes del host, con `disabled_toolsets` y la MCP de V2.
2. Comprobar `GET /v1/toolsets` y las consultas hostiles (R2).
3. Tres sesiones con `X-Hermes-Session-Id` distintos: un dato dicho en una no debe aparecer en otra.
4. Contención de red desde dentro del contenedor (R10).
5. Doce solicitudes simultáneas para provocar 429 y comprobar la recuperación (R6).
6. Correr el banco en Hermes y en el bucle de referencia: tokens por llamada, razón y latencia separada (R3 a R5). **Pasa** si la razón ≤ 2× y p95 < 15 s.

## V4 — Memoria y cupo
Medir memoria de cada contenedor en reposo, bajo el banco y en ráfaga; calcular el cupo con la fórmula de `data-model.md`; compararlo con 4 e informar el techo y el componente limitante.

## V5 — Canal (necesita el número)
Vincular el número, recibir y responder un mensaje, ejecutar el guion de caídas (R8), distinguir un mensaje humano de uno por API, medir memoria. Solo con mensajes al equipo.

## V6 — Cierre
Llenar la tabla de veredictos, escribir los ADR nuevos (confirman o superan a ADR-001, 002, 005 y 008) y actualizar `STATE.md`.
