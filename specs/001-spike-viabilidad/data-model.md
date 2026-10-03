# Data Model: Spike de viabilidad F1

No hay base de datos de producto. Son las entidades que el spike registra en `resultados.md`.
El esquema sintético de tienda (solo para probar V2/V3) es la excepción y se describe al final.

## Verificación
| Campo | Descripción |
|---|---|
| id | `V0`…`V5` (ver `plan.md`) |
| pieza | VM · Antigravity · Herramientas · Arnés · Cupo · Canal |
| requisitos | FR cubiertos |
| estado | `pendiente` · `en curso` · `pasa` · `falla` · `bloqueada` |
| causa_bloqueo | obligatoria si `bloqueada` (acceso, llave OpenRouter, número) |

## Evidencia
| Campo | Descripción |
|---|---|
| verificacion | id de la verificación |
| procedimiento | pasos repetibles (`quickstart.md`) |
| entradas | consultas del banco, parámetros, versiones fijadas |
| resultado_crudo | números o registros tal cual salieron |
| fecha | cuándo se midió |

## Veredicto
| Campo | Descripción |
|---|---|
| pieza | canal · arnés · herramientas · Antigravity |
| decision | `go` · `no-go` |
| alternativa | si `no-go`: WAHA/BuilderBot · bucle propio · MCP propio · descartado |
| adr | ADR nuevo que lo registra (confirma o supera al original) |

## Banco sintético
Lista de consultas con: `id`, `grupo` (precio, stock, inexistente, ambigua, fuera de tema, hostil),
`texto`, `espera` (qué debe pasar, sin cifras inventadas). Común a arnés, bucle de referencia y
Antigravity.

## Cupo
`ram_total`, `margen_so`, `compartido`, `por_cliente`, `cupo = piso((ram_total − margen_so − compartido) / por_cliente)`,
`techo`, `componente_limitante`, `meta = 4`.

## Esquema sintético de tienda (solo V2/V3)
- `producto(id, sku, nombre, categoria, precio, activo)`
- `inventario(producto_id, cantidad)`
- Datos inventados; rol `lector` (solo SELECT) y rol `escritor` (solo para comprobar que el lector no puede escribir).
