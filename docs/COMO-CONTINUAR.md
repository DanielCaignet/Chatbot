# Cómo continuar chatbot-richard desde otro PC

Guía para Richard. Al terminarla, tu Claude Code trabaja este proyecto con las mismas reglas,
herramientas y memoria con que se montó.

## Índice
1. Qué hay en el repo
2. Herramientas que necesitas
3. Instalación paso a paso
4. Hook opcional de context-mode
5. Cómo trabaja el agente en este proyecto
6. Secretos y datos
7. Diferencias con el PC donde se montó

## 1. Qué hay en el repo

| Archivo | Para qué |
|---|---|
| `STATE.md` | Dónde está el proyecto, qué bloquea y cuál es el próximo paso. Se sobreescribe. |
| `vault/AGENT-INDEX.md` | Por dónde entra el agente al vault. |
| `docs/PLAN-MAESTRO.md` | Plan aprobado: arquitectura, fases F0–F8, referencias externas consultadas. |
| `.specify/memory/constitution.md` | Las seis reglas que nunca se rompen. |
| `vault/` | Conceptos, decisiones (ADR-000…008) y fichas de fuentes externas. Se abre con Obsidian. |
| `herramientas/full-autodev/` | Copia de la skill que orquesta el proyecto (Spec Kit + vault + grafo). |
| `herramientas/instalar.ps1` | Prepara el PC. |
| `CLAUDE.md` | Lo lee Claude Code solo: reglas de trabajo y estilo de interacción. |

El grafo (`graphify-out/`) no está en git: es derivado y el instalador lo reconstruye.

## 2. Herramientas que necesitas

**Del sistema** (las instalas tú; el script te dice el comando si falta):

| Herramienta | Versión mínima | Instalar |
|---|---|---|
| Git | 2.40 | `winget install --id Git.Git -e` |
| Node.js | 20 LTS | `winget install --id OpenJS.NodeJS.LTS -e` |
| Python | 3.11 | `winget install --id Python.Python.3.13 -e` |
| uv | 0.8 | `winget install --id astral-sh.uv -e` |
| Claude Code | última (`claude update`) | `npm install -g @anthropic-ai/claude-code` |
| GitHub CLI | 2.x | `winget install --id GitHub.cli -e`, luego `gh auth login` |
| Cliente OpenSSH | — | viene con Windows 10/11 (características opcionales); para entrar a la VM |
| Obsidian | — | opcional, para leer el vault: abrir la **raíz del repo** como vault |

**Las instala el script** (`herramientas/instalar.ps1` → `stack.ps1` de la skill):

| Herramienta | Qué hace |
|---|---|
| `graphify` + `graphify-mcp` (`graphifyy[mcp]==0.9.67`) | Grafo de conocimiento del repo; el agente lo consulta antes de responder. |
| `specify` (Spec Kit) | Specs por feature: `speckit-specify`, `speckit-plan`, `speckit-tasks`… |
| `markitdown` | Convierte PDF/DOCX a Markdown citable. |
| `claude-thermos` y `agent-browser` | Opcionales: proxy de caché y verificación de interfaces. |

**Plugins de Claude Code** (los instala el mismo script, cada uno fijado al commit que se revisó):

| Plugin | Repo | Para qué |
|---|---|---|
| `context-mode` | mksglu/context-mode | Lee y busca sin volcar archivos al contexto; memoria de la sesión. |
| `anti-slop` (4 variantes) | TheMizeGuy, paslavskyi, luantaraschi, miqdadbadjuber | Scanner de calidad de código y prosa en cada commit. |
| `thermos` | theocarranza/thermos-claude | Auditoría profunda de un PR. **Solo cuando la pidas.** |

Si `stack.ps1` dice **SIN REVISAR**, lo instalado no coincide con el commit revisado: una skill
es texto que el agente obedece, así que no la uses hasta revisarla.

**Para el producto** (no en tu PC, sino en la Oracle VM): Docker y Docker Compose. Se instalan
en el spike F1.

## 3. Instalación paso a paso

1. Clona el repo y entra a la carpeta:
   ```powershell
   git clone <URL del repo> "Chatbot Richard"
   cd "Chatbot Richard"
   ```
2. Ejecuta el instalador:
   ```powershell
   powershell -ExecutionPolicy Bypass -File herramientas\instalar.ps1
   ```
   Si falta algo del sistema, instálalo, abre una terminal nueva y repítelo. Para solo revisar:
   agrega `-SoloVerificar`.
3. Configura tu identidad git en el repo:
   ```powershell
   git config user.name "Tu nombre"
   git config user.email "tu@correo"
   ```
4. Abre Claude Code en la raíz del repo y escribe:
   ```
   /full-autodev --resume
   ```
   El agente lee `STATE.md` y `vault/AGENT-INDEX.md` y sigue desde el próximo paso.
5. Reinicia Claude Code después de instalar los plugins para que carguen.

## 4. Hook opcional de context-mode

En el PC donde se montó, un hook obliga al agente a leer y buscar con context-mode en vez de
volcar archivos completos. Ahorra contexto y tokens. Para activarlo:

1. Copia `herramientas/hooks/contexto_obligatorio.py` a `%USERPROFILE%\.claude\hooks\`.
2. Agrega esto en `%USERPROFILE%\.claude\settings.json`, dentro de `"hooks"`:
   ```json
   "PreToolUse": [
     {
       "matcher": "Read|Grep|WebFetch|Bash|PowerShell",
       "hooks": [{ "type": "command",
                   "command": "python \"C:/Users/<tu usuario>/.claude/hooks/contexto_obligatorio.py\"",
                   "timeout": 10 }]
     }
   ]
   ```
3. Para apagarlo en una emergencia: crea el archivo `%USERPROFILE%\.claude\hooks\.ctx_off`.

## 5. Cómo trabaja el agente en este proyecto

- **Orientación:** al arrancar lee solo `STATE.md` y `vault/AGENT-INDEX.md`. El resto lo alcanza
  por enlaces.
- **Antes de responder o actuar:** `graphify query "<pregunta>"`.
- **Cada hecho en un solo archivo.** Un término va a `vault/Conceptos/`, una decisión a un ADR
  nuevo en `vault/Decisiones/` (los ADR no se editan) y una fuente externa a `vault/Fuentes/`.
- **Feature nueva:** `speckit-specify` → `speckit-plan` → `speckit-tasks` → `speckit-implement`,
  con su ficha en `vault/Specs/` y su fila en `vault/MOCs/00 - Indice de Specs.md`.
- **Al cerrar cada fase:** `graphify update .`, `graphify save-result …` y se reescribe `STATE.md`.
- **Commits:** el hook pre-commit corre las compuertas (`gates.py`) y el scanner anti-slop.
- **Grafo semántico:** `graphify update .` solo extrae estructura (sin LLM). El pase semántico
  sobre documentos se corre con `/graphify .` desde Antigravity, si lo tienes instalado.

Las reglas completas están en `herramientas/full-autodev/SKILL.md` y en `CLAUDE.md`.

## 6. Secretos y datos

- Ninguna llave, token o contraseña va al repo. Se guardan en `.env` (ignorado por git) o en el
  gestor de secretos que se defina en el spike.
- Los modelos gratuitos (OpenRouter `:free`) solo reciben datos sintéticos: principio IV de la
  constitución.
- El plan menciona código de proyectos previos de DataSeed (`D:\Dataseed\…`). Ese código no está
  en este repo; si lo necesitas, pídeselo a Daniel.

## 7. Diferencias con el PC donde se montó

- No se copió el hook que exige `/thermos` antes de cada merge: en este proyecto thermos corre
  solo cuando se pide.
- La memoria automática del agente de ese PC no viaja. Las reglas que guardaba ya están en
  `CLAUDE.md` (sección "Reglas de trabajo").
