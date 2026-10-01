# chatbot-richard

Proyecto gestionado por la skill `full-autodev`. Perfil: `software`.

## Orientacion al arrancar (presupuesto duro)

Leer **exactamente dos archivos**, nada mas:
1. `STATE.md` — donde estamos
2. `vault/AGENT-INDEX.md` — por donde entrar

Todo lo demas se alcanza siguiendo `[[enlaces]]` bajo demanda.
**Nunca leer el vault en bloque. Nunca releer una fuente que ya tiene ficha.**

## La referencia antes que la memoria

Que pide el cliente (o el usuario, o el paper) se responde **citando** su parrafo, registrado
en `vault/Fuentes/REFERENCIAS.md` (`[EXT:NNN §x]`). Sin cita: "no esta escrito", `[INT?]`,
se pregunta y no se construye encima. Un PDF sin capa de texto se transcribe a `.md` con
parrafos citables; no se trabaja "de lo que se recuerda que decia".

## Herramientas de lectura: context-mode siempre

Leer, buscar, hacer grep o diff y traer webs pasa por context-mode
(`ctx_batch_execute`, `ctx_execute`, `ctx_execute_file`, `ctx_search`, `ctx_fetch_and_index`).
Bash, Read y Grep directos quedan para mutar estado (git, mkdir, rm) o para leer un archivo
que se va a editar con Edit. El grafo responde *que* mirar; context-mode lo lee sin volcarlo.

## Stack de calidad (plugins de usuario)

| Momento | Herramienta | Que hace |
|---|---|---|
| Mientras se escribe | skill `anti-slop` (auto) | reglas de prosa, codigo, UI y seguridad |
| Cada commit | `gates.py::SLOP-SCAN` | scanner determinista sobre lo cambiado |
| Antes de subir el nivel de un spec | `/slop-check diff` | revision semantica puntuada del diff |
| Antes de cerrar un spec en `N2`+ o de un merge | `/thermos` | auditoria paralela correctitud/seguridad + mantenibilidad |

Un hallazgo bloqueante de `/thermos` se corrige antes de subir el nivel. Uno no bloqueante
va a backlog o a una decision; no se deja solo en el chat.
El stack completo (cuatro variantes de anti-slop, con sus hooks) y su verificacion estan en
la skill `full-autodev`, archivo `references/calidad.md`, y en `references/stack.ps1`.

## Puerta de consumo

Antes de responder sobre este proyecto, o de escribir un spec, un plan o una ficha:

```bash
graphify query "<pregunta>"
graphify affected "<nodo>"
```

Leer un archivo completo solo cuando el grafo señala un `source_location` concreto.
Si el grafo no tiene la respuesta, decirlo y leer la fuente. No rellenar con memoria.

## Ley de Dueño Unico

Cada hecho vive en **un** archivo. Lo demas enlaza, no repite.

| Hecho | Dueño |
|---|---|
| Requisitos de una feature | `specs/NNN-slug/spec.md` |
| Diseño tecnico | `specs/NNN-slug/plan.md` |
| Invariantes del proyecto | `.specify/memory/constitution.md` |
| Significado de un termino | `vault/Conceptos/<X>.md` |
| Por que se decidio algo | `vault/Decisiones/ADR-NNN.md` (nombre = ID exacto), o el registro unico de `decisions_file` en `gates.toml` (rige uno solo) |
| Que specs existen | ficha en `vault/Specs/` + fila en `vault/MOCs/00 - Indice de Specs.md` |
| Nivel de madurez de un spec (N0-N3 + limite) | columnas `Nivel`/`Limite` de `vault/MOCs/00 - Indice de Specs.md` (la ficha no lo repite) |
| Fuente externa | `vault/Fuentes/<Titulo>.md` |
| Estado actual | `STATE.md` (se sobreescribe) |

Prohibido:
- Reescribir un hecho que ya tiene dueño. Enlazarlo.
- Acumular archivos de estado o handoff. `STATE.md` se sobreescribe.
- Citar `graphify-out/` como fuente de verdad: es un indice derivado.
- Correr `graphify export obsidian` o `graphify export wiki`. Generan un .md por nodo,
  documentacion derivada que compite con las fichas escritas a mano. Es la duplicacion
  que este proyecto existe para evitar.

## Antes de crear un spec

1. Leer `vault/MOCs/00 - Indice de Specs.md`.
2. `graphify query "<lo que se va a especificar>"` — ¿ya hay un nodo que lo cubre?
3. `graphify affected "<concepto central>"` — ¿que specs quedan superados?

Si ya existe: extenderlo, o marcar el viejo `superseded` y poner `supersedes:` en el
nuevo. Decirlo explicitamente. Al crear el spec, agregar SIEMPRE su ficha en
`vault/Specs/` y su fila en el MOC: omitirlo es la falla `SPEC-UNINDEXED`.

## Comandos de Spec Kit

Se invocan como skills. Los nombres reales de este proyecto:
`speckit-constitution`, `speckit-specify`, `speckit-clarify`, `speckit-plan`,
`speckit-tasks`, `speckit-analyze`, `speckit-checklist`, `speckit-implement`,
`speckit-converge`.

## Al cerrar cada fase

```bash
graphify update .
graphify save-result --question "<pregunta guia>" --answer "<conclusion 2-3 lineas>"
```
Y sobreescribir `STATE.md`.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
