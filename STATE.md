---
tipo: state
proyecto: "chatbot-richard"
actualizado: 2026-10-01
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
ninguno. Siguiente: SPEC-001, spike de viabilidad en la VM (F1 del plan).

## Bloqueos
- Falta acceso a la Oracle VM (host, usuario, llave SSH) para el spike y para verificar su tamaño
  real (los docs dicen 2 OCPU / 12 GB: [[Oracle Always Free]]).
- Falta llave de OpenRouter para el perfil `dev-free` ([[ADR-004]]).
- Falta un número de WhatsApp dedicado de prueba (no VoIP) para Evolution/Baileys.

## Proximo paso
`speckit-specify` del spike F1: (a) Evolution+Baileys, (b) Hermes api_server solo-MCP,
(c) MCP Toolbox, (d) RAM por stack, (e) prueba de descarte de Antigravity ([[ADR-008]]).
