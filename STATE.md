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
- **T005 hecha:** llave de OpenRouter en `spike/.env`, válida (comprobada). `API_SERVER_KEY` y claves
  de Postgres siguen vacías.
- **Tope diario de los `:free`: 50 solicitudes por día**, común a todos los modelos [Seguro, medido].
  El spike pide ~150-200. Richard decidió sumar proveedores gratuitos con cuota propia ([[ADR-011]]):
  Gemini, Groq, Mistral, GitHub Models y NVIDIA. Faltan sus cuentas y llaves (T049, Richard).
- MCP de lectura: levantada en la VM (T029); faltan T030–T031 (ataques y rol de solo lectura).
- Falta un número de WhatsApp dedicado de prueba (no VoIP); solo bloquea V5.

## Proximo paso
1. Richard crea las cuentas y llaves de T049; luego `verificar_proveedores.py` fija modelos y cupos.
2. T029 hecha (PR aparte, rama `001-spike-toolbox`); siguen T030–T031, luego Hermes y T011–T015, T017.
Tareas en `specs/001-spike-viabilidad/tasks.md`; mediciones en `resultados.md`.
Rama de trabajo: `docs/adr-010-modelos-free` (PR 8 abierto).
