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
([[ADR-000-constitucion]]). Decisiones base en [[ADR-001]]…[[ADR-009]].
Plan maestro aprobado: `docs/PLAN-MAESTRO.md`. Traspaso a Richard: `docs/COMO-CONTINUAR.md`.

## Spec activo
[[SPEC-001]] spike de viabilidad F1 (N0): `specs/001-spike-viabilidad/spec.md`. Meta de desarrollo =
4 clientes por VM (FR-022).
Hecho y unido a `main`: T001–T004, T006–T009, T016, T027, T028, T037–T041. **Antigravity descartado
por el criterio 6** [Probable]; ADR en T043.
Hecho en la rama `001-spike-hermes`: T010 (compose y config de Hermes, validados con
`docker compose config` en la VM) y escritos sin correr T011, T012, T013, T014, T015 (probados solo
contra un servidor simulado). Imagen fijada `nousresearch/hermes-agent:v2026.9.24`, arm64 confirmado.

## Bloqueos
- VM provisional ([[ADR-009]]): responde por SSH, Docker y Python 3.9 listos. Forma: ARM, 2 núcleos,
  10.898 MiB visibles, 8,7 GB de disco libres, compartida con otro proyecto. La imagen de Hermes pesa
  ~1 GB comprimida: medir el disco antes de bajarla.
- **T005 en curso (Richard):** falta la llave de OpenRouter en `spike/.env` y el modelo `:free`.
  Sin ella no se pueden correr T011–T015 contra el modelo ni T017.
- Falta la MCP de lectura (T029–T031, Toolbox): T012 la usa como control y Hermes la declara en
  `config.yaml` (dirección `http://toolbox:5000/mcp`, por confirmar en T029).
- Falta un número de WhatsApp dedicado de prueba (no VoIP) para Evolution/Baileys; solo bloquea V5.

## Proximo paso
1. Richard termina T005 y avisa el identificador del modelo (se anota en `resultados.md` §1).
2. T029–T031 (Toolbox en la VM). Luego levantar Hermes y correr T011–T015 y T017.
Tareas en `specs/001-spike-viabilidad/tasks.md`; mediciones en `resultados.md`.
Rama de trabajo: `001-spike-hermes`.
