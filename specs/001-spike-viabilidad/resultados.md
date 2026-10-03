# Resultados: Spike de viabilidad F1 (SPEC-001)

> **Único dueño de las mediciones.** Formato fijo en [contracts/resultados-tabla.md](contracts/resultados-tabla.md).
> Estados: `pendiente` (aún no se intentó) · `pasa` · `falla` · `bloqueada` (con causa). Al cerrar el spike no puede quedar ninguna `pendiente` (FR-027).

## 1. Entorno

| Dato | Valor |
|---|---|
| Acceso SSH a la VM | sí (VM provisional compartida, [[ADR-009]]; datos de acceso fuera del repositorio) |
| Fecha de medición (UTC) | 2026-10-03T03:52:50Z (provisional, [[ADR-009]]) |
| Forma según OCI (metadatos) | VM.Standard.A1.Flex, 2.0 OCPU, 12.0 GB |
| Arquitectura | aarch64 |
| Núcleos visibles | 2 |
| Memoria total visible (MiB) | 10898 |
| Memoria usada al medir (MiB) | 1417 (otro proyecto en la misma VM) |
| Memoria disponible al medir (MiB) | 9480 |
| Disco raíz | 30G total, 8.7G libres, 71% usado |
| Sistema operativo | Oracle Linux Server 9.8, kernel 6.12.0-204.92.4.4.3.el9uek.aarch64 |
| Python del sistema | 3.9.25 |
| Contenedores en ejecución (cualquier proyecto) | 2 |
| Modelo `:free` de OpenRouter (identificador exacto) | `nvidia/nemotron-3-super-120b-a12b:free` ([[ADR-010]]; respaldos de otros proveedores en [[ADR-011]], pendientes de T049) |
| Tope diario de solicitudes a `:free` (medido 2026-10-03, sin créditos) | 50 por día, común a todos los modelos; 0 usadas al medir |
| Versión o digest: Docker | 29.8.1 (Compose 5.5.1) |
| Versión o digest: Hermes | imagen `nousresearch/hermes-agent:v2026.9.24` (arm64 confirmado); el digest se anota al descargarla |
| Versión o digest: MCP Toolbox | pendiente |
| Versión o digest: Evolution API / Baileys | pendiente |
| Versión: Postgres | pendiente |

> **Provisional:** los resultados de V0, V4, memoria y V5 obtenidos en la VM provisional no valen como definitivos; se repiten en la VM definitiva (T047).

## 2. Verificaciones

| Verificación | Requisito | Criterio | Resultado | Estado | Evidencia |
|---|---|---|---|---|---|
| V0 | FR-001 | Forma real de la VM registrada y contrastada con 2 OCPU / 12 GB | OCI declara 2 OCPU / 12 GB (coincide con el plan [EXT:Oracle Always Free]); el sistema ve 2 núcleos ARM y 10.898 MiB de memoria (unos 1.390 MiB menos que 12 GB, `[Probable]`: reserva del sistema). Provisional ([[ADR-009]]) | pasa | `spike/vm/forma.sh`, §1 |
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
| 1 | Invocación programática sin interfaz gráfica | no probado | descartado por criterio 6 |
| 2 | ≥3 conversaciones concurrentes aisladas | no probado | descartado por criterio 6 |
| 3 | p95 < 15 s | no probado | descartado por criterio 6 |
| 4 | Usa la MCP del SAS | no probado | descartado por criterio 6 |
| 5 | 24/7 en Linux ARM sin sesión interactiva | no probado | descartado por criterio 6 |
| 6 | Términos permiten atender a terceros | **falla** `[Probable]` | Ver abajo |

**Evidencia del criterio 6** (leída el 2026-10-02 en https://antigravity.google/terms/; ficha [[Antigravity terminos]]):
- Cláusula 6: usar software, herramientas o servicios de terceros para acceder al servicio "is a breach of this Agreement" y puede suspender las cuentas de Antigravity y Gemini CLI. Nuestro bot sería precisamente software propio que accede al servicio para atender a clientes.
- Ninguna cláusula autoriza atender a clientes finales con una cuenta personal (ausencia de cláusula, no verificada con consulta legal).
- Cláusula 3: Google registra las interacciones y las usa para mejorar sus productos, lo que chocaría con la Constitución IV si hubiera datos reales.

**Matices (por qué es `[Probable]` y no `[Seguro]`):**
- El foro de Google dice que invocar `agy -p` desde scripts propios está soportado; es respuesta de comunidad, no el contrato.
- Los términos no aplican a quien accede por Gemini Enterprise o Workspace con otros términos. Esa vía no se evaluó y queda fuera del alcance del spike.
- No es asesoría legal.

**Conclusión:** por la regla de ADR-008 (falla uno, se descarta), Antigravity queda **descartado** como agente del bot. El ADR formal se escribe en T043.

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
| Antigravity | no-go `[Probable]` (criterio 6) | descartado | pendiente (T043) |
