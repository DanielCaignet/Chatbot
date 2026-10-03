# Contrato: tabla de resultados

`specs/001-spike-viabilidad/resultados.md` es el **único** lugar de las mediciones. Estructura fija:

## 1. Entorno
Forma de la VM (arquitectura, núcleos, memoria, disco, sistema operativo) y versiones o digests
exactos de cada pieza y del modelo `:free` usado.

## 2. Tabla de verificaciones
| Verificación | Requisito | Criterio | Resultado | Estado | Evidencia |
|---|---|---|---|---|---|
| V3 | FR-010 | Ninguna herramienta nativa activa | `GET /v1/toolsets`: … | pasa / falla / bloqueada | enlace al registro |

Reglas:
- `Estado` solo toma `pasa`, `falla` o `bloqueada` (con causa). Nunca vacío.
- `Resultado` lleva el número o registro crudo, no una interpretación.
- Un 429 del proveedor y uno del arnés van en filas distintas.

## 3. Tabla de Antigravity (ADR-008)
| # | Criterio | Estado | Evidencia |
|---|---|---|---|
| 1 | Invocación programática sin interfaz gráfica | | |
| 2 | ≥3 conversaciones concurrentes aisladas | | |
| 3 | p95 < 15 s | | |
| 4 | Usa la MCP del SAS | | |
| 5 | 24/7 en Linux ARM sin sesión interactiva | | |
| 6 | Términos permiten atender a terceros | | texto citado + `[EXT:Antigravity terminos]` |

Si una fila falla, las siguientes pueden quedar `no probado` con la nota "descartado por criterio N".

## 4. Cupo
Los campos de **Cupo** de `data-model.md` y la conclusión frente a la meta de 4.

## 5. Veredictos
Una fila por pieza: `go`/`no-go`, alternativa y enlace al ADR nuevo.
