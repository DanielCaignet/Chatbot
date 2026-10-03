---
tipo: spec
id: SPEC-001
titulo: "Spike de viabilidad F1 (gate)"
status: vigente
spec_path: "specs/001-spike-viabilidad/"
supersedes: []
creado: 2026-10-02
actualizado: 2026-10-02
---

# SPEC-001 — Spike de viabilidad F1 (gate)

> Esta ficha **no repite** el spec. Es el nodo que lo hace encontrable en el grafo.
> El contenido normativo vive en `spec_path`. Aca solo van punteros y relaciones.
> El **nivel de madurez** (N0-N3) y su limite viven en la fila de [[00 - Indice de Specs]],
> dueño unico. No se repiten aca.

**Spec:** [`specs/001-spike-viabilidad/spec.md`](specs/001-spike-viabilidad/spec.md)
**Plan:** [`specs/001-spike-viabilidad/plan.md`](specs/001-spike-viabilidad/plan.md)
**Tareas:** [`specs/001-spike-viabilidad/tasks.md`](specs/001-spike-viabilidad/tasks.md)

## En una linea
Decide con evidencia medida en la VM si canal, arnés y herramientas de lectura del plan se conservan o pasan a su alternativa, cuántos clientes caben por VM y si Antigravity se descarta.

## Conceptos que toca
[[Canal]] · [[Capa SAS]] · [[Takeover]] · [[Tenant]] · [[Catalogo semantico]]

## Decisiones que lo gobiernan
[[ADR-001]] · [[ADR-002]] · [[ADR-003]] · [[ADR-004]] · [[ADR-005]] · [[ADR-008]]

## Fuentes
[[Evolution API]] · [[Hermes Agent api_server]] · [[MCP Toolbox for Databases]] · [[Oracle Always Free]] · [[OpenRouter limites]]

## Depende de / Bloquea
- Depende de: acceso a la Oracle VM, llave de OpenRouter y número de WhatsApp de prueba ([[STATE]])
- Bloquea: F2 SAS (su forma depende del veredicto de herramientas) y F3 MVP tienda
