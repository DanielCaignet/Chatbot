# CHANGELOG — full-autodev

Registro de cómo evoluciona la plantilla. **Append-only.** Una entrada revertida se
supersede con una nueva que referencia la anterior; no se edita ni se borra.

Cada entrada dice de dónde vino el cambio. La fuente más valiosa es un proyecto real que
resolvió algo mejor que la plantilla: eso se porta hacia acá, no al revés.

---

## 2026-09-29 · v0.5 — skill modular por momento de lectura, compuertas de tamaño y huérfanos

Origen: pedido del usuario. `SKILL.md` tenía 504 líneas y se cargaba entera en cada invocación.

- **División.** El núcleo (reglas que rigen siempre, ruteo y Ciclo de cierre) queda en
  `SKILL.md`. Cada momento tiene su archivo: `memoria.md`, `calidad.md`,
  `fase-0-bootstrap.md`, `fase-1-4-diseno.md`, `fase-5-implementacion.md` y `fase-6-retro.md`.
  El modo `--audit` se unió a `audit.md`. El texto se movió por rangos de líneas con un script,
  y se verificó que las 345 líneas con contenido quedaran todas. Punteros actualizados en
  `~/.claude/CLAUDE.md`, en `auditoria_obligatoria.py` (mensaje de «Costo de thermos») y en la
  plantilla de `bootstrap.ps1`.
- **Regla de archivos modulares** (núcleo, junto a la Ley de Dueño Único): dividir por momento de
  lectura, no por tamaño. Compuertas nuevas en `warn`: `DOC-SIZE` (> `doc_max_lines`, 200) y
  `DOC-ORPHAN` (nota de `vault/` o `docs/` sin enlace entrante).
  Medido en CristalChile-Maqueta: con `docs/` incluido, `DOC-SIZE` dio 17 avisos, casi todos de
  registros históricos, así que `docs/` quedó fuera por defecto y se suma por proyecto.
  `DOC-ORPHAN` dio 4 avisos plausibles.
- **Añadidos evaluados** (`calidad.md`, candidatos): protocolo de depuración en Fase 5, a partir
  de la idea de `systematic-debugging` de Superpowers; verificación de UI en el navegador del
  host antes de subir el nivel; cuatro invariantes por defecto de la constitución, a partir de
  las guías de Karpathy. `agent-browser` quedó como candidato **SIN REVISAR**, sin instalar.
  Superpowers completo y Supermemory quedaron descartados.
- Respaldo del estado anterior: `~/.claude/backups/full-autodev-2026-09-29/`.

## 2026-09-27 · v0.4.4 — anti-slop en cada modificación de código, escrito en la skill

Origen: el usuario lo recordó en CristalChile-Maqueta: la regla vivía en `~/.claude/CLAUDE.md` y
en el hook, pero la skill la ubicaba en «Cada commit», que se lee como algo que ocurre al final y
no con cada cambio.

### Cambiado
- Tabla de «Stack de calidad»: la fila del scanner dice **cada modificación de código**, antes de
  su commit, sin excepción por tamaño, urgencia ni tipo de cambio (arreglo, refactor, prueba, script).
- Fase 5, paso 1: el scanner corre sobre los archivos cambiados de cada modificación; un `high`
  introducido se corrige antes del commit, uno previo se reporta, y recién después se sella.

---

## 2026-09-26 · v0.4.3 — zona de impacto del delta y barrido de main

Origen: el usuario pidió cubrir el punto ciego de v0.4.2, donde un arreglo que rompe algo fuera
de su delta no lo ve esa ronda, y barrer la rama principal de vez en cuando.

### Añadido
- **Zona de impacto** en las rondas delta: el prompt lleva quién usa lo que tocó el arreglo
  (`graphify affected`, o un grep del nombre si el símbolo no está en el grafo). La lista del
  agente principal es complemento: comparte el punto ciego de quien escribió el arreglo.
- **Barrido de main** en `auditoria_obligatoria.py`. Con `BARRIDO_CADA = 5` PRs con código
  fusionados (commits de primer padre) desde el último barrido, el siguiente `gh pr merge` se
  bloquea hasta correr thermos sobre ese rango y sellar con `--sellar-thermos-main <commit>`. El
  bloqueo lista los archivos que en su PR sólo se auditaron en delta. La primera mirada anota la
  punta de main como inicio, así que la historia previa no se barre.

### Aprendido
- En CristalChile-Maqueta, `graphify affected` no encuentra funciones JS escritas dentro de
  strings de Python (`agDesdePartes` en `ui_plan.py`): el grafo AST no las ve. Ahí la zona de
  impacto sale de un grep.
- El conteo usa la copia local de main: sin fetch, cuenta de menos.

## 2026-09-26 · v0.4.2 — thermos incremental, revisores estáticos y modelo por etapa

Origen: el usuario reportó que thermos consumía demasiados tokens. Se midió en las
transcripciones del PR #54 de CristalChile-Maqueta: 33 corridas de revisor en un día (unas 16
rondas sobre el mismo PR). El revisor de bugs en Opus llegaba a 64–92 turnos y hasta 9.4M tokens
leídos de caché por corrida. Hacía hasta 45 llamadas a Bash: ejecutaba las suites del proyecto,
escribía scripts de prueba propios y rehacía el diff de todo el rango. Los prompts de thermos
suman unos 20 KB y el contexto inicial de cada revisor ronda los 27–30k tokens: no eran la causa.

### Cambiado
- **Sello de thermos incremental** en `auditoria_obligatoria.py`. `--sellar-thermos [PR] --delta`
  sella una ronda que auditó sólo el delta desde el último commit sellado del PR, y
  `--base-thermos [PR]` imprime qué auditar. Se encadenan hasta `MAX_DELTAS = 3` deltas; el
  siguiente exige completo. La base se busca sólo entre los commits del PR (`rev-list cabeza --not
  origin/<base>`). Si desde el último sello sólo cambió prosa del PR, el merge pasa sin otra ronda.
  El formato del sello admite `<commit> delta <base>`; las líneas viejas (sólo el commit) siguen
  valiendo como completo.
- **Modelo por etapa** (`~/.claude/CLAUDE.md`, «Costo de thermos»): el revisor de calidad corre
  siempre en Sonnet. El de bugs corre en Opus sólo si el PR deja algún spec en `N2`+ según el MOC
  de su cabeza; si no, en Sonnet. Un proyecto sin MOC de niveles cuenta como `N2`+. Resuelve el
  pendiente de v0.4.1 en su parte de regla; la compuerta sigue en `BACKLOG.md`.
- **Revisores estáticos**: el prompt les pasa el diff, los archivos, el log y el resultado de los
  tests, y les prohíbe ejecutar código del proyecto o rehacer el diff. Se aplica desde el prompt
  del agente principal (el paso 5 de thermos admite reglas de la casa), sin tocar el plugin fijado.

### Aprendido
- Un primer intento tomaba como base del delta el sello del PR #52, que había llegado a la rama
  por main. Por eso la base se limita a los commits propios del PR.
- La definición del subagente de bugs dice «prefer static reading», y en Opus no alcanza: la
  prohibición tiene que ir explícita en el prompt.

## 2026-09-24 · v0.4.1 — modelo por revisor de thermos y backlog del stack

Origen: pedido del usuario para bajar el costo de los subagentes de thermos, que gastan más
que el chat principal.

### Cambiado
- **Modelo de los revisores de thermos**, en `~/.claude/CLAUDE.md` (sección de auditoría):
  `thermo-nuclear-code-quality-review-subagent` corre con Sonnet 5 y `thermo-nuclear-review-subagent`
  (bugs y seguridad) con Opus. Se aplica con el parámetro `model` de la llamada a Agent, sin tocar
  el plugin fijado. Es una prueba de costo: si el revisor en Sonnet devuelve hallazgos pobres, se
  dice en la síntesis.

### Añadido
- **`references/BACKLOG.md`**, para los pendientes del stack que no son de un proyecto.

### Pendiente
- **Elegir el modelo de los revisores según la etapa del proyecto** (Sonnet en `N0`/`N1`, Opus en el
  revisor de bugs para subir a `N2`+). Detalle y criterio de cierre en `BACKLOG.md`.

### Aprendido
- **Los subagentes de thermos no pueden usar context-mode.** Declaran una lista cerrada de
  herramientas (`Read, Grep, Glob, Bash, Skill` y `WebFetch` en el de bugs), sin `ToolSearch` ni
  `ctx_*`. Igual reciben el bloque de ruteo que context-mode agrega a todo prompt de Agent, que
  les pide cargar `ctx_*`: ese bloque gasta tokens sin efecto.
- Se probó darles context-mode con una copia de usuario de cada subagente en `~/.claude/agents/`.
  El usuario la descartó y se revirtió el mismo día. Las definiciones de subagente se cargan al
  arrancar la sesión, así que la copia no llegó a probarse.

## 2026-09-23 · v0.4 — vault que resuelve, grafo semántico en Antigravity, auditoría con el stack

Origen: segunda vuelta en CristalChile. El usuario señaló tres cosas: que no veía nada en
Obsidian, que una sola spec no era lo esperado de Spec Kit, y que faltaba auditar con las
herramientas del stack.

### Corregido
- **Los enlaces del vault no resolvían desde la v0.1** `[MEDIDO: 86 enlaces rotos]`. La plantilla
  nombraba las fichas `SPEC-NNN-<slug>.md` y `ADR-NNN-<slug>.md`, pero las enlazaba `[[SPEC-NNN]]`.
  Obsidian y graphify resuelven por el nombre exacto del archivo. Ahora las fichas se llaman con
  su ID exacto (`SPEC-NNN.md`, `ADR-NNN.md`) y el título va en el frontmatter.
- **`-NoSpecKit` se aplicó a un repo cuya "convención" era una sola spec.** Ahora el criterio está
  en la Fase 0: la convención tiene que ser una spec por feature.
- **graphify no estaba fijado a una versión.** Una reinstalación lo subió de 0.9.65 a 0.9.67.
  `stack.ps1` ahora instala `graphifyy[mcp]==0.9.67`.
- **`graphify-mcp` respondía `--help` pero no arrancaba**, porque faltaba el extra `[mcp]`. Con el
  extra, `tools/list` devuelve 10 herramientas `[MEDIDO]`.

### Añadido
- **`gates.py::WIKI-DANGLING`:** todo `[[enlace]]` de `vault/`, `specs/` y `STATE.md` tiene que
  resolver a una nota. Ignora plantillas y código.
- **Grafo semántico con Antigravity**, por regla del usuario. `stack.ps1` instala la skill con
  `graphify install --platform antigravity`. Claude solo corre el AST.
- **Auditoría con el stack** como paso real, con cuatro revisores en paralelo y en solo lectura:
  - thermos, correctitud;
  - thermos, calidad;
  - slop-detector;
  - anti-slop:audit + antislop-human + check_contrast + scanner.

  Los hallazgos se escriben junto a la spec que afectan, no quedan en el chat.

### Aprendido
- Un efecto lateral a vigilar: `graphify install --platform claude` **reescribe una línea del
  `~/.claude/CLAUDE.md` global del usuario**. Se restauró a mano. Ninguna herramienta del stack
  debería tocar las instrucciones del usuario sin avisar.
- La auditoría encontró que la pantalla de la demo citaba un correo inexistente («16-09»). Es el
  mismo tipo de falla que motivó ADR-001: afirmar lo que dijo el cliente sin citarlo. Candidata a
  compuerta determinista: toda fecha o `§` citada en `src/` debe existir en `cliente/Correos Pablo.md`.

---

## 2026-09-23 · v0.3.2 — aprendido montando CristalChile-Maqueta

Origen: primer montaje sobre un proyecto real con historia (77 commits). Allí se perdieron dos
semanas replicando un tablero que el cliente había descrito por escrito como «solo una
referencia inicial y no un diseño definitivo».

### Añadido
- **Regla "la referencia antes que la memoria"** en el manual `CLAUDE.md` del bootstrap. Lo que
  pide el cliente se cita del registro `REFERENCIAS.md`; sin cita es `[INT?]`.
- **`markitdown` en `stack.ps1`.** Estaba como skill pero no estaba instalado. Límite
  `[MEDIDO]`: no lee PDFs de "Microsoft: Print To PDF", que no tienen capa de texto. En ese
  caso hay que transcribir.
- **`claude-thermos` en `stack.ps1`**, fijado a `2b030cd` y revisado (único destino
  `api.anthropic.com`, log solo de metadatos).
- **`gates.py`:** `slop_exclude` saca de `SLOP-SCAN` los artefactos de terceros. Antes el
  tablero HTML del cliente disparaba 14 `innerHTML`.

### Corregido
- `STATE-SPRAWL` no veía `TRASPASO.md` porque sus patrones estaban solo en inglés. Se agregó
  `*traspaso*.md` a los defaults.
- El `specs_glob` por defecto (`specs/`) daba 0 specs en un repo con `spec/`. **El bootstrap no
  lo detecta todavía:** con `-NoSpecKit` debería inferir el directorio real de specs. Queda pendiente.

### Aprendido, no portado
- CristalChile tiene más de 30 puertas propias en `src/gates.py`, más finas que las de la
  plantilla (`G-PARIDAD`, `G-CERO-HARDCODE`, `G-DEMO`…). Se conservan tal cual. Candidata a
  portar: `G-PARIDAD`, que exige "nunca menos que lo que el cliente ya tiene".

---

## 2026-09-23 · v0.3.1 — stack instalado de verdad, sin descartes unilaterales, con revisión de seguridad

Origen: tres correcciones del usuario sobre v0.3.

### Corregido

- **v0.3 descartó plugins sin consultar.** El usuario pidió montar "anti-slop" y "thermos";
  había seis repos con esos nombres y la v0.3 eligió dos. Esa decisión era del usuario. Además,
  según el usuario, esos plugins resuelven problemas que tiene hoy en proyectos reales.
  **Regla nueva: ante homónimos no se descarta nada sin razones concretas presentadas antes.**
  Ahora quedan instalados los cuatro anti-slop y thermos.
- **La plantilla documentaba herramientas sin instalarlas.** Nuevo `references/stack.ps1`,
  que verifica e instala los CLIs (graphify, graphify-mcp, Spec Kit vía `uv tool`) y los seis
  plugins. El bootstrap lo corre antes de montar nada (`-NoStack` lo salta). Nunca actualiza
  lo que ya está.

### Añadido

- **Commits revisados fijados** en `stack.ps1`. Un plugin en otro commit se reporta como
  SIN REVISAR, porque una skill es texto que el agente obedece.
- **Revisión de contenido malicioso** además de la de código. Se escanearon skills, agentes,
  referencias y archivos sin extensión de los cinco plugins nuevos buscando:
  - instrucciones de anulación u ocultamiento;
  - destinos de exfiltración;
  - lectura de secretos o de configuración;
  - unicode invisible;
  - comentarios HTML.

  `[MEDIDO]` 2026-09-23: sin anulaciones, exfiltración ni unicode oculto. Los comentarios HTML
  son solo marcadores. Hallazgos que no son maliciosos pero hay que conocer:
  - luantaraschi: hook SessionStart con "do not mention this note to the user"; la nota solo
    rutea a sus skills;
  - miqdadbadjuber: un wizard que propone, con aprobación, escribir un bloque en el `CLAUDE.md`
    del proyecto;
  - paslavskyi: un hook Stop con `decision: block`, y el tier A de `deslop`, que borra sin reportar.
- **Choque de nombres** `[MEDIDO]`: TheMizeGuy, luantaraschi y miqdadbadjuber declaran el
  marketplace `anti-slop`, y Claude Code rechaza el segundo. Solución: una copia local fijada
  al commit, con solo `name` renombrado y `skip-worktree` para que `git pull` no lo pise.

### Pendiente de decisión

- **`izeigerman/claude-thermos`, no instalado a la espera de un sí explícito.** Razones concretas:
  1. No es un plugin. Es un paquete de Python (`mitmproxy`, `click`, `httpx`) que corre un
     proxy local, y Claude Code tiene que lanzarse con `ANTHROPIC_BASE_URL` apuntando a él.
     **Todo** el tráfico, con el token de sesión, pasa por código de terceros.
  2. Mientras el agente principal espera a un subagente, envía cada 270 s una petición de
     calentamiento con el prompt completo. Cuesta lecturas de caché a cambio de evitar la
     reescritura (1,25x).
  3. Solo actúa donde el caché dura 5 minutos. Esta sesión de escritorio usa 1 hora; en CLI
     con otra cuenta o configuración puede ser distinto `[INT?]`.

---

## 2026-09-23 · v0.3 — stack de calidad (anti-slop + thermos) y context-mode como regla dura

Origen: pedido del usuario. Quería sumar a la plantilla "anti-slop" y "thermos" y
convertir en regla el uso de context-mode, que se venía salteando.

### Selección (había homónimos)

Se clonaron y revisaron los siete candidatos: hooks, scripts, red y licencia.

- **Adoptado:** `TheMizeGuy/anti-slop` v2.4.0. MIT, sin hooks, sin red (el dashboard escucha
  en 127.0.0.1 y solo arranca a mano). Cubre prosa, código, UI y seguridad, y trae un
  scanner determinista sin dependencias que encaja como compuerta de `gates.py`.
- **Adoptado:** `theocarranza/thermos-claude` v1.0.0. MIT, solo markdown (skills y agentes). Es
  un port de `cursor/plugins/thermos`: las rúbricas quedan intactas (1 línea de diff en cada
  una) y solo se adaptaron el orquestador y los agentes al harness de Claude.
- **Descartado:** `izeigerman/claude-thermos`. No revisa código: es un proxy local que calienta
  el caché de la API, y además intercepta el tráfico.
- **Descartado:** `paslavskyi/anti-slop`. Su hook Stop devuelve `decision: block` en cada turno
  con ≥30 líneas cambiadas y se superpone con `/thermos`. Su skill `drilling-design-problems`
  vale la pena mirarla aparte.
- **No evaluados a fondo:** `luantaraschi/anti-slop` (UI y prosa, con hook SessionStart) y
  `miqdadbadjuber/anti-slop` (reglas + MCP de contraste en Python). Más angostos para un
  flujo de desarrollo general.

### Añadido

- **`gates.py::SLOP-SCAN`**: corre `slop-scanner.mjs` sobre los archivos cambiados (staged,
  no staged y no rastreados, sin borrados), en lotes de 50. El plugin instalado se
  autodetecta; `conventions.slop_scanner`, `slop_fail_on` (default `high`) y `slop_exts`
  lo configuran. Sin plugin o sin node emite `warn` y nunca bloquea.
- **SKILL.md: "Herramientas de lectura: context-mode siempre"**. Leer, buscar y hacer diff
  pasan por `ctx_*`; Bash, Read y Grep quedan para mutar o para leer lo que se va a editar.
- **SKILL.md: "Stack de calidad"**, con qué corre en cada momento. La Fase 5 ahora pide
  `gates.py` → `/slop-check diff` → `/thermos` (este último para `N2`+ o antes de un merge).
- **`bootstrap.ps1`**:
  - `gates.toml` con `SLOP-SCAN` activado en `warn`.
  - `.anti-slop/` en `.gitignore`.
  - Manual `CLAUDE.md` con las secciones de context-mode y del stack.

### Decidido

- `SLOP-SCAN` nace en `warn` y no en `block`. Es un regex sobre código ajeno a la plantilla,
  así que su tasa de falsos positivos en cada proyecto es `[INT?]` hasta que `--stats` la mida.
  Se promueve por proyecto en `gates.toml`.

### Verificado

- `[MEDIDO]` 2026-09-23: los dos plugins quedaron instalados en scope `user` y habilitados
  según `claude plugin list`.
- `[MEDIDO]` 2026-09-23: se corrió bootstrap con git en una carpeta desechable y después
  `gates.py --gate SLOP-SCAN`. Resultados:

  | Caso | Resultado |
  |---|---|
  | Árbol limpio | 0 hallazgos |
  | `eval()` en un `.py` no rastreado | 1 `high` con archivo, línea y fix |
  | Severidad `block` | exit 1 |
  | Scanner inexistente | `warn`, exit 0 |

### Pendiente

- Los proyectos ya montados no reciben la sección de `gates.toml` ni la del manual: el
  bootstrap nunca sobreescribe. Se agregan a mano.

---

## 2026-09-23 · v0.2.2 — el nivel de madurez tiene un solo dueño y G-N1 queda armada

Origen: revisión de v0.2.1. Resuelve su **Pendiente** y corrige un error suyo.

### Corregido

- **v0.2.1 duplicaba el nivel.** Ponía `nivel:` en la ficha `SPEC-NNN` **y** en el MOC: dos
  dueños del mismo hecho, y además `G-N1` no leía ninguno de los dos (lee `maturity_file`).
  Ahora el dueño único es la fila del MOC, columnas `Nivel` y `Limite`. La ficha no lo lleva.
- **`bootstrap.ps1`** (resuelve el Pendiente de v0.2.1):
  - `_TEMPLATE-SPEC.md`: `status: vigente | superseded`, con nota de que el nivel vive en el MOC.
  - MOC de specs: columnas `Nivel` y `Limite`, con la definición N0–N3 en la cabecera.
  - Manual `CLAUDE.md`: fila de decisiones con las dos variantes, fila nueva de madurez.
  - `gates.toml`: `maturity_file` apunta al MOC y `G-N1` pasa a `enabled = true, severity = "block"`.
    Antes estaba declarada y apagada: una compuerta que no existía.

### Cambiado

- **`gates.py::G-N1` lee por columna.** Si la tabla tiene encabezados `Nivel` y `Limite`
  (con o sin tilde), toma el nivel y el límite de esas columnas. Si no, cae a la heurística
  anterior, para proyectos con convención propia (Agent Engine). La heurística tenía dos
  fallas que la lectura por columna elimina:
  - falso negativo: un título de 6+ palabras contaba como límite;
  - falso positivo: un `N1` mencionado en el título se tomaba como el nivel.
  Detecta tablas separadas en un mismo archivo y reinicia el mapeo de columnas en cada una.

### Verificado

- `[MEDIDO]` 2026-09-23: `gates.py --gate G-N1` sobre un MOC sintético con los casos
  título largo sin límite (dispara), N1 con límite (pasa), N1 en título con Nivel N2 (pasa)
  y segunda tabla sin encabezados (heurística, dispara). Exit 1 como se espera.
- `[MEDIDO]` 2026-09-23: `bootstrap.ps1 -NoSpecKit -NoGit` en carpeta desechable + `gates.py`:
  sin hallazgos de G-N1, solo `GRAPH-MISSING` (esperado en proyecto recién montado), exit 0.

### Sin tocar

- Los proyectos ya montados conservan su `gates.toml` y su MOC: el bootstrap nunca
  sobreescribe. Para adoptar v0.2.2 hay que agregarles a mano las columnas y `maturity_file`.

---

## 2026-09-23 · v0.2.1 — coherencia interna de SKILL.md con v0.2

Origen: revisión del propio `SKILL.md`. v0.2 cambió dos reglas en el CHANGELOG pero dejó
el texto operativo con las reglas viejas; un agente que siguiera las fases al pie de la
letra deshacía v0.2.

### Corregido

- **Fase 3, paso 6:** la ficha `SPEC-NNN` llevaba `status` como avance. Ahora lleva
  `nivel: N0` (madurez) y `status: vigente | superseded` (solo si rige). El MOC de specs
  gana columna `Nivel`.
- **Fase 5, paso 3:** cerraba con `status: done`. Ahora corre `gates.py` antes de subir el
  nivel, exige frase de límite para `N1` y evidencia de producción para `N2`/`N3`.
- **Ley de Dueño Único, fila de decisiones:** solo admitía ADR por archivo. Ahora admite
  ADR por archivo (default) **o** un registro único vía `conventions.decisions_file`, con
  la regla de que rige uno solo por proyecto.

### Pendiente

- `references/bootstrap.ps1` sigue generando `_TEMPLATE-SPEC.md` con
  `status: draft | active | done | superseded`, y el MOC de specs sin columna `Nivel`.
  Todo proyecto nuevo nace con la regla vieja hasta que se corrija.

---

## 2026-09-22 · v0.2 — portado desde Agent Engine (DataSeed)

Origen: `D:\Dataseed\Agent Engine`. El proyecto tenía una convención **más rigurosa** que
la plantilla v0.1 en cuatro ejes. Se portaron los cuatro.

### Añadido

- **Orden de evidencia como compuerta** (de su artículo A8). Antes la plantilla pedía
  "no rellenar con memoria" como buena intención. Ahora es una jerarquía explícita
  — `[EXT:NNN]` → `[INT:<ruta>]` → `[INT?]` — con una **regla de admisión**: una afirmación
  `[INT?]` no sobrevive a una spec cerrada. O una sonda la convierte en `[MEDIDO]`, o se elimina.
  Verificable por `gates.py::G-REF`.

- **"Un requisito sin test o eval no es un requisito"** (de A9). La plantilla v0.1 no tenía
  regla de admisión para requisitos: aceptaba cualquier cosa escrita en un spec. Ahora
  `G-EARS` exige forma verificable y `G-VERIF` exige método de verificación declarado.

- **Niveles de madurez con límite falsable escrito** (de A11). Reemplaza al
  `status: draft|active|done`, que era binario y mentía: una capa nunca está "abierta",
  está **cerrada en un nivel**. Un stub sin límite declarado es una mentira, no un stub.

- **Correcciones con la cicatriz a la vista.** Nunca edición silenciosa: un bloque
  `> Corregido AAAA-MM-DD` o `⚠️ SUPERSEDIDA por §X`. La plantilla v0.1 permitía
  sobreescribir sin dejar rastro, lo que hace imposible auditar por qué cambió una decisión.

- **`gates.py`**: las compuertas dejan de ser prosa en `audit.md` y pasan a ser un script
  determinista, sin LLM, configurable por proyecto vía `gates.toml`. Exit 1 en severidad
  `block`, enganchable en `pre-commit`.

- **Fase 6 — Retroalimentación**: `.gates/history.jsonl` + `.gates/feedback.md` +
  `gates.py --stats`. Detecta reglas muertas, regresiones y falsos positivos, y define
  cómo un aprendizaje local se promueve a la plantilla.

### Cambiado

- El registro de decisiones deja de ser obligatoriamente un archivo por ADR. Agent Engine
  usa un único `decisiones.md` append-only compartido entre proyectos hermanos, y para ese
  caso es mejor: una sola memoria, sin bifurcación. La plantilla ahora soporta ambos y
  `gates.toml` declara cuál rige.

### Aprendido, no portado

- Agent Engine **no usa Spec Kit** y está mejor así: su flujo
  `REFERENCIAS → DE- → SPEC-E → evals → tareas → implementación` ya es desarrollo dirigido
  por especificación, con compuertas más duras. Lección para la plantilla: **Spec Kit es
  opcional.** Si el proyecto ya tiene una convención de specs viva, imponerle
  `specs/NNN-slug/` es duplicación estructural, no una mejora.

---

## 2026-09-22 · v0.1 — versión inicial

Origen: investigación sobre [vaultmem](https://github.com/jayantak/vaultmem),
[obsidian-agent-memory-skills](https://github.com/adamtylerlynch/obsidian-agent-memory-skills),
[VaultForge](https://github.com/alphakeeer/VaultForge) y
[Spec Kit](https://github.com/github/spec-kit).

- Ley de Dueño Único y las tres prohibiciones.
- Presupuesto de orientación: 2 archivos, ~100 líneas (de obsidian-agent-memory-skills).
- Clases de lint nombradas con "por qué importa", separando `ORPHAN` de `UNINDEXED`
  (de vaultmem).
- Bootstrap idempotente con escaneo previo `fresh | incremental | skip` (de VaultForge).
- Enlaces nuevo→viejo: no reescribir fichas existentes.
- Prohibición de `graphify export obsidian`: el vault se escribe, el grafo se deriva.
