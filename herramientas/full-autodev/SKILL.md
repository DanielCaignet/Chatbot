---
name: full-autodev
description: "Orquesta el ciclo completo de desarrollo dirigido por especificación (Spec Kit) sobre una memoria persistente: un vault de Obsidian escrito a mano y un grafo de conocimiento graphify derivado de él. El agente primero PRODUCE conocimiento estructurado y luego lo CONSUME en vez de releer fuentes. Trigger: /full-autodev <nombre del proyecto>. Usar también cuando el usuario pida armar el esqueleto de un proyecto, retomar uno existente, auditar specs duplicados u olvidados, o gestionar memoria y contexto entre specs."
---

# /full-autodev

Un comando que deja un proyecto listo para desarrollo dirigido por especificación con memoria persistente y consultable.

## Las tres herramientas no son capas paralelas

| Herramienta | Rol | Quién escribe | Cuándo se lee |
|---|---|---|---|
| **Spec Kit** | Qué se construye y en qué orden | El agente, por feature | Solo la feature activa |
| **Vault Obsidian** | Qué significan las cosas y cómo se relacionan | El agente, a mano, con `[[wikilinks]]` | Vía el grafo, bajo demanda |
| **graphify** | Índice consultable derivado de los dos anteriores | Nadie: se deriva | Siempre, antes de responder |

Los `[[wikilinks]]` del vault **son** las aristas que graphify indexa. El vault es la superficie de autoría del grafo, no una copia.

## Uso

```
/full-autodev <nombre>                 # bootstrap + entrevista + SDD en el directorio actual
/full-autodev <nombre> --path D:\ruta  # en otra ruta
/full-autodev <nombre> --profile research   # software (def.) | research | data
/full-autodev --resume                 # retomar un proyecto ya montado
/full-autodev --spec "<descripción>"    # agregar una feature
/full-autodev --audit                  # auditoría: specs olvidados, duplicación, grafo obsoleto
```

Si no se dio ruta, usar el directorio actual. Si el directorio actual no es el proyecto (p. ej. un scratch workspace), mover la sesión con `change_directory` antes de escribir nada.

## Qué archivo leer y cuándo (ruteo)

Este archivo es el núcleo: reglas que rigen siempre. El detalle de cada momento vive en un solo
archivo de `references/`, y se abre **al llegar a ese momento**, no antes y no de memoria. Si el
momento figura en la tabla y el archivo no se abrió en esta sesión, abrirlo antes de actuar.

| Momento | Leer |
|---|---|
| Antes de responder sobre el proyecto, o de actuar (publicar, desplegar, entregar un enlace, tocar el VPS) | `references/memoria.md` (context-mode + Obsidian + graphify, Puerta de consumo) |
| Antes de un commit con código, de fusionar un PR, de sellar o de responder a un bloqueo del hook; antes de adoptar un plugin o una skill | `references/calidad.md` (Stack de calidad, Auditoría obligatoria, Costo de thermos) |
| Proyecto nuevo | `references/fase-0-bootstrap.md` |
| Entrevista, constitución, spec, plan y tareas | `references/fase-1-4-diseno.md` |
| Escribir código, depurar un bug, verificar una UI | `references/fase-5-implementacion.md` |
| `--audit` | `references/audit.md` |
| Consultas cruzadas entre proyectos | `references/memoria.md` (Varios proyectos) |
| Cerrar un hito | `references/fase-6-retro.md` |

**Puerta de consumo, en una línea:** antes de responder o actuar, `graphify query` con la
pregunta como la haría una persona; no afirmar que el grafo no tiene algo sin los cinco pasos
de `references/memoria.md`.

> Corregido 2026-09-29: la skill tenía 504 líneas en un archivo y se cargaba entera en cada
> invocación. Se dividió por **momento de lectura**, no por tamaño: el núcleo queda en este
> archivo y cada fase en su archivo. El texto se movió línea por línea, sin reescribirlo. Ver
> CHANGELOG v0.5.

---

## Presupuesto de orientación (regla dura)

Al arrancar en un proyecto ya montado, leer **exactamente dos archivos**:

1. `STATE.md` — dónde estamos
2. `vault/AGENT-INDEX.md` — por dónde entrar

Juntos deben caber en ~100 líneas. Todo lo demás se alcanza siguiendo `[[enlaces]]` **bajo demanda**. Nunca leer el vault en bloque, nunca leer todos los specs, nunca releer PDFs o fuentes que ya tienen ficha.

Si esos dos archivos no alcanzan para orientarse, el defecto está en ellos: corregirlos, no compensarlo leyendo más.

---

## Ley de Dueño Único

Cada clase de hecho tiene **exactamente un archivo dueño**. Todo lo demás enlaza.

| Clase de hecho | Dueño único | Cómo lo referencia el resto |
|---|---|---|
| Requisitos de una feature | `specs/NNN-slug/spec.md` | `[[SPEC-NNN]]` |
| Diseño técnico | `specs/NNN-slug/plan.md` | `[[SPEC-NNN]]` |
| Pasos ejecutables | `specs/NNN-slug/tasks.md` | `[[SPEC-NNN]]` |
| Invariantes del proyecto | `.specify/memory/constitution.md` | cita textual, nunca copia |
| Significado de un término | `vault/Conceptos/<Término>.md` | `[[Término]]` |
| Por qué se decidió algo | **uno de dos**, según `gates.toml`: `vault/Decisiones/ADR-NNN.md` (un archivo por decisión, default; el título va en el frontmatter) **o** un único registro append-only declarado en `conventions.decisions_file` | `[[ADR-NNN]]` o `DE-NNN` |
| Qué specs existen y su estado | ficha `vault/Specs/SPEC-NNN.md` (nombre = ID exacto, para que `[[SPEC-NNN]]` resuelva) + fila en `vault/MOCs/00 - Indice de Specs.md` | `[[SPEC-NNN]]` |
| Nivel de madurez (`N0`–`N3` + límite) | columnas `Nivel`/`Limite` de `vault/MOCs/00 - Indice de Specs.md` (= `maturity_file` en `gates.toml`) | la ficha no lo repite |
| Fuente externa | `vault/Fuentes/<Título>.md` | `[[Título]]` |
| Estado actual | `STATE.md` (**se sobreescribe**) | nadie lo copia |
| Índice consultable | `graphify-out/` (derivado, gitignored) | — |

Rige **un solo** registro de decisiones por proyecto: si `decisions_file` está declarado, no se crean ADR sueltos (sería un segundo dueño). Donde esta skill dice `ADR-NNN`, léase la entrada del registro que rija.

> Corregido 2026-09-23: la fila de decisiones solo admitía ADR por archivo, contradiciendo el cambio de v0.2 que acepta un `decisiones.md` único. Ver CHANGELOG v0.2.1.

Tres prohibiciones, verificadas antes de cada escritura:

1. **No reescribir un hecho que ya tiene dueño.** Enlazarlo.
2. **No acumular archivos de estado.** `STATE.md` se sobreescribe. La historia va a un ADR inmutable.
3. **No citar `graphify-out/` como fuente de verdad.** Es un índice: apunta a `source_location`; la verdad está ahí.

Al escribir una ficha nueva, enlazar **de lo nuevo hacia lo viejo**. No reescribir fichas existentes para que apunten a la nueva, salvo que el enlace inverso sea necesario para la navegación.

### Archivos modulares: dividir por momento de lectura

Un documento del proyecto (`docs/`, `vault/`, `CLAUDE.md`) se divide cuando **supera ~200 líneas
y tiene partes que se leen en momentos distintos**. Es lo mismo que sacar una función del
programa principal: el índice dice cuándo leer cada pieza, y la pieza se abre sólo al llegar
ese momento.

- **El tamaño solo no alcanza.** Un archivo cohesivo de 250 líneas que siempre se lee entero se
  deja entero: partirlo agrega lecturas y abre la puerta a saltarse una parte.
- **Cada pieza tiene un solo índice que la enlaza** (`AGENT-INDEX.md`, un MOC o el documento
  padre), con el momento en que se lee. Una pieza que nadie enlaza no existe para el agente.
- **Las reglas que rigen siempre no se mueven a una pieza.** Se quedan en el archivo que se lee siempre.
- Un archivo de referencia de más de 100 líneas abre con un índice de sus secciones.
- En código, el límite de tamaño y de cohesión lo juzga `/thermos` (revisor de mantenibilidad).

Lo verifica `gates.py`: `DOC-SIZE` avisa si un documento pasa de `doc_max_lines` (200), y
`DOC-ORPHAN` avisa si una nota de `vault/` o `docs/` no la enlaza nadie. Los dos nacen en `warn`:
el tamaño no prueba que haya que partir, sólo pide mirarlo. `DOC-SIZE` mira por defecto `vault/`
y `CLAUDE.md`. Los documentos operativos de `docs/` (despliegue, arquitectura) se suman en
`doc_size_globs` de `gates.toml`. Los registros históricos no se suman: no se leen para operar.

---

## Orden de evidencia (compuerta, no preferencia)

Toda afirmación sustantiva declara su origen, en este orden y sin saltos:

| Etiqueta | Significa |
|---|---|
| `[EXT:NNN]` | referencia externa del registro de fuentes |
| `[INT:<ruta>]` | activo propio medido, con ruta |
| `[MEDIDO]` | verificado en este entorno, con fecha y comando |
| `[INT?]` | intuición |

**Regla de admisión:** una afirmación `[INT?]` **no sobrevive a un spec cerrado**. O una
sonda la convierte en `[MEDIDO]`, o se elimina. Lo no medido no se promete y no va a material
que otro vaya a leer como compromiso. Lo verifica `gates.py::G-REF`.

Además, confianza explícita en cada afirmación: `[Seguro]` / `[Probable]` / `[Adivinando]`.

## Regla de admisión de requisitos

**Un requisito sin test determinista o sin eval con dataset y umbral no es un requisito.**
Va al backlog y no se promete. Lo verifican `gates.py::G-EARS` (forma verificable) y
`gates.py::G-VERIF` (método de verificación declarado).

## Niveles de madurez, no estados binarios

Una pieza nunca está "abierta": está **cerrada en un nivel**.

| Nivel | Significa |
|---|---|
| `N0` | contrato escrito, nada implementado |
| `N1` | stub conforme **con límite falsable escrito** |
| `N2` | producción, un caso real |
| `N3` | producción, multi-caso |

Un `N1` sin una frase de límite refutable es una mentira, no un stub (`gates.py::G-N1`).
`G-N1` lee la tabla de `maturity_file`. Si tiene columnas `Nivel` y `Limite` las lee por nombre; si no (convención propia del proyecto), usa una heurística más débil.
Al mostrar el estado, se muestra la tabla completa con los `N1` a la vista.

## Correcciones con la cicatriz a la vista

Nunca edición silenciosa. Un cambio que contradice algo escrito antes deja marca:
`> Corregido AAAA-MM-DD: <qué cambió y por qué>` o `⚠️ SUPERSEDIDA por §X`.
Sin la cicatriz no hay forma de auditar por qué cambió una decisión, ni de distinguir
un cambio deliberado de un olvido.

---

## Ciclo de cierre (obligatorio al terminar cada fase)

Es lo que convierte al agente de productor en consumidor:

```bash
graphify update .                                    # 1. el grafo refleja lo recién escrito
graphify save-result --question "<pregunta guía>" \  # 2. el razonamiento queda en la memoria del grafo
                     --answer "<conclusión, 2-3 líneas>" \
                     --nodes "<nodo1>" "<nodo2>"
```

3. **Sobreescribir `STATE.md`** — nunca agregar un archivo nuevo de estado. Máximo 40 líneas: dónde estamos, spec activo, bloqueos, próximo paso.
4. Reportar en 3 líneas: qué se creó, qué se enlazó, qué sigue. El detalle está en los archivos.

---

## Reglas de honestidad

- Si el grafo no tiene la respuesta, decirlo y leer la fuente.
- Si un spec quedó superado, marcarlo `superseded` y decirlo. No borrarlo en silencio.
- Si `graphify update` falló, reportarlo: el grafo quedó viejo y lo que sigue es menos confiable.
- Si hay duplicación, nombrar los dos archivos concretos, no hablar en abstracto.
- Nunca `graphify export obsidian` ni `export wiki` sobre un proyecto gestionado por esta skill.
