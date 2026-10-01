# Contrato de auditoría — `/full-autodev --audit`

> Se carga desde `SKILL.md` en `--audit`. Primero lo determinista (`gates.py`), después el contrato semántico.

Secciones: Modo `--audit` (compuertas de `gates.py`) · Las dos fallas que motivan esta skill ·
Clases (encontrabilidad, consistencia, duplicación, frescura) · Cómo se corre · Formato del reporte.

## Modo `--audit`

**Lo determinista primero, y es un script, no un juicio mío:**

```bash
python "$env:USERPROFILE\.claude\skills\full-autodev\references\gates.py"
python "$env:USERPROFILE\.claude\skills\full-autodev\references\gates.py" --json   # para encadenar
```

Sin LLM, sin red. Exit 1 si dispara una compuerta con `severity = "block"`, lo que la hace
enganchable en `pre-commit` y en CI. Las compuertas y su severidad se declaran en `gates.toml`
del proyecto; si no existe, se usan los valores por defecto de `gates.py`.

Cubre: `G-REF`, `G-EARS`, `G-VERIF`, `G-N1`, `TRAZA`, `REF-DANGLING`, `DE-DANGLING`,
`STATE-SPRAWL`, `GRAPH-MISSING`, `DERIVED-COMMITTED`, `SLOP-SCAN`, `WIKI-DANGLING`,
`DOC-SIZE`, `DOC-ORPHAN`.

`SLOP-SCAN` nace en `warn`: se promueve a `block` en `gates.toml` cuando `--stats` muestre
que no da falsos positivos en ese proyecto. Si falta el plugin o `node`, avisa y nunca bloquea.

**Lo semántico después**, que sí requiere el grafo y criterio (contrato completo más abajo):

- `DUP-CANDIDATE` / `FACT-SPRAWL` — dos archivos describiendo el mismo hecho.
- `SPEC-UNINDEXED` / `ORPHAN` — el spec existe pero el agente no lo encuentra.
- `GRAPH-STALE` — `graphify check-update .`

Reportar con la corrección concreta al lado. **No corregir sin que el usuario lo pida.**

Si una compuerta se puede escribir como parseo determinista, **va a `gates.py`, no a la prosa
de `audit.md`**. Una compuerta declarada y no armada es una compuerta que no existe.

---


Clases de hallazgo nombradas y verificables. El modelo viene de [vaultmem](https://github.com/jayantak/vaultmem), que separa dos fallas que suelen confundirse: una nota puede ser alcanzable por el grafo pero invisible para las superficies de triaje, y viceversa.

La auditoría **no corrige**. Reporta y propone. Corregir solo si el usuario lo pide.

---

## Las dos fallas que motivan esta skill

| Falla del usuario | Clase que la detecta |
|---|---|
| "olvidaste un spec" | `SPEC-UNINDEXED`, `SPEC-NOCARD`, `INDEX-DRIFT` |
| "duplicaste documentación" | `DUP-CANDIDATE`, `FACT-SPRAWL`, `STATE-SPRAWL` |

---

## Clases

### Encontrabilidad

| Clase | Dispara cuando | Por qué importa |
|---|---|---|
| `SPEC-NOCARD` | existe `specs/NNN-slug/` sin su ficha `vault/Specs/SPEC-NNN-*.md` | el spec existe en disco pero no es un nodo del grafo: solo se encuentra por búsqueda textual, nunca por traversal ni por el índice |
| `SPEC-NODIR` | existe una ficha `SPEC-NNN` cuyo `spec_path` no resuelve | la ficha promete un spec que no está; el agente planifica contra algo inexistente |
| `SPEC-UNINDEXED` | la ficha no aparece en `vault/MOCs/00 - Indice de Specs.md` | no tiene punto de entrada curado — **esta es la clase de "olvidé un spec"** |
| `ORPHAN` | una ficha con cero `[[enlaces]]` entrantes desde cualquier otro archivo | nada en el grafo lleva ahí; es inalcanzable por `query`, `path` o `affected` |
| `MOC-STALE` | un MOC cuyo `actualizado:` es anterior a la ficha más nueva que debería listar | el índice quedó atrás de la realidad |

### Consistencia

| Clase | Dispara cuando | Por qué importa |
|---|---|---|
| `MISSING-FM` | frontmatter requerido ausente — spec: `id`,`status`,`spec_path`; adr: `id`,`status`,`fecha`; concepto: `titulo` | el resto del flujo lee estos campos directo y trata la ausencia como vacío silencioso |
| `INDEX-DRIFT` | el `status` de la fila en el MOC discrepa del `status:` del frontmatter de la ficha | el índice miente sobre el estado; se planifica sobre un spec dado por cerrado que sigue abierto |
| `ADR-MUTATED` | un ADR con `status: accepted` cuyo contenido cambió respecto del último commit | los ADR son inmutables; si la decisión cambió corresponde un ADR nuevo con `supersedes:` |
| `SUPERSEDE-DANGLING` | `supersedes: [X]` donde `X` no existe, o `X` no quedó marcado `superseded` | la cadena de supersesión está rota; quedan dos specs vigentes para lo mismo |

### Duplicación

| Clase | Dispara cuando | Por qué importa |
|---|---|---|
| `DUP-CANDIDATE` | dos fichas cuyos vecindarios en el grafo se solapan por encima del umbral | **esta es la clase de "duplicaste documentación"**: dos archivos describiendo el mismo hecho |
| `FACT-SPRAWL` | un mismo término se define en más de una ficha (definición, no mención) | viola la Ley de Dueño Único; las definiciones divergen con el tiempo |
| `STATE-SPRAWL` | existe más de un archivo de estado: `STATE.md` más cualquier `*handoff*`, `*estado*`, `*context*` numerado fuera de `vault/Decisiones/` | `STATE.md` dejó de sobreescribirse y volvió a ser un log. Es la patología exacta que produjo `06_`, `18_` y `21_` duplicados en el corpus de Candidatura |
| `DERIVED-COMMITTED` | `graphify-out/` versionado en git | un índice derivado en el repo genera conflictos de merge y se lee como fuente |

### Frescura

| Clase | Dispara cuando | Por qué importa |
|---|---|---|
| `GRAPH-STALE` | `graphify check-update .` reporta re-extracción pendiente | las consultas al grafo responden sobre una foto vieja, sin avisar |
| `GRAPH-MISSING` | no existe `graphify-out/graph.json` | la puerta de consumo no puede cerrarse; el agente vuelve a leer fuentes en bloque |

---

## Cómo se corre

```bash
# frescura
graphify check-update .

# encontrabilidad y duplicación: por cada spec activo
graphify query "<titulo del spec>"
graphify affected "<concepto central del spec>"
```

Lo estructural (`SPEC-NOCARD`, `SPEC-NODIR`, `SPEC-UNINDEXED`, `MISSING-FM`, `INDEX-DRIFT`, `STATE-SPRAWL`, `DERIVED-COMMITTED`) se resuelve leyendo frontmatter y listando directorios — barato, sin LLM. Correrlo primero.

`DUP-CANDIDATE` y `FACT-SPRAWL` requieren el grafo. Correrlos después, y solo sobre specs con `status: active` o `draft`.

---

## Formato del reporte

Una línea por hallazgo, agrupado por clase, con la corrección concreta al lado:

```
DUP-CANDIDATE (2)
  vault/Conceptos/Autenticación.md ⇄ vault/Conceptos/Auth.md
    → fusionar en Autenticación.md; dejar Auth.md como alias en el frontmatter
  vault/Specs/SPEC-004-login.md ⇄ vault/Specs/SPEC-007-sesiones.md
    → solapan en [[Token de sesión]]; decidir dueño y enlazar desde el otro

SPEC-UNINDEXED (1)
  vault/Specs/SPEC-006-export.md
    → agregar fila en vault/MOCs/00 - Indice de Specs.md
```

Sin hallazgos: decirlo en una línea. No inventar trabajo.
