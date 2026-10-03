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
[[SPEC-001]] spike de viabilidad F1 (N0, borrador): `specs/001-spike-viabilidad/spec.md`.
Sin marcadores abiertos: meta de desarrollo = 4 clientes por VM (FR-022).

## Bloqueos
- Falta acceso a la Oracle VM (host, usuario, llave SSH) para el spike y para verificar su tamaño
  real (los docs dicen 2 OCPU / 12 GB: [[Oracle Always Free]]).
- Falta llave de OpenRouter para el perfil `dev-free` ([[ADR-004]]).
- Falta un número de WhatsApp dedicado de prueba (no VoIP) para Evolution/Baileys. Richard no lo
  tendrá en varios días: solo bloquea la verificación (a); el resto del spike puede avanzar.

## Proximo paso
Plan de SPEC-001 listo (`specs/001-spike-viabilidad/plan.md`). Siguiente: `speckit-tasks`.
Orden del spike: V0 VM → V1 Antigravity (leer términos primero; la cláusula 6 apunta a descarte
[Probable]) → V2 herramientas → V3 Hermes → V4 cupo → V5 canal (espera el número) → V6 veredictos.
