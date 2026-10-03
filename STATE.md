---
tipo: state
proyecto: "chatbot-richard"
actualizado: 2026-10-03
---

# STATE — chatbot-richard

> **Se sobreescribe, nunca se acumula.** Maximo 40 lineas.
> Lo que es historia va a un ADR inmutable en `vault/Decisiones/`.
> Si aparece un segundo archivo de estado o handoff, eso es `STATE-SPRAWL`: corregirlo.

## Donde estamos
F0 cerrada: Spec Kit + vault + grafo montados. Constitución v1.0.0 ratificada
([[ADR-000-constitucion]]). Decisiones base en [[ADR-001]]…[[ADR-010]].
Plan maestro aprobado: `docs/PLAN-MAESTRO.md`. Traspaso a Richard: `docs/COMO-CONTINUAR.md`.

## Spec activo
[[SPEC-001]] spike de viabilidad F1 (N0): `specs/001-spike-viabilidad/spec.md`. Meta de desarrollo =
4 clientes por VM (FR-022). **Antigravity descartado por el criterio 6** [Probable]; ADR en T043.
Unido a `main` (PR 7, auditado con `/thermos`): T010 (compose y config de Hermes, validados en la
VM) y escritos sin correr T011–T015 (probados solo contra un servidor simulado). Mejoras: T048.
Modelo ([[ADR-010]]): `nvidia/nemotron-3-super-120b-a12b:free`, respaldos Qwen y Gemma.

## Bloqueos
- VM provisional ([[ADR-009]]): SSH, Docker y Python listos; ARM, 2 núcleos, 10,9 GiB, 8,4 GB de
  disco libres, compartida. Hermes pesa ~1 GB comprimido: medir el disco antes de bajarlo.
- **T005 (Richard):** la cuenta de OpenRouter existe; falta pegar la llave en `spike/.env`. Sin ella
  no corren T011–T015 contra el modelo ni T017. `API_SERVER_KEY` y claves de Postgres siguen vacías.
- **Tope diario de los `:free`:** común a todos los modelos; de memoria ~50 por día sin créditos y
  T017 solo no cabe [Probable]. Falta leer el valor real (`GET /api/v1/key`) y decidir: repartir en
  días, comprar el mínimo de créditos o sumar otro proveedor ([[ADR-010]]).
- Falta la MCP de lectura (T029–T031); T012 la usa como control.
- Falta un número de WhatsApp dedicado de prueba (no VoIP); solo bloquea V5.

## Proximo paso
1. Richard pega la llave y decide qué hacer con el tope diario.
2. T029–T031 (Toolbox en la VM); luego levantar Hermes y correr T011–T015 y T017.
Tareas en `specs/001-spike-viabilidad/tasks.md`; mediciones en `resultados.md`.
Rama de trabajo: `docs/adr-010-modelos-free` (PR por abrir).
