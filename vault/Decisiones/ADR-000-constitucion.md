---
tipo: adr
id: ADR-000-constitucion
titulo: "Constitución v1.0.0"
status: accepted
supersedes: []
fecha: 2026-10-01
---

# ADR-000-constitucion — Constitución v1.0.0

> Inmutable. Una enmienda de la constitución exige un ADR nuevo.

## Contexto
Proyecto recién montado. El usuario aprobó seis invariantes y la definición de terminado en la entrevista de la Fase 1.

## Decision
Ratificar `.specify/memory/constitution.md` v1.0.0 con seis principios: cifras solo desde la [[Capa SAS]] (contra el [[Ledger del turno]]), aislamiento por [[Tenant]], solo responder ([[ADR-006]]), datos personales fuera de modelos gratuitos ([[ADR-004]]), reglas de implementación y definición de terminado (tests + evals + E2E).

## Alternativas descartadas
- Constitución con roadmap o estado — descartada: el estado vive en STATE.md.

## Consecuencias
- Todo plan pasa por el Constitution Check contra estos seis principios.
- Fuera de v1: cobro, campañas salientes y panel web del admin.

## Relacionado
[[Capa SAS]] · [[Tenant]] · [[ADR-005]]
