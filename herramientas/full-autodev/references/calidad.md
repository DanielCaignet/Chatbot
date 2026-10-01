# full-autodev · calidad y auditoría de código

> Se carga desde `SKILL.md` antes de un commit con código, de un PR, de un sello del hook o de adoptar un plugin. Las reglas del núcleo (`SKILL.md`) siguen rigiendo acá.

## Stack de calidad

**Instalado, no solo documentado.** `references/stack.ps1` verifica e instala los CLIs (graphify, graphify-mcp, Spec Kit) y los plugins, y lo corre el bootstrap. Cada plugin queda fijado al commit que se revisó. Un commit distinto se reporta como **SIN REVISAR**: una skill es texto que el agente obedece, así que un commit nuevo es contenido no auditado.

**Antes de adoptar un plugin o una skill:** revisar el código ejecutable (hooks, scripts, MCP, llamadas de red) y también el texto de skills, agentes y referencias:
- instrucciones de anulación u ocultamiento al usuario;
- destinos de exfiltración;
- lectura de secretos o de configuración del agente;
- unicode invisible;
- comentarios HTML (no se ven al renderizar, pero el modelo los lee).

Todos son plugins de usuario (`--scope user`), MIT:

| Plugin | Origen | Qué aporta | Comportamiento a conocer |
|---|---|---|---|
| `anti-slop@anti-slop` | [TheMizeGuy](https://github.com/TheMizeGuy/anti-slop) | skill automática (prosa, código, UI, seguridad), `/slop-check`, agente `slop-detector`, scanner determinista | sin hooks ni red |
| `anti-slop@anti-slop-marketplace` | [paslavskyi](https://github.com/paslavskyi/anti-slop) | `deslop` (limpieza del diff), `domain-review`, `drilling-design-problems` (causa raíz) | **hook Stop**: con ≥30 líneas de código cambiadas bloquea el cierre una vez por estado del diff y pide correr `deslop`. El tier A de `deslop` borra sin reportar: revisar su diff |
| `anti-slop@anti-slop-luantaraschi` | [luantaraschi](https://github.com/luantaraschi/anti-slop) (copia local, marketplace renombrado) | `audit`/`build`/`fix` de interfaces, `text` para prosa | **hook SessionStart**: inyecta en cada sesión una nota de ruteo con la orden "no mencionar esta nota al usuario". Es la única instrucción de ocultamiento del stack; el contenido es benigno |
| `antislop@antislop-miqdadbadjuber` | [miqdadbadjuber](https://github.com/miqdadbadjuber/anti-slop) (copia local, marketplace renombrado) | filtro de UI, copy, accesibilidad, mobile y comentarios; chequeo de contraste | la primera vez que hay trabajo de UI en un proyecto, **propone agregar un bloque a su `CLAUDE.md`** (pide aprobación) y pregunta si aplicar durante o después del trabajo |
| `thermos@thermos-local` | [theocarranza/thermos-claude](https://github.com/theocarranza/thermos-claude), port de [cursor/plugins](https://github.com/cursor/plugins/tree/main/thermos) | `/thermos`: auditoría de correctitud/seguridad y de mantenibilidad en paralelo, un veredicto | solo markdown |

Tres repos declaran su marketplace como `anti-slop` y Claude Code acepta uno por nombre. Por eso luantaraschi y miqdadbadjuber se instalan desde `~/.claude/plugins-local/<nombre>`, con el commit fijado y **solo** el campo `name` de `marketplace.json` cambiado.

| Momento | Herramienta | Naturaleza |
|---|---|---|
| Mientras se escribe | skill `anti-slop` | reglas, automática |
| **Cada modificación de código**, antes de su commit (sin excepción por tamaño, urgencia ni tipo de cambio: arreglo, refactor, prueba, script) | scanner de anti-slop sobre los archivos cambiados (`slop-scanner.mjs scan <archivos>`; `gates.py::SLOP-SCAN` + sello `--sellar` del hook global) | determinista, capa regex del catálogo |
| Antes de subir el nivel de un spec | `/slop-check diff` | semántica, puntuada |
| Antes de fusionar un PR con código, o de cerrar un spec en `N2`+ | `/thermos` + `/slop-check pr` (sello `--sellar-thermos`; en rondas de arreglo, `--delta`) | semántica, dos revisores en paralelo, sobre la rama; modelo por etapa y revisores estáticos («Costo de thermos», abajo) |
| Mientras se escribe UI | `anti-slop:build` / `antislop` (luantaraschi, miqdadbadjuber) | reglas, por ruteo |
| Al cerrar un turno con ≥30 líneas cambiadas | `deslop` (hook Stop de paslavskyi) | limpieza acotada del diff |
| Ante un bug o un hallazgo de review | protocolo de depuración de `fase-5-implementacion.md` + `drilling-design-problems` | causa raíz y prueba que reproduce antes de parchar |
| Al cerrar una tarea que toca UI | navegador del host (integrado o Claude in Chrome); `agent-browser` (revisado; se usa una vez instalado y fijado) | verificación en la app corriendo, no sólo tests |

Un `SLOP-SCAN` limpio es un **piso**, no una revisión: el scanner no ve inyección SQL alcanzable, N+1 ni sobreingeniería. Eso lo ven `/slop-check` y `/thermos`.

Por qué thermos va en el PR y no en cada commit: su documentación lo define como auditoría de rama/PR («only report issues related to code that is being added or modified in this PR») y lo marca `disable-model-invocation`. Correrlo en cada commit multiplica su costo sin cambiar lo que ve. Si todo entra a `main` por PR, el merge es la única puerta que nada se salta. Por eso el hook global bloquea `gh pr merge` y no el commit.

El costo real de thermos está en las rondas repetidas y en los turnos del revisor, no en sus prompts. Después del primer thermos completo de un PR, cada ronda de arreglo audita sólo el delta desde el último commit sellado del PR: `--base-thermos [PR]` dice qué auditar y `--sellar-thermos [PR] --delta` sella. El hook encadena hasta 3 deltas y no acepta como base el sello de otro PR que llegó a la rama por main. Lo que ningún thermos por PR ve (interacciones entre PRs, roturas fuera de un delta) lo cubre el barrido de main: cada 5 PRs con código, thermos sobre el rango acumulado (`--sellar-thermos-main`).

**`claude-thermos`** ([izeigerman](https://github.com/izeigerman/claude-thermos)), instalado con `uv tool` y fijado a `2b030cd`. Es un proxy local (mitmproxy) que mantiene caliente el caché mientras el agente principal espera a un subagente. **Se activa lanzando `claude-thermos` en vez de `claude`** (CLI); no afecta a las sesiones que no arrancan así. Revisado: el único destino es `api.anthropic.com` y el log (`~/.claude-thermos/logs`) guarda solo metadatos de uso, sin prompts ni headers. Tus credenciales pasan por el proceso local.

> Corregido 2026-09-23: estaba como "pendiente de decisión"; el usuario lo aprobó y quedó instalado.

**Candidatos evaluados el 2026-09-29** (no instalados, no están en `stack.ps1`):

| Candidato | Veredicto | Motivo |
|---|---|---|
| [`agent-browser`](https://github.com/vercel-labs/agent-browser) (Vercel Labs, Apache 2.0) | **revisado 2026-09-29, apto con condiciones; instalado 2026-09-29 fijado a 0.38.1 (hash npm verificado)** | CLI de navegador con snapshots de accesibilidad y referencias `@eN`; según sus autores gasta ~90 % menos tokens que Playwright MCP. Cubre verificación de UI en sesiones sin navegador del host (CLI, CI). Detalle de la revisión abajo |

**Revisión de `agent-browser` v0.38.1** (commit `aff6125c`, tag `v0.38.1`; npm `sha512-k58FCz0y…lvnhw==`).
Alcance: la superficie de ataque, no las ~103.000 líneas de Rust una por una.

- **Cadena de suministro:** la atestación SLSA de npm apunta a `release.yml` en el commit del tag
  (primera revisión). La segunda revisión sólo vio que el workflow declara `--provenance`
  (`release.yml:334`); no consultó la atestación. Los 7 binarios se compilan en GitHub Actions y
  viajan dentro del tarball (en win32-x64 el postinstall no descarga nada). No se verificó que el
  binario sea reproducible bit a bit. **Debilidades del release:** se dispara en cada push a `main`
  (`release.yml:5`), 0 Actions fijadas por SHA, y los assets se suben con `gh release upload
  --clobber` (`release.yml:423`), o sea reemplazables. La atestación prueba dónde se construyó, no
  que el código sea benigno.
- **Instalación:** el postinstall reescribe los shims globales de npm (`.cmd`/`.ps1`) para
  apuntar al binario (`postinstall.js:278-319`). Si el binario falta, lo baja de GitHub Releases
  **sin checksum** (`postinstall.js:54-84`, sigue redirects sin comprobar host). `install.rs` baja
  Chrome for Testing también sin hash.
- **Red:** sin telemetría (grep). Solo contacta hosts externos por uso explícito: Chrome for Testing
  (`agent-browser install`), npm (`agent-browser upgrade`, manual) y los proveedores cloud o
  `ai-gateway.vercel.sh` solo si se configura su API key.
- **Daemon:** en Windows escucha por TCP en `127.0.0.1` **sin token**, en un puerto derivado por
  hash determinista del nombre de sesión (`connection.rs:382-390`; no es aleatorio). Una página
  web no puede hablarle, porque corta cualquier línea que empiece como HTTP. Cualquier proceso
  local del usuario sí puede manejarlo.
- **ALTA — `./agent-browser.json` del directorio actual ejecuta programas** (revisión 2, `flags.rs:356`):
  se carga sin confirmar y define `plugins` (`flags.rs:107`), `executablePath`, `args`,
  `extensions`, `initScripts`, `proxy`, `caCert`. Los plugins con `launch.mutate` se lanzan con
  `Command::new` (`plugins.rs:207`, `native/actions.rs:4273`). Correrlo en un repo ajeno con ese
  archivo ejecuta su `command`. Sólo lo frenaría una `action_policy` propia. **Mitigación:**
  exportar `AGENT_BROWSER_CONFIG` a un archivo propio (`flags.rs:333-349`, hace que se ignore el
  del proyecto) y revisar si existe `agent-browser.json` antes de correr en un repo ajeno.
  Se pierde: la configuración por proyecto.
- **ALTA, sólo con `AI_GATEWAY_API_KEY` definida — `/api/chat` no rechaza orígenes ajenos**
  (`http.rs:291`; `/api/command` sí da 403, `http.rs:191-227`): un POST desde cualquier web al
  puerto loopback llega al bucle LLM (`chat.rs:906-936`). `execute_chat_tool` valida sólo la
  primera palabra contra `ALLOWED_COMMANDS` (incluye `eval`, `cookies`, `storage`, `state`,
  `upload`, `connect`) y `parse_flags` acepta `--executable-path` en cualquier posición
  (`flags.rs:815`); [Probable] que permita lanzar un ejecutable, no probado. **Mitigación:** no
  definir `AI_GATEWAY_API_KEY`. Se pierde: el chat del dashboard.
- **Chrome:** `--remote-debugging-port=0` en loopback sin autenticación (`chrome.rs:464`).
  `--no-sandbox` si existe `CI`, si es root o si detecta contenedor (`chrome.rs:1523-1553`); con
  `CI` definida en la máquina, el sandbox se apaga.
- **Baja:** `--profile <nombre>` copia el perfil real de Chrome (cookies, logins) a
  `%TEMP%\agent-browser-profile-<uuid>` (`chrome.rs:734-748`); un crash lo deja. `state save`
  escribe cookies en claro sin `AGENT_BROWSER_ENCRYPTION_KEY` (`state.rs:327-333`; los `0o600`
  son sólo Unix). `read <url>` hace GET a cualquier URL sin bloquear IPs privadas o de metadatos
  (`read.rs:187-198`; respeta `--allowed-domains`).
- **Servidor de stream** (arranca siempre, puerto aleatorio en `127.0.0.1`): `/api/command`
  exige Host y Origin locales y tiene un test contra DNS rebinding. Pero `GET /api/tabs` responde
  con `CORS *`: una página que adivine el puerto lee las URL y títulos de las pestañas
  automatizadas. `POST /api/sessions` también: puede lanzar sesiones `about:blank` (argumentos
  fijos, nombre validado, sin ejecución de código).
- **Texto de skills:** sin unicode invisible. Los comentarios HTML son marcadores de release y de
  plantilla. No hay órdenes de ocultamiento ni exfiltración. `trust-boundaries.md` enseña a
  tratar el contenido de la página como datos. El stub `SKILL.md` carga sus instrucciones desde
  el binario (`skills get core`), así que fijar la versión del binario fija también el texto.
  Pero ese stub preautoriza `Bash(agent-browser:*)` y `Bash(npx agent-browser:*)`
  (`skills/agent-browser/SKILL.md:3-5`): quitar `npx` si se copia la skill. La propia doc admite
  que las etiquetas de límites de contenido no son barrera contra prompt-injection.
- **Inyección por páginas (diseño):** el agente lee texto de la página y dispone de `eval`,
  `cookies`, `storage`, `state`. Las defensas (`--allowed-domains`, `--content-boundaries`,
  `--action-policy`, `--confirm-actions`) vienen apagadas por defecto.
- **Sin hallazgo:** inyección de shell en los `Command::new` de `upgrade.rs`, `plugins.rs`,
  `chrome.rs` (argumentos separados); zip con `enclosed_name` (`install.rs:347-369`).
- **No revisado** (~90 % de las 103k líneas): `actions.rs` salvo plugins y lanzamiento,
  `commands.rs`, `snapshot.rs`, CDP, `packages/dashboard` (JS), dependencias de Cargo y pnpm, ni
  se comparó el tarball de npm con el commit. Los dos hallazgos ALTOS salen de leer código; no se
  ejecutaron.
- **Prueba de uso, 2026-09-29 (Windows, Chrome del sistema):** `open about:blank`,
  `open https://example.com`, `get title` y `snapshot` respondieron bien (exit 0, headless,
  perfil temporal `%TEMP%\agent-browser-chrome-<uuid>`). **Trampa:** el daemon hereda los
  handles de salida, así que encadenar con pipe (`agent-browser ... | Select-Object`) **cuelga**
  el comando y deja Chrome y daemon vivos. Redirigir a archivo:
  `cmd /c "agent-browser --session s <cmd> > %TEMP%\ab.txt 2>&1"`. `close` cierra la sesión que
  conoce; los restos de una corrida colgada se matan por línea de comandos (`agent-browser-chrome-`
  en `--user-data-dir`), nunca por nombre `chrome.exe`, que mataría el Chrome del usuario.
  Al leer la salida por consola aparece mojibake (codificación del lector, no de la herramienta).
- **Condiciones de uso:** fijar `agent-browser@0.38.1` y no usar `upgrade` sin revisar el delta.
  Usar Chrome del sistema (`--executable-path`) o `agent-browser install`. No abrir URL con
  secretos en la query mientras corre, por `/api/tabs`. Cerrar la sesión al terminar
  (`agent-browser close`). No configurar plugins ni API keys de proveedores sin revisarlos aparte.
  **Añadidas en la revisión 2:** exportar `AGENT_BROWSER_CONFIG` a un archivo propio y revisar
  `agent-browser.json` antes de correr en repos ajenos; no definir `AI_GATEWAY_API_KEY`; no usar
  `--profile` con nombre; no definir `CI` al lanzarlo; definir `AGENT_BROWSER_ENCRYPTION_KEY` si
  se usa `state save`; preferir `--allowed-domains`; quitar `npx` de `allowed-tools` si se copia
  la skill.
| [Superpowers](https://github.com/obra/superpowers) (plugin completo) | descartado | brainstorming, planes y subagentes duplican Spec Kit y las fases 1–4, y sus disparadores compiten con los de esta skill. Se adoptó sólo la idea del protocolo de depuración, escrita en `fase-5-implementacion.md` |
| [Supermemory](https://supermemory.ai/docs/integrations/claude-code) | descartado | segunda memoria de hechos fuera del vault (rompe la Ley de Dueño Único) y envía el contexto a un servicio externo |
| [Guías de Karpathy](https://github.com/multica-ai/andrej-karpathy-skills) | adoptadas como texto | cuatro reglas de implementación, puestas como invariantes por defecto de la constitución (Fase 2); no requieren plugin |

## Auditoría de código obligatoria: anti-slop por cambio, thermos por PR (regla dura, todo proyecto)

> Movida desde `~/.claude/CLAUDE.md` el 2026-09-29 para no cargarla en cada sesión. Sigue valiendo en **todo** proyecto, use o no full-autodev; `CLAUDE.md` deja un puntero a esta sección.

Con el mismo rango que context-mode: en todo proyecto, no es opcional ni se omite por urgencia. Cada herramienta corre en la unidad para la que su documentación la hizo:
1. **Cada cambio de código, antes del commit:** anti-slop. La skill aplica mientras se escribe, y el scanner determinista corre sobre los archivos cambiados. Un `high` que introduce el diff se corrige; uno previo se reporta. En un cambio solo de documentación, el scanner corre sobre la prosa.
2. **Antes de fusionar un PR con código, y antes de subir un spec a `N2`+:** `/thermos` sobre el diff de la rama (los dos revisores en paralelo) y `/slop-check pr`. thermos se define como revisión de rama o PR y no se invoca sola (`disable-model-invocation`). La unidad es el PR, no la madurez del proyecto: un proyecto joven también fusiona ramas.
3. **Revisión pedida** («revisá esto», auditoría de un módulo): `/thermos` sobre lo que se nombre.

### Costo de thermos

Desde el 2026-09-26; medido en el PR #54 de CristalChile-Maqueta: 33 corridas de revisor en un día, y el de bugs en Opus con hasta 92 turnos y 9.4M tokens leídos de caché, porque ejecutaba suites y escribía scripts de prueba.
- **Modelo por etapa**, con el parámetro `model` de la llamada a Agent. Desde el 2026-09-29 **todo revisor corre con `"sonnet"` (Sonnet 5.5), sin escalar a Opus por nivel de spec**: `thermo-nuclear-code-quality-review-subagent`, `thermo-nuclear-review-subagent` (bugs y seguridad) y el `slop-detector` de `/slop-check` (su frontmatter dice `model: inherit`; se le pasa `model: "sonnet"` en la llamada a Agent, sin editar el plugin fijado). El scanner `slop-scanner.mjs` es regex determinista y no usa modelo. Si un revisor devuelve hallazgos pobres o incompletos, decirlo en la síntesis.
- **Revisores estáticos.** El prompt de cada revisor lleva la ruta del diff en el scratchpad, la lista de archivos, el log de commits y el resultado de los tests que ya corrió el agente principal. También les prohíbe ejecutar suites, servidores o `node`/`python` del proyecto, escribir scripts de prueba, y rehacer `git diff`/`git log` del rango. Un hallazgo que sólo se confirma ejecutando se reporta «por confirmar», con el comando, y lo corre el agente principal.
- **Rondas incrementales.** El primer thermos de un PR es completo. Las rondas de arreglo auditan sólo el delta que imprime `--base-thermos [PR]`, con los hallazgos previos y cuáles se corrigieron, y sólo con el revisor cuyos hallazgos se atendieron. Se sellan con `--delta`. Hay un máximo de 3 deltas seguidos; el siguiente es completo. Si desde el último sello sólo cambió prosa, el merge pasa sin otra ronda.
- **Zona de impacto del delta.** El prompt de una ronda delta lleva, además del diff, quién usa lo que tocó el arreglo: `graphify affected "<símbolo>"` tras `graphify update .`, o un grep del nombre si el símbolo no está en el grafo (el JS dentro de strings de Python no está). El revisor mira esos usos, no los archivos enteros. La lista que el agente principal escribe de lo que tocó va como complemento, no en lugar de la mecánica: la escribió quien hizo el arreglo, y si supiera qué rompió no lo habría roto.
- **Barrido de la rama principal.** Thermos por PR no ve cómo interactúan PRs distintos, y un delta no ve lo que un arreglo rompió fuera de él. Cuando hay 5 PRs con código fusionados desde el último barrido, el hook bloquea el siguiente merge hasta correr thermos sobre ese rango de main. El foco son las interacciones entre esos PRs y los archivos que en su PR sólo se auditaron en delta (el bloqueo los lista). Se sella con `--sellar-thermos-main <commit>`. Un hallazgo bloqueante del barrido va a su propio PR.

Un hallazgo bloqueante se corrige antes del commit o del merge; los demás van a backlog o a una decisión, no se quedan en el chat.

Lo hace cumplir `~/.claude/hooks/auditoria_obligatoria.py`: el commit pide `--sellar` (anti-slop sobre el árbol) y `gh pr merge` pide `--sellar-thermos [PR]` o `--sellar-thermos [PR] --delta` (thermos sobre la cabeza del PR), más `--sellar-thermos-main` cuando toca barrido. El modelo de cada revisor no lo verifica: es regla, no compuerta.
