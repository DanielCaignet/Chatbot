# Resultados: Spike de viabilidad F1 (SPEC-001)

> **Único dueño de las mediciones.** Formato fijo en [contracts/resultados-tabla.md](contracts/resultados-tabla.md).
> Estados: `pendiente` (aún no se intentó) · `pasa` · `falla` · `bloqueada` (con causa). Al cerrar el spike no puede quedar ninguna `pendiente` (FR-027).

## 1. Entorno

| Dato | Valor |
|---|---|
| Acceso SSH a la VM | pendiente |
| Arquitectura, núcleos, memoria, disco, sistema operativo | pendiente (V0, tarea T006) |
| Modelo `:free` de OpenRouter (identificador exacto) | pendiente (T005) |
| Versión o digest: Docker | pendiente |
| Versión o digest: Hermes | pendiente |
| Versión o digest: MCP Toolbox | pendiente |
| Versión o digest: Evolution API / Baileys | pendiente |
| Versión: Postgres | pendiente |

## 2. Verificaciones

| Verificación | Requisito | Criterio | Resultado | Estado | Evidencia |
|---|---|---|---|---|---|
| V0 | FR-001 | Forma real de la VM registrada y contrastada con 2 OCPU / 12 GB | | pendiente | |
| V2 | FR-017 | Herramientas generadas desde descripción del esquema | | pendiente | |
| V2 | FR-018 | Entradas hostiles no alteran la consulta | | pendiente | |
| V2 | FR-019 | Sin vía de SQL libre; escritura con rol de lectura falla | | pendiente | |
| V3 | FR-010 | Ninguna herramienta nativa activa; mensajes hostiles no ejecutan nada | | pendiente | |
| V3 | FR-011 | Sesiones paralelas aisladas | | pendiente | |
| V3 | FR-012 | Sin montajes del host; salida de red limitada | | pendiente | |
| V3 | FR-013 | 429 del arnés y recuperación sin pérdida ni duplicado | | pendiente | |
| V3 | FR-014 | Tokens por llamada ≤ 2× el bucle de referencia (≥20 consultas) | | pendiente | |
| V3 | FR-015 | p95 < 15 s (modelo y arnés separados) | | pendiente | |
| V3 | FR-016 | Memoria del arnés medida | | pendiente | |
| V3 | FR-020 | El arnés consume las herramientas de V2 de punta a punta | | pendiente | |
| V4 | FR-021 | Memoria por componente, compartido vs por cliente | | pendiente | |
| V4 | FR-022 | Cupo contrastado con la meta de 4 clientes e informado el techo | | pendiente | |
| V5 | FR-006 | Conexión, mensaje entrante y respuesta por la API | | pendiente | |
| V5 | FR-007 | Reconexión sin nuevo emparejamiento en ≤ 120 s | | pendiente | |
| V5 | FR-008 | Mensaje humano distinguible del enviado por la API | | pendiente | |
| V5 | FR-009 | Memoria del canal medida | | pendiente | |

## 3. Antigravity (ADR-008)

| # | Criterio | Estado | Evidencia |
|---|---|---|---|
| 1 | Invocación programática sin interfaz gráfica | pendiente | |
| 2 | ≥3 conversaciones concurrentes aisladas | pendiente | |
| 3 | p95 < 15 s | pendiente | |
| 4 | Usa la MCP del SAS | pendiente | |
| 5 | 24/7 en Linux ARM sin sesión interactiva | pendiente | |
| 6 | Términos permiten atender a terceros | pendiente | |

## 4. Cupo

| Campo | Valor |
|---|---|
| `ram_total` | pendiente |
| `margen_so` | pendiente (inicial 1,5 GB, `[Adivinando]`) |
| `compartido` | pendiente |
| `por_cliente` | pendiente |
| `cupo` | pendiente |
| `techo` y `componente_limitante` | pendiente |
| `meta` | 4 clientes |
| Conclusión | pendiente |

## 5. Veredictos

| Pieza | Decisión | Alternativa | ADR |
|---|---|---|---|
| Canal (Evolution + Baileys) | pendiente | WAHA / BuilderBot | |
| Arnés (Hermes) | pendiente | bucle propio | |
| Herramientas de lectura (MCP Toolbox) | pendiente | MCP propio | |
| Antigravity | pendiente | descartado | |
