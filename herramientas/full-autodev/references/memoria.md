# full-autodev · memoria y contexto

> Se carga desde `SKILL.md` antes de responder sobre el proyecto o de actuar (publicar, desplegar, entregar un enlace). Las reglas del núcleo (`SKILL.md`) siguen rigiendo acá.

## Memoria y contexto: context-mode + Obsidian + graphify (fijo, todo proyecto)

Regla del usuario (2026-09-28): la memoria y el contexto de **cada** proyecto se manejan con
estas tres herramientas, y ninguna es opcional ni se reemplaza por la memoria del agente.

| Herramienta | Es la memoria de… | Se usa para |
|---|---|---|
| **Obsidian** (vault + `docs/` + specs) | los hechos del proyecto: qué es, qué se decidió, cómo se opera (despliegue, accesos, procedimientos) | escribir cada hecho una vez, en su dueño, con `[[enlaces]]` |
| **graphify** | dónde está cada hecho y con qué se conecta, más las respuestas ya dadas (`graphify-out/memory/`) | orientarse **antes** de responder o actuar, también en operaciones, no sólo sobre el producto |
| **context-mode** | la sesión: lo leído, lo decidido, lo que falló (`ctx_search`, `sort: "timeline"`) | leer lo que el grafo señala sin volcarlo al contexto, y retomar después de una compactación |

La **auto-memoria del agente** (`~/.claude/projects/<proyecto>/memory/`) no es dueña de
ningún hecho del proyecto: guarda sólo **cómo trabajar**, es decir correcciones del usuario y
modos de consultar. Si un hecho aparece ahí, se mueve a su dueño en el vault o en `docs/`, y
en la memoria queda un enlace. Un hecho que sólo vive en la auto-memoria es invisible para el
grafo y para cualquier otro agente o persona del equipo.

**Antes de actuar** (publicar, desplegar, entregar un enlace, tocar el VPS), la misma puerta
que antes de responder: grafo, luego `source_location`, luego el procedimiento escrito. El
28-09 se publicó con la CLI en vez del script del repo, y se entregó la URL corta en vez del
enlace de acceso: las dos cosas estaban en `docs/DESPLIEGUE.md` y en el grafo.

> **Nunca ejecutar `graphify export obsidian` ni `export wiki` en un proyecto gestionado por esta skill.** Generan un `.md` por nodo a partir del grafo: documentación derivada que compite con las fichas escritas. Es exactamente la duplicación que esta skill existe para impedir. El vault se escribe; el grafo se deriva. Nunca al revés.

## Puerta de consumo (consume-first)

Antes de responder sobre el proyecto, o de escribir un spec, un plan o una ficha:

```bash
graphify query "<la pregunta o el concepto>"   # subgrafo acotado
graphify affected "<nodo>"                      # qué queda obsoleto si esto cambia
graphify path "<A>" "<B>"                       # cómo se relacionan dos cosas
graphify explain "<nodo>"                       # qué es un nodo y sus vecinos
```

Leer un archivo completo solo cuando el grafo señala un `source_location` concreto y se necesita el detalle fino. Si el grafo no tiene la respuesta, **decirlo** y leer la fuente. No rellenar con memoria paramétrica.

> Corregido 2026-09-28: «el grafo no tiene la respuesta» se afirma sólo después de verificarlo.
> Ese día se dijo que el grafo «no llega» al enlace de acceso de Vercel. Lo tenía: el nodo
> «Cómo lo ve el equipo» y una respuesta guardada del 26-09. Falló la consulta: se hizo con
> palabras sueltas y la salida quedó cortada en 54 de 120 nodos. Antes de concluir que algo falta:
> 1. formular la consulta como la pregunta que haría una persona, no como palabras clave;
> 2. si la salida dice `TRUNCATED`, repetir con más `--budget`;
> 3. `graphify explain "<título de sección>"`: los nodos de Markdown son **títulos**, sin el
>    cuerpo, así que un término que sólo está en el texto («bypass») da 0 resultados;
> 4. revisar `graphify-out/memory/`, las respuestas guardadas con `save-result`;
> 5. leer el `source_location` que aparezca.
>
> Si después de eso el grafo sigue sin cubrirlo, es un hueco semántico: se deja en `STATE.md`
> para Antigravity (ver la tabla de abajo).

Si `graphify-out/graph.json` no existe, construirlo antes de contestar.

**Quién construye qué parte del grafo** (regla del usuario, 2026-09-23):

| Parte | Quién | Comando |
|---|---|---|
| Estructural (código, AST, sin LLM) | Claude, y el hook post-commit | `graphify update .` |
| **Semántica** (docs, specs, vault, fuentes del cliente) | **el agente de Antigravity** | en Antigravity, sobre la raíz del proyecto: `/graphify .` (o `/graphify --update`) |

`stack.ps1` instala la skill de graphify en Antigravity (`graphify install --platform antigravity`). Claude **no** lanza el pase semántico con su propio LLM. Cuando el grafo necesita semántica nueva, lo dice y lo deja como próximo paso en `STATE.md`.

## Herramientas de lectura: context-mode siempre (regla dura)

El grafo dice **qué** mirar; context-mode lo lee **sin volcarlo** al contexto. Leer,
buscar, hacer grep o diff, inspeccionar un repo y traer una web pasa por
`ctx_batch_execute` / `ctx_execute` / `ctx_execute_file` / `ctx_search` / `ctx_fetch_and_index`.
Bash, Read y Grep directos quedan solo para **mutar estado** (git, mkdir, rm, instalar) o
para leer un archivo que se va a **editar** con Edit. Sin context-mode instalado, decirlo y
seguir con las herramientas nativas.

## Varios proyectos

Un grafo por proyecto. Para consultas cruzadas no unificar vaults: federar con el grafo global.

```bash
graphify extract . --global --as <tag>
graphify global list
graphify query "<pregunta>" --graph "$(graphify global path)"
```
