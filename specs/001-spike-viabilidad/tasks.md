---
description: "Lista de tareas del spike de viabilidad F1 (SPEC-001)"
---

# Tasks: Spike de viabilidad F1 (gate)

**Input**: `specs/001-spike-viabilidad/` — [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md), [data-model.md](data-model.md), [quickstart.md](quickstart.md), [contracts/](contracts/)

**Prerequisites**: plan.md y spec.md (listos). Insumos externos: acceso SSH a la VM, llave de OpenRouter y número de WhatsApp dedicado no VoIP.

**Tests**: no hay suite de tests de producto. **Las verificaciones del spike son las pruebas**: cada tarea de prueba termina escribiendo su resultado crudo y su estado (`pasa` / `falla` / `bloqueada` con causa) en `specs/001-spike-viabilidad/resultados.md`.

**Organization**: agrupadas por historia de usuario del spec (US1–US5). El orden **de ejecución recomendado** difiere del orden de prioridad: está en "Dependencies & Execution Order".

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede hacer en paralelo (archivos distintos, sin depender de una tarea incompleta)
- **[Story]**: historia a la que pertenece (US1 arnés, US2 canal, US3 herramientas, US4 cupo, US5 Antigravity)
- **(Richard)**: tarea que solo puede hacer Richard (accesos, línea de WhatsApp, cuentas)

## Path Conventions

- Documentación: `specs/001-spike-viabilidad/`
- Experimentos desechables: `spike/` (declarado descartable; nada pasa a F2 sin un spec propio)
- Único dueño de las mediciones: `specs/001-spike-viabilidad/resultados.md`
- Las llaves y tokens van **solo** en `spike/.env` (ignorado por Git); nunca en un archivo versionado

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: estructura del spike y del archivo de resultados

- [x] T001 Crear la estructura `spike/{vm,toolbox,hermes,baseline,evolution,bench,measure}/` y `spike/README.md` con una línea que declare que todo es descartable
- [x] T002 [P] Crear `specs/001-spike-viabilidad/resultados.md` con las cinco secciones de `contracts/resultados-tabla.md` (Entorno, Verificaciones, Antigravity, Cupo, Veredictos) y todas las filas en `pendiente`
- [x] T003 [P] (el `.gitignore` ya excluía `.env` en cualquier carpeta; verificado con `git check-ignore`) Crear `spike/.env.example` con los nombres de variables sin valores (`OPENROUTER_API_KEY`, `API_SERVER_KEY`, etc.)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: forma de la VM, insumos y herramientas de medición compartidas

**⚠️ CRITICAL**: ninguna historia puede dar un veredicto sin esta fase. Si falta un insumo, la tarea correspondiente queda `bloqueada` con su causa (FR-027); no se omite.

- [x] T004 (Richard) Entregar acceso SSH a la Oracle VM (host, usuario, llave) y registrar en `resultados.md` §1 solo "acceso: sí/no" (nunca la llave); sin acceso, marcar V0 `bloqueada`
- [ ] T005 [P] (Richard) Crear la llave de OpenRouter, guardarla en `spike/.env` y fijar el identificador exacto del modelo `:free` a usar; registrar solo el identificador en `resultados.md` §1
- [ ] T006 V0: escribir `spike/vm/forma.sh` que registre arquitectura, núcleos, memoria, disco, sistema operativo y versiones de Docker y Python; ejecutarlo en la VM y pegar la salida en `resultados.md` §1; contrastar con 2 OCPU / 12 GB [EXT:Oracle Always Free] (FR-001, FR-004)
- [x] T007 [P] Crear `spike/bench/banco.json` con ~20 consultas sintéticas de tienda en seis grupos (`precio`, `stock`, `inexistente`, `ambigua`, `fuera_de_tema`, `hostil`), mínimo 2 por grupo, con campo `version`, según `contracts/banco-consultas.md` (FR-002)
- [x] T008 Escribir `spike/bench/runner.py` que ejecute el banco contra un endpoint compatible con OpenAI y guarde por consulta: tiempo total, tiempo del modelo, `prompt_tokens`, `completion_tokens` y si hubo 429 del proveedor o del arnés, en `spike/bench/salida/*.json` (R4, R5; depende de T007)
- [x] T009 [P] Escribir `spike/measure/memoria.sh` que capture memoria (RSS) y CPU por contenedor en reposo, bajo carga y en ráfaga, y guarde un CSV en `spike/measure/salida/`

**Checkpoint**: VM caracterizada, banco y medidores listos. Las historias pueden empezar.

---

## Phase 3: User Story 1 - Veredicto del arnés de agente (Priority: P1) 🎯 MVP

**Goal**: saber si Hermes por su `api_server`, con todas las herramientas nativas apagadas y solo la MCP del SAS, es seguro y barato; si no, activar el bucle propio (ADR-002).

**Independent Test**: levantar el arnés con la MCP de V2 (o una MCP de prueba mínima), correr el banco y leer las filas V3 de `resultados.md`; no necesita WhatsApp.

### Implementation for User Story 1

- [ ] T010 [US1] Crear `spike/hermes/compose.yml` y `spike/hermes/config.yaml`: `agent.disabled_toolsets` con todas las nativas, solo la MCP del SAS, contenedor **sin montajes del host**, `API_SERVER_KEY` por variable de entorno, **sin** `multiplex_profiles` [EXT:Hermes Agent api_server] (R1; FR-010, FR-012)
- [ ] T011 [US1] Escribir y correr `spike/hermes/prueba_toolsets.sh`: `GET /v1/toolsets` no debe listar ninguna nativa; guardar la salida en `resultados.md` (FR-010)
- [ ] T012 [P] [US1] Escribir y correr `spike/hermes/prueba_hostil.sh` con las consultas del grupo `hostil` (pedir comando, archivo, web, datos de otro cliente, cambio de instrucciones); verificar en el registro del contenedor que no se ejecutó nada (R2; FR-010)
- [ ] T013 [US1] Escribir y correr `spike/hermes/prueba_sesiones.sh`: tres conversaciones con `X-Hermes-Session-Id` distintos; un dato inventado en la A no debe aparecer en la B (FR-011)
- [ ] T014 [US1] Contención de red en `spike/hermes/red/`: red interna más proxy con lista blanca (proveedor de modelos y MCP); comprobar **desde dentro del contenedor** que otro destino falla y que no hay montajes del host (R10; FR-012)
- [ ] T015 [US1] Escribir y correr `spike/hermes/prueba_429.py`: 12 solicitudes simultáneas contra el límite de 10; confirmar 429 en las excedentes y recuperación completa con reintento y espera creciente, sin pérdida ni duplicado; anotar si el límite aplica a `/v1/chat/completions` o solo a `/v1/runs` (R6; FR-013)
- [x] T016 [US1] Escribir `spike/baseline/bucle.py`: bucle de referencia mínimo con el mismo proveedor, modelo, herramientas MCP y banco (R3; FR-014)
- [ ] T017 [US1] Correr el banco (≥20 consultas) en Hermes y en el bucle con `runner.py`; calcular tokens por llamada y su razón, y p50/p95 de latencia separando modelo de arnés; pasa si razón ≤ 2× y p95 < 15 s (R3–R5; FR-014, FR-015; depende de T008, T010, T016)
- [ ] T018 [US1] Medir la memoria del arnés en reposo y bajo carga con `spike/measure/memoria.sh` (FR-016)
- [ ] T019 [US1] Dar el veredicto del arnés en `resultados.md` (filas V3 y §5): `go`, o `no-go` con bucle propio si la razón > 2× o no se pueden apagar las herramientas (FR-025)

**Checkpoint**: arnés con veredicto, probado de forma independiente.

---

## Phase 4: User Story 2 - Veredicto del canal WhatsApp (Priority: P1)

**Goal**: saber si Evolution API sobre Baileys conecta, reconecta solo y distingue lo que escribe un humano de lo que envía la API (base del takeover) (ADR-001).

**Independent Test**: vincular el número de prueba y ejecutar el guion; no necesita el arnés. **Bloqueada hasta tener la línea.**

### Implementation for User Story 2

- [ ] T020 [US2] (Richard) Comprar y entregar un número de WhatsApp dedicado, no VoIP; mientras no exista, marcar V5 `bloqueada` con la causa en `resultados.md` (FR-027)
- [ ] T021 [US2] Crear `spike/evolution/compose.yml` con Evolution API y Baileys con versión o digest fijados; registrar las versiones en `resultados.md` §1 [EXT:Ban de WhatsApp en bots 2026] (FR-004)
- [ ] T022 [US2] Vincular el número de prueba, crear `spike/evolution/receptor.py` (receptor mínimo del webhook), recibir un mensaje del equipo con su contenido y remitente, y responderlo por la API (FR-006)
- [ ] T023 [US2] Escribir y correr `spike/evolution/guion_caidas.sh`: cortar el proceso, cortar la red 2 minutos y cortar el proceso otra vez; medir el tiempo hasta reconectar sin nuevo QR (≤ 120 s `[Adivinando]`) y registrar qué pasó con los mensajes llegados durante la caída (R8; FR-007)
- [ ] T024 [US2] Probar `fromMe` en `spike/evolution/receptor.py`: enviar un mensaje por la API y otro a mano desde el teléfono; distinguirlos cruzando el id del mensaje con la respuesta del envío y anotar el resultado en `resultados.md` [EXT:Evolution API] (R8; FR-008)
- [ ] T025 [US2] Medir la memoria del canal en reposo y bajo una ráfaga sintética con `spike/measure/memoria.sh` (FR-009)
- [ ] T026 [US2] Dar el veredicto del canal en `resultados.md` (filas V5 y §5): `go`, o `no-go` con WAHA o BuilderBot como alternativa (FR-025)

**Checkpoint**: canal con veredicto, o `bloqueada` con causa.

---

## Phase 5: User Story 3 - Herramientas de lectura con SQL fijo (Priority: P2)

**Goal**: saber si MCP Toolbox, con un `tools.yaml` generado, da lectura segura (SQL fijo, parámetros tipados, solo lectura) o si hace falta un MCP propio (ADR-005).

**Independent Test**: generar las herramientas del esquema sintético y atacarlas; sin arnés ni WhatsApp.

### Implementation for User Story 3

- [x] T027 [US3] Crear `spike/toolbox/esquema.sql` y `spike/toolbox/esquema.json`: tablas `producto(id, sku, nombre, categoria, precio, activo)` e `inventario(producto_id, cantidad)` con datos inventados, rol `lector` (solo SELECT) y rol `escritor` (solo para comprobar que el lector no puede escribir)
- [x] T028 [P] [US3] Escribir `spike/toolbox/generar_tools.py` que genere `tools.yaml` desde `esquema.json` con herramientas `kind: tool` con `type: postgres-sql` (`catalogo_buscar`, `item_obtener`, `disponibilidad`), `statement` fijo con `$1…` y `parameters` tipados [EXT:MCP Toolbox for Databases] (R7; FR-017; depende de T027)
- [ ] T029 [US3] Crear `spike/toolbox/compose.yml` con Toolbox y Postgres con versiones fijadas, usando el rol `lector` en el `source`; nunca `--prebuilt=postgres` (FR-004, FR-019)
- [ ] T030 [US3] Escribir y correr `spike/toolbox/ataques.sh`: comillas, `; DROP`, `UNION SELECT` y parámetros de tipo equivocado; ninguno debe alterar la consulta ni devolver datos fuera de lo declarado (R7; FR-018)
- [ ] T031 [US3] Comprobar en `spike/toolbox/tools.yaml` y `spike/toolbox/compose.yml` que no existe ninguna vía de SQL libre y que un `INSERT` con el rol `lector` falla; anotar el resultado en `resultados.md` (FR-019)
- [ ] T032 [US3] Dar el veredicto de las herramientas en `resultados.md` (filas V2 y §5): `go`, o `no-go` con MCP propio (FR-025)

**Checkpoint**: herramientas de lectura con veredicto.

---

## Phase 6: User Story 4 - Cupo de clientes por VM (Priority: P2)

**Goal**: saber cuántos clientes caben en la VM con mediciones, contrastado con la meta de 4 clientes e informando el techo.

**Independent Test**: con los componentes levantados, medir y calcular; el cálculo es verificable con la tabla de mediciones.

### Implementation for User Story 4

- [ ] T033 [US4] Medir la memoria de cada componente (Evolution, proxy, Hermes, SAS/Toolbox, Postgres) en reposo, bajo el banco y en ráfaga, separando **compartido** de **por cliente**, y volcar el CSV a `resultados.md` §4 (R9; FR-021)
- [ ] T034 [US4] Proyectar a 4 clientes con carga simulada (1 número real) y calcular `cupo = piso((RAM_total − margen_SO − compartido) / por_cliente)` con margen inicial 1,5 GB `[Adivinando]`; declarar la proyección como tal (R9; FR-021)
- [ ] T035 [US4] Informar en `resultados.md` §4 el techo de la VM y el componente que se agota primero, y contrastarlo con la meta de 4 clientes (FR-022)
- [ ] T036 [US4] Anotar el perfil de uso observado frente a los umbrales de reclamo por inactividad de Oracle [EXT:Oracle Always Free] y dar el veredicto del cupo en `resultados.md` §4 y §5

**Checkpoint**: cupo calculado con mediciones.

---

## Phase 7: User Story 5 - Prueba de descarte de Antigravity (Priority: P3)

**Goal**: evidencia de si Antigravity sirve como agente del bot; seis criterios obligatorios, falla uno y se descarta (ADR-008).

**Independent Test**: llenar la tabla de seis filas; no depende del canal.

### Implementation for User Story 5

- [x] T037 [US5] Criterio 6: citar la cláusula 6 de los términos en la tabla de `resultados.md` §3 con `[EXT:Antigravity terminos]` y dar el veredicto; si falla, marcar "descartado por criterio 6" y las demás filas como `no probado` (R11; FR-023)
- [x] T038 [US5] Solo si T037 no descartó: criterios 1 y 5, invocar Antigravity sin interfaz gráfica ni sesión interactiva desde la VM con `spike/bench/antigravity.sh` y anotar la evidencia en `resultados.md` §3 (R11; FR-023) **(no aplica: T037 descartó Antigravity)**
- [x] T039 [US5] Solo si sigue: criterios 2, 3 y 4 (≥3 conversaciones aisladas, p95 < 15 s, uso de la MCP del SAS) con el banco de `spike/bench/banco.json` (FR-023) **(no aplica: T037 descartó Antigravity)**
- [x] T040 [US5] Solo si pasa los seis: comparar con el arnés sobre el mismo banco y registrar la comparación en `resultados.md` §3 (FR-024) **(no aplica: T037 descartó Antigravity)**
- [x] T041 [US5] Completar en `resultados.md` §3 la tabla pasa/falla/no probado con evidencia por fila y anotar el criterio que descartó (FR-023)

**Checkpoint**: Antigravity con veredicto de descarte o de continuidad.

---

## Phase 8: Polish & Cross-Cutting (cierre V6)

**Purpose**: veredictos, decisiones registradas y cierre de fase

- [ ] T042 Consolidar en `resultados.md` §5 una fila por pieza (canal, arnés, herramientas, Antigravity) con `go`/`no-go` y la alternativa activada (FR-025)
- [ ] T043 Escribir los ADR nuevos en `vault/Decisiones/` (ADR-009 en adelante) que confirman o superan a ADR-001, 002, 005 y 008 con `supersedes:` cuando corresponda, y agregarlos a `vault/MOCs/02 - Indice de Decisiones.md` (FR-026)
- [ ] T044 Verificar que cada verificación tiene estado `pasa`/`falla`/`bloqueada` con causa, que se cumplen SC-001 a SC-006 y que no hay secretos ni datos reales en `spike/` ni en `resultados.md` (FR-027, SC-006)
- [ ] T045 Actualizar el nivel de SPEC-001 en `vault/MOCs/00 - Indice de Specs.md`, sobreescribir `STATE.md`, correr `graphify update .` y `graphify save-result` (cierre de fase de CLAUDE.md)
- [ ] T046 Hacer los commits atómicos, subir la rama y actualizar el pull request siguiendo el ciclo de Git de `CLAUDE.md`; preguntar a Richard por `/thermos` antes de unir
- [ ] T047 Cuando exista la VM definitiva ([[ADR-009]]), repetir allí V0 (`spike/vm/forma.sh`), V4 (`spike/measure/memoria.sh`), todas las mediciones de memoria y V5; reemplazar en `resultados.md` los valores provisionales por los de la VM definitiva y cerrar la nota de provisional (FR-001, FR-021, FR-022). **Se ejecuta antes de T042.**

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sin dependencias.
- **Foundational (Phase 2)**: depende de Setup; **bloquea** todo veredicto. T004 y T005 dependen de Richard.
- **Historias (Phase 3–7)**: dependen de Foundational. Reglas de dependencia reales:
  - **US1** consume la MCP de **US3** (T017 usa las herramientas de T029). Si US3 no está lista, usar una MCP de prueba mínima y anotarlo (FR-020).
  - **US4** necesita US1 y US3 corriendo (y US2 para el número real); sin US2 se proyecta con carga simulada y se declara.
  - **US2** depende de T020 (la línea de WhatsApp).
  - **US5** es independiente, y su primer paso (T037) solo requiere leer.
- **Polish (Phase 8)**: depende de las historias que hayan dado veredicto.

### Orden de ejecución recomendado (distinto del de prioridad)

1. Setup T001–T003 → Foundational T004–T009
2. **US5 solo T037** (barato; si falla, Antigravity queda descartado ya)
3. **US3** T027–T032
4. **US1** T010–T019
5. **US4** T033–T036
6. **US2** T021–T026 (cuando llegue la línea; T020 es tuya)
7. **T047** (repetir en la VM definitiva) y luego Phase 8 T042–T046

### Within Each User Story

- Configuración y levantamiento antes de las pruebas; pruebas antes del veredicto.
- Cada veredicto escribe su fila en `resultados.md` antes de pasar a la siguiente historia.

### Parallel Opportunities

- Setup: T002 y T003 en paralelo.
- Foundational: T005, T007 y T009 en paralelo; T008 espera a T007.
- Las tareas [P] dentro de cada historia (T012, T028) no comparten archivo.
- US3 y US5-T037 pueden avanzar a la vez; US2 queda esperando la línea sin frenar a las demás.

---

## Parallel Example: Foundational

```bash
# Insumos y herramientas que no se pisan:
Task: "Crear la llave de OpenRouter y fijar el modelo :free en spike/.env"
Task: "Crear spike/bench/banco.json con ~20 consultas sintéticas"
Task: "Escribir spike/measure/memoria.sh"
```

---

## Implementation Strategy

### MVP First (lo que no necesita el número de WhatsApp)

1. Setup + Foundational
2. US5-T037 (descarte barato) → US3 → US1
3. **STOP y VALIDAR**: arnés y herramientas con veredicto en `resultados.md`
4. Con eso ya se puede decidir F2 (SAS) para esa parte; el canal queda pendiente de la línea

### Incremental Delivery

1. Cada historia cierra con su fila de veredicto y, al terminar el conjunto, un commit pequeño.
2. US4 solo se cierra con los números reales de US1, US3 y, si existe, US2.
3. El spike **no se da por cerrado** mientras alguna verificación esté sin estado (FR-027).

---

## Notes

- Total: 47 tareas (Setup 3 · Foundational 6 · US1 10 · US2 7 · US3 6 · US4 4 · US5 5 · Cierre 6).
- La VM actual es provisional y compartida ([[ADR-009]]): sus resultados son provisionales hasta T047.
- Todo es desechable salvo `resultados.md` y los ADR nuevos.
- Datos solo sintéticos y modelos `:free` (Constitución IV); el bot nunca escribe primero (Constitución III).
- Commit después de cada grupo lógico, con las reglas de Git de `CLAUDE.md`.
