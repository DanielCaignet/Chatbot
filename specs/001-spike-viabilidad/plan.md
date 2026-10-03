# Implementation Plan: Spike de viabilidad F1 (gate)

**Branch**: `001-spike-viabilidad` | **Date**: 2026-10-02 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-spike-viabilidad/spec.md`

## Summary

Un spike no entrega producto: entrega **veredictos con evidencia**. El plan monta una VM de prueba
con tres piezas aisladas (herramientas de lectura, arnés Hermes, canal Evolution), un banco
sintético de ~20 consultas y un bucle de referencia mínimo, y mide: apagado real de herramientas,
aislamiento de sesiones, comportamiento ante 429, tokens por llamada (razón vs bucle propio),
latencia separada modelo/arnés, memoria por componente y cupo de clientes. Antigravity se prueba
al principio por su criterio más barato: leer sus términos. Los scripts son **desechables**; el
único resultado duradero es `resultados.md` y los ADR que confirman o superan a los existentes.

## Technical Context

**Language/Version**: scripts de shell y Python 3 (versión de la VM, a registrar en V0); sin código de producto

**Primary Dependencies**: Docker + Compose; Evolution API; Hermes Agent (`api_server`); MCP Toolbox for Databases; Postgres; OpenRouter (modelos `:free`). Cada versión o digest exacto se fija y registra en `resultados.md` (FR-004)

**Storage**: Postgres con esquema sintético de tienda; mediciones en archivos Markdown

**Testing**: verificaciones deterministas con script (lista de herramientas, inyección SQL, escritura rechazada, aislamiento) más mediciones repetidas con tabla; no hay suite de tests de producto

**Target Platform**: Oracle VM Always Free Ampere A1 (arm64). Sistema operativo y forma real: se descubren en V0 (los docs dicen 2 OCPU / 12 GB [EXT:Oracle Always Free])

**Project Type**: spike (scripts desechables + documentación)

**Performance Goals**: p95 < 15 s sobre el total (FR-015); tokens por llamada del arnés ≤ 2× el bucle de referencia (FR-014); reconexión ≤ 120 s [Adivinando] (FR-007)

**Constraints**: 12 GB de RAM compartidos; solo datos sintéticos; modelos `:free` con topes por cuenta [EXT:OpenRouter limites]; el bot nunca escribe primero (Constitución III)

**Scale/Scope**: meta de desarrollo 4 clientes por VM y medición del techo (FR-022)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Estado | Cómo se cumple |
|---|---|---|
| I. Cifras solo desde el SAS | Pasa | El spike no envía cifras a clientes; las herramientas de prueba usan SQL fijo parametrizado y el banco incluye casos que intentan sacar cifras sin herramienta |
| II. Aislamiento por cliente | Pasa | Un compose por cliente simulado; sin montajes del host; salida de red con lista blanca; ningún secreto en el contexto del modelo (llaves solo en variables del contenedor) |
| III. Solo responder | Pasa | Solo se contestan mensajes del propio equipo al número de prueba; no hay envíos iniciados por el sistema |
| IV. Datos personales fuera de modelos gratuitos | Pasa | Todo el banco es inventado; ningún dato real |
| V. Reglas de implementación | Pasa | Scripts mínimos y descartables; sin abstracciones de un solo uso; supuestos declarados |
| VI. Definición de terminado | **Atención** | Exige prueba E2E con número de prueba: la verificación (a) queda `bloqueada` hasta comprar la línea, y el spike no se cierra sin ella (FR-027). Es una dependencia, no una violación |

Re-chequeo tras el diseño (Fase 1): sin cambios; el diseño no introduce nada que toque I–V.

## Orden de ejecución

Lo barato y sin número de WhatsApp va primero. Cada paso cierra con su veredicto antes de seguir.

| Paso | Qué | Necesita | Cubre |
|---|---|---|---|
| V0 | Forma real de la VM y versiones fijadas | Acceso SSH | FR-001, FR-004, FR-021 |
| V1 | Antigravity: criterio 6 (leer términos) y, si sigue, criterios 1 y 5 en seco | Nada / cuenta de Richard | FR-023 |
| V2 | Herramientas de lectura (MCP Toolbox) sobre esquema sintético | V0 | FR-017 a FR-019 |
| V3 | Arnés Hermes: herramientas apagadas, aislamiento, contención, 429, tokens, latencia | V0, V2, llave OpenRouter | FR-010 a FR-016, FR-020 |
| V4 | Memoria por componente y cupo (meta 4, techo) | V2, V3 | FR-021, FR-022 |
| V5 | Canal Evolution/Baileys: conexión, reconexión, `fromMe`, memoria | V0, número de prueba | FR-006 a FR-009 |
| V6 | Veredictos, ADR nuevos y cierre | V1–V5 | FR-025 a FR-027 |

Si V1 falla en el criterio 6, Antigravity queda descartado sin más pruebas (ADR-008 permite parar
al primer fallo); se anota qué criterios quedaron sin probar.

## Project Structure

### Documentation (this feature)

```text
specs/001-spike-viabilidad/
├── plan.md              # Este archivo
├── research.md          # Decisiones y alternativas (Fase 0)
├── data-model.md        # Entidades del spike (Fase 1)
├── quickstart.md        # Cómo repetir cada verificación (Fase 1)
├── contracts/
│   ├── resultados-tabla.md      # Formato de la tabla de veredictos
│   └── banco-consultas.md       # Formato del banco sintético
├── checklists/requirements.md
├── resultados.md        # Dueño único de las mediciones (se crea al ejecutar)
└── tasks.md             # Lo crea /speckit-tasks
```

### Source Code (repository root)

Todo bajo `spike/`, **descartable por declaración**; nada de aquí pasa a F2 sin un spec propio.

```text
spike/
├── vm/            # script de forma de la VM y versiones fijadas
├── toolbox/       # esquema sintético, tools.yaml generado, rol de solo lectura, ataques
├── hermes/        # compose, config.yaml (disabled_toolsets), pruebas hostiles
├── baseline/      # bucle de referencia mínimo (solo para medir tokens)
├── evolution/     # compose de Evolution y guion de reconexión
├── bench/         # banco de ~20 consultas y runner que registra usage y tiempos
└── measure/       # captura de memoria/CPU por componente y cálculo de cupo
```

**Structure Decision**: documentación en `specs/` (norma del proyecto), experimentos en `spike/`.
Las mediciones viven solo en `resultados.md` (Ley de Dueño Único); los porqués, en ADR.

## Cobertura de requisitos

| Requisito | Dónde se resuelve |
|---|---|
| FR-001, FR-004, FR-005 | V0; `quickstart.md` fija el formato de procedimiento |
| FR-002, FR-003 | Restricciones transversales; revisión al cerrar V6 |
| FR-006 a FR-009 | V5, `research.md` R8 |
| FR-010 a FR-016 | V3, `research.md` R1 a R6 |
| FR-017 a FR-020 | V2, `research.md` R7 |
| FR-021, FR-022 | V4, `research.md` R9 |
| FR-023, FR-024 | V1, `research.md` R11 |
| FR-025 a FR-027 | V6, `contracts/resultados-tabla.md` |

## Complexity Tracking

Sin violaciones que justificar.
