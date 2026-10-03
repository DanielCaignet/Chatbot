---
tipo: state
proyecto: "chatbot-richard"
actualizado: 2026-10-02
---

# STATE — chatbot-richard

> **Se sobreescribe, nunca se acumula.** Maximo 40 lineas.
> Lo que es historia va a un ADR inmutable en `vault/Decisiones/`.
> Si aparece un segundo archivo de estado o handoff, eso es `STATE-SPRAWL`: corregirlo.

## Donde estamos
F0 cerrada: Spec Kit + vault + grafo montados. Entrevista hecha; constitución v1.0.0 ratificada
([[ADR-000-constitucion]]). Decisiones base en [[ADR-001]]…[[ADR-008]].
Plan maestro aprobado: `docs/PLAN-MAESTRO.md`. Traspaso a Richard: `docs/COMO-CONTINUAR.md`.

## Spec activo
[[SPEC-001]] spike de viabilidad F1 (N0): `specs/001-spike-viabilidad/spec.md`. Spec, plan y
tareas ya unidos a `main` (PR 1). Meta de desarrollo = 4 clientes por VM (FR-022).
Hecho: T001–T004, T006, T007, T008, T009, T016, T027, T028 y T037–T041. **Antigravity descartado por el
criterio 6** [Probable]; ADR en T043. Los scripts de `spike/` solo se probaron contra servidores
simulados (runner, bucle, memoria.sh) y por validación de esquema (generador); lo real se prueba
en la VM (T006, T017, T029, T030).

## Bloqueos
- Sin bloqueos de acceso: la VM provisional ([[ADR-009]]) responde por SSH y el usuario del spike ya
  usa Docker. Forma medida (T006): ARM, 2 núcleos, 10.898 MiB visibles (OCI declara 12 GB), 8,7 GB de
  disco libres, compartida con otro proyecto.
- Falta llave de OpenRouter para el perfil `dev-free` ([[ADR-004]]).
- Falta un número de WhatsApp dedicado de prueba (no VoIP) para Evolution/Baileys. Richard no lo
  tendrá en varios días: solo bloquea la verificación (a); el resto del spike puede avanzar.

## Proximo paso
T005 (llave de OpenRouter) espera el permiso de Richard; no empezar sin él. Luego T029–T031
(Toolbox en la VM) y US1 (Hermes).
Si Richard quiere avanzar sin accesos: T010 (compose y config de Hermes) y T011–T015 (scripts de
prueba) se pueden escribir, no ejecutar.
Tareas en `specs/001-spike-viabilidad/tasks.md`; mediciones en `resultados.md`.
Rama de trabajo: `001-spike-scripts` (PR 3 abierto).
