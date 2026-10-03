# Research: Spike de viabilidad F1

Cada decisión cita su ficha en `vault/Fuentes/`. Lo que depende de la VM real se marca
`[medir en V0]`; no es una pregunta para Richard.

## R1 — Cómo se apagan las herramientas nativas de Hermes
- **Decisión**: `agent.disabled_toolsets` en `config.yaml` del contenedor, con todas las nativas listadas; se deja solo la MCP del SAS [EXT:Hermes Agent api_server].
- **Por qué**: se aplica después de la config por plataforma y gana siempre.
- **Alternativas**: apagarlas solo por plataforma (más débil: una config guardada las reactiva).
- **Riesgo conocido**: con `multiplex_profiles: true` el api_server las ignora (issue #91415). Se usa un contenedor por cliente **sin multiplex** y V3 lo comprueba igualmente.

## R2 — Cómo se verifica que están apagadas
- **Decisión**: dos pruebas. (1) `GET /v1/toolsets` no lista ninguna nativa. (2) Mensajes hostiles del banco piden ejecutar un comando, leer un archivo y buscar en la web; el registro del contenedor no debe mostrar ninguna ejecución [EXT:Hermes Agent api_server].
- **Por qué**: la lista puede mentir (ver R1); el comportamiento no.

## R3 — Bucle de referencia para medir tokens
- **Decisión**: bucle mínimo de unas decenas de líneas contra el mismo proveedor y modelo, con las mismas herramientas MCP y el mismo banco. Descartable.
- **Por qué**: sin base de comparación, "≤ 2×" no se puede medir (FR-014).
- **Alternativa**: comparar con una cifra teórica; descartada, no es medición.

## R4 — De dónde salen los tokens
- **Decisión**: del campo `usage` (`prompt_tokens`, `completion_tokens`) de la respuesta compatible con OpenAI, que Hermes devuelve [EXT:Hermes Agent api_server]; el bucle de referencia usa el mismo campo.
- **Riesgo**: con streaming o varias vueltas de herramientas el `usage` puede ser parcial `[medir en V3]`. Si pasa, se suma por llamada al proveedor y se anota.

## R5 — Latencia: separar modelo de arnés
- **Decisión**: se registran tres tiempos por consulta: total (cliente), llamada al modelo (según el proveedor o el bucle) y diferencia = sobrecosto del arnés. Se reportan p50 y p95.
- **Por qué**: los modelos `:free` tienen latencia y topes variables [EXT:OpenRouter limites]; sin separar, el veredicto del arnés se contamina.
- **Regla**: un 429 del proveedor se registra aparte de un 429 del arnés.

## R6 — Prueba de 429 del arnés
- **Decisión**: 12 solicitudes simultáneas contra el límite por defecto de 10 ejecuciones concurrentes; se espera 429 en las excedentes y recuperación completa con reintento y espera creciente.
- **Incógnita** `[Adivinando]`: si el límite aplica a `/v1/chat/completions` o solo a las ejecuciones largas (`/v1/runs`). V3 lo comprueba y lo anota en la ficha.

## R7 — Herramientas de lectura con MCP Toolbox
- **Decisión**: generar `tools.yaml` desde una descripción del esquema sintético (`catalogo_buscar`, `item_obtener`, `disponibilidad`) con herramientas `kind: tool` con `type: postgres-sql`, `statement` con `$1…` y `parameters` tipados [EXT:MCP Toolbox for Databases]. Solo-lectura con un rol de Postgres sin permisos de escritura.
- **Ataques**: comillas, `; DROP`, `UNION SELECT`, parámetros fuera de tipo, intento de `INSERT` con el rol de lectura.
- **Prohibido**: `--prebuilt=postgres` (incluye SQL libre).
- **Plan B si falla**: MCP propio (ADR-005).

## R8 — Canal: reconexión y `fromMe`
- **Decisión**: guion con tres cortes (proceso, red 2 minutos, proceso otra vez) midiendo el tiempo hasta reconectar sin nuevo QR y qué mensajes llegaron. Para `fromMe`: enviar uno por API y otro a mano desde el teléfono, y distinguirlos cruzando el id del mensaje con la respuesta del envío [EXT:Evolution API].
- **Por qué**: hay reportes de `fromMe: true` también para envíos por API.
- **Seguridad**: versión de Evolution y Baileys fijadas; hubo un fork malicioso en npm [EXT:Ban de WhatsApp en bots 2026].

## R9 — Memoria y cupo
- **Decisión**: medir RSS por contenedor en reposo, bajo el banco y en ráfaga, separando **compartido** (Evolution, proxy) de **por cliente** (Hermes, SAS, Postgres). Fórmula: `cupo = piso((RAM_total − margen_SO − compartido) / por_cliente)`; margen inicial 1,5 GB `[Adivinando]`. Se proyecta a 4 clientes con carga simulada y se informa el techo y el componente que se agota primero [EXT:Oracle Always Free].
- **Alternativa**: confiar en las cifras publicadas; descartada: no hay datos de ARM para Evolution.

## R10 — Contención de red del arnés
- **Decisión** `[medir en V3]`: red de Docker interna más un proxy con lista blanca (proveedor de modelos y MCP). Comprobar desde dentro del contenedor que otro destino falla.
- **Alternativa**: reglas de firewall del host; más frágiles y más difíciles de repetir.

## R11 — Antigravity: orden de pruebas
- **Decisión**: leer primero los términos (criterio 6). La cláusula 6 dice que usar herramientas de terceros para acceder al servicio es un incumplimiento y que atender a clientes con una cuenta personal no está autorizado en el texto [EXT:Antigravity terminos]. Si el criterio 6 falla, se descarta sin más pruebas.
- **Matiz**: la comunidad dice que `agy -p` es válido para scripts propios; es evidencia débil frente al contrato.

## R12 — Dónde van los resultados
- **Decisión**: `resultados.md` único con la tabla de `contracts/resultados-tabla.md`. Cada veredicto firme produce un ADR nuevo que confirma o supera al original (ADR inmutables).

## R13 — Contenido del banco sintético
- **Decisión**: ~20 consultas de tienda en seis grupos: precio, stock, producto inexistente, ambigüedad, fuera de tema, y hostiles (inyección de instrucciones, petición de comandos o archivos, petición de datos de otro cliente). Tamaño `[Adivinando]`; el banco completo es de F2.
