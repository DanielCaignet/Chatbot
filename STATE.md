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
Hecho: T001–T003, T007 y T037. **Antigravity descartado por el criterio 6** [Probable]; ADR en T043.

## Bloqueos
- Falta acceso a la Oracle VM (host, usuario, llave SSH) para el spike y para verificar su tamaño
  real (los docs dicen 2 OCPU / 12 GB: [[Oracle Always Free]]).
- Falta llave de OpenRouter para el perfil `dev-free` ([[ADR-004]]).
- Falta un número de WhatsApp dedicado de prueba (no VoIP) para Evolution/Baileys. Richard no lo
  tendrá en varios días: solo bloquea la verificación (a); el resto del spike puede avanzar.

## Proximo paso
Sin la VM se puede escribir ya: T008 `runner.py`, T009 `memoria.sh`, T027–T028 (esquema y
generador de `tools.yaml`) y T016 (bucle de referencia). Con la VM y la llave: T006, T029+ y US1.
Tareas en `specs/001-spike-viabilidad/tasks.md`; mediciones en `resultados.md`.
Rama de trabajo: `001-spike-ejecucion` (PR 2 abierto).
