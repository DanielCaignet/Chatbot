<#
.SYNOPSIS
  Monta el esqueleto full-autodev: Spec Kit + vault Obsidian + grafo graphify.

.DESCRIPTION
  Idempotente. Fase 0 escanea lo que ya existe y decide por cada pieza:
  fresh (crear), incremental (completar lo que falta), skip (ya esta).
  Nunca sobreescribe contenido escrito por una persona.

  Todo el contenido se define en here-strings LITERALES (@'...'@) para que los
  backticks de los bloques de codigo sobrevivan; los valores se inyectan despues
  con los marcadores {{NAME}}, {{TODAY}} y {{PROFILE}}.

.EXAMPLE
  .\bootstrap.ps1 -Path "D:\Dev\AgentEngine" -Name "Agent Engine"
  .\bootstrap.ps1 -Path "D:\Dev\Tesis" -Name "Tesis" -Profile research
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Path,
    [Parameter(Mandatory = $true)][string]$Name,
    [ValidateSet('software', 'research', 'data')][string]$Profile = 'software',
    [switch]$NoSpecKit,
    [switch]$NoGit,
    [switch]$NoStack,
    [switch]$WhatIfOnly
)

$ErrorActionPreference = 'Stop'
$script:Created = @()
$script:Skipped = @()
$script:Failed  = @()

$Utf8NoBom = New-Object System.Text.UTF8Encoding $false

# --- helpers -----------------------------------------------------------------

function Expand-Tokens {
    param([string]$Text)
    $out = $Text -replace '\{\{NAME\}\}',    $Name
    $out = $out  -replace '\{\{TODAY\}\}',   $script:Today
    $out = $out  -replace '\{\{PROFILE\}\}', $Profile
    return $out
}

function Write-File {
    param([string]$FullPath, [string]$Content)
    if (Test-Path -LiteralPath $FullPath) {
        $script:Skipped += $FullPath
        return
    }
    $dir = Split-Path -Parent $FullPath
    if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    if ($WhatIfOnly) { Write-Host "  [dry-run] crearia $FullPath"; return }
    [System.IO.File]::WriteAllText($FullPath, (Expand-Tokens $Content), $Utf8NoBom)
    $script:Created += $FullPath
}

function New-Dir {
    param([string]$FullPath)
    if (Test-Path -LiteralPath $FullPath) { return }
    if ($WhatIfOnly) { Write-Host "  [dry-run] crearia dir $FullPath"; return }
    New-Item -ItemType Directory -Path $FullPath -Force | Out-Null
    $script:Created += "$FullPath\"
}

function Invoke-Step {
    param([string]$Label, [scriptblock]$Action)
    try { & $Action }
    catch {
        $script:Failed += "$Label : $($_.Exception.Message)"
        Write-Host "  ! $Label fallo: $($_.Exception.Message)" -ForegroundColor Yellow
    }
}

# --- Fase 0: escaneo ---------------------------------------------------------

if (-not (Test-Path -LiteralPath $Path)) { New-Item -ItemType Directory -Path $Path -Force | Out-Null }
$Root = (Resolve-Path -LiteralPath $Path).Path
$script:Today = Get-Date -Format 'yyyy-MM-dd'

Write-Host ""
Write-Host "full-autodev bootstrap" -ForegroundColor Cyan
Write-Host "  proyecto : $Name"
Write-Host "  raiz     : $Root"
Write-Host "  perfil   : $Profile"
Write-Host ""

$hasGit     = Test-Path -LiteralPath (Join-Path $Root '.git')
$hasSpecify = Test-Path -LiteralPath (Join-Path $Root '.specify')
$hasVault   = Test-Path -LiteralPath (Join-Path $Root 'vault')
if ($hasVault) { $mode = 'incremental' } else { $mode = 'fresh' }
Write-Host "Fase 0 - escaneo: modo=$mode  git=$hasGit  specify=$hasSpecify  vault=$hasVault"

# --- stack: CLIs y plugins instalados de verdad, no solo documentados ---------

if (-not $NoStack) {
    $stackPs1 = Join-Path $PSScriptRoot 'stack.ps1'
    if ($WhatIfOnly) { & $stackPs1 -CheckOnly } else { & $stackPs1 }
    if ($LASTEXITCODE -ne 0) { $script:Failed += 'stack: faltan herramientas (ver arriba)' }
}

# --- git (los hooks de graphify lo necesitan) --------------------------------

if (-not $hasGit -and -not $NoGit -and -not $WhatIfOnly) {
    Invoke-Step 'git init' {
        git init -q -- "$Root" 2>&1 | Out-Null
        Write-Host "  + repositorio git inicializado"
    }
    $hasGit = Test-Path -LiteralPath (Join-Path $Root '.git')
}

# --- Spec Kit ----------------------------------------------------------------

if (-not $hasSpecify -and -not $NoSpecKit -and -not $WhatIfOnly) {
    Invoke-Step 'specify init' {
        Push-Location $Root
        try {
            $out = & specify init --here --force --non-interactive --integration claude --script ps 2>&1
            if (Test-Path -LiteralPath (Join-Path $Root '.specify')) {
                Write-Host "  + Spec Kit inicializado (.specify/ + skills speckit-* en .claude/skills/)"
            } else {
                throw (($out | Select-Object -Last 3) -join ' ')
            }
        } finally { Pop-Location }
    }
}

# --- vault -------------------------------------------------------------------

$vaultDirs = @('MOCs', 'Specs', 'Conceptos', 'Decisiones', 'Fuentes')
switch ($Profile) {
    'software' { $vaultDirs += 'Componentes' }
    'research' { $vaultDirs += @('Metodos', 'Resultados') }
    'data'     { $vaultDirs += @('Datasets', 'Experimentos') }
}
foreach ($d in $vaultDirs) { New-Dir (Join-Path $Root "vault\$d") }

# --- plantillas de ficha -----------------------------------------------------

$tplSpec = @'
---
tipo: spec
id: SPEC-NNN
titulo: ""
status: vigente        # vigente | superseded  (solo si rige; NO mide avance)
spec_path: "specs/NNN-slug/"
supersedes: []
creado: {{TODAY}}
actualizado: {{TODAY}}
---

# SPEC-NNN — <titulo>

> Esta ficha **no repite** el spec. Es el nodo que lo hace encontrable en el grafo.
> El contenido normativo vive en `spec_path`. Aca solo van punteros y relaciones.
> El **nivel de madurez** (N0-N3) y su limite viven en la fila de [[00 - Indice de Specs]],
> dueño unico. No se repiten aca.

**Spec:** [`specs/NNN-slug/spec.md`](specs/NNN-slug/spec.md)
**Plan:** [`specs/NNN-slug/plan.md`](specs/NNN-slug/plan.md)
**Tareas:** [`specs/NNN-slug/tasks.md`](specs/NNN-slug/tasks.md)

## En una linea
<que resuelve, una sola oracion>

## Conceptos que toca
[[Concepto A]] · [[Concepto B]]

## Decisiones que lo gobiernan
[[ADR-000]]

## Depende de / Bloquea
- Depende de: [[SPEC-NNN]]
- Bloquea: [[SPEC-NNN]]
'@

$tplConcepto = @'
---
tipo: concepto
titulo: ""
alias: []
creado: {{TODAY}}
actualizado: {{TODAY}}
---

# <Concepto>

## Definicion
<Una definicion. Esta ficha es la dueña unica del termino: si otro archivo
necesita explicarlo, enlaza aca en vez de redefinirlo.>

## Por que importa en este proyecto
<2-3 lineas>

## Se relaciona con
[[Otro Concepto]]

## Aparece en
[[SPEC-NNN]] · [[ADR-NNN]]
'@

$tplAdr = @'
---
tipo: adr
id: ADR-NNN
titulo: ""
status: accepted        # proposed | accepted | superseded
supersedes: []
fecha: {{TODAY}}
---

# ADR-NNN — <titulo>

> Inmutable. Si la decision cambia se escribe un ADR nuevo con `supersedes: [ADR-NNN]`
> y el viejo pasa a `status: superseded`. Nunca se edita un ADR aceptado.

## Contexto
<que situacion forzo la decision>

## Decision
<que se decidio, en voz activa>

## Alternativas descartadas
- <alternativa> — descartada porque <razon>

## Consecuencias
- <lo que esto habilita>
- <lo que esto cuesta>

## Relacionado
[[Concepto]] · [[SPEC-NNN]]
'@

$tplFuente = @'
---
tipo: fuente
titulo: ""
autores: []
anio:
url: ""
archivo_local: ""
creado: {{TODAY}}
---

# <Titulo>

> Esta ficha **reemplaza** a la fuente en el contexto. Volver al archivo original
> solo para un detalle fino que no este aca: una ecuacion, una firma, un valor.

## TL;DR
<3 lineas maximo>

## Que aporta a este proyecto
<rol concreto, no resumen generico>

## Datos duros
- <metrica / cifra / limite que se vaya a citar>

## Conceptos
[[Concepto A]] · [[Concepto B]]
'@

Write-File (Join-Path $Root 'vault\Specs\_TEMPLATE-SPEC.md')          $tplSpec
Write-File (Join-Path $Root 'vault\Conceptos\_TEMPLATE-CONCEPTO.md')  $tplConcepto
Write-File (Join-Path $Root 'vault\Decisiones\_TEMPLATE-ADR.md')      $tplAdr
Write-File (Join-Path $Root 'vault\Fuentes\_TEMPLATE-FUENTE.md')      $tplFuente

# --- MOCs --------------------------------------------------------------------

$mocSpecs = @'
---
tipo: moc
titulo: "Indice de Specs"
actualizado: {{TODAY}}
---

# Indice de Specs — {{NAME}}

> **Registro unico de specs.** Antes de crear un spec nuevo se lee este archivo.
> Un spec que no aparece aca es `SPEC-UNINDEXED`: existe en disco pero el agente
> solo puede encontrarlo por busqueda textual, nunca por el indice ni por el grafo.
>
> **Dueño unico del nivel de madurez.** No hay "terminado": cada spec esta cerrado en un nivel.
> `N0` contrato escrito · `N1` stub con limite falsable · `N2` produccion, un caso · `N3` multi-caso.
> Un `N1` exige en `Limite` una frase refutable (>= 6 palabras); lo verifica `gates.py::G-N1`.
> `N2`/`N3` citan el caso real en `Limite` (`[INT:<ruta>]` o `[MEDIDO]`).

| ID | Titulo | Nivel | Limite | Status | Spec |
|---|---|---|---|---|---|
| — | _sin specs todavia_ | — | — | — | — |

## Superados
_ninguno_
'@

$mocConceptos = @'
---
tipo: moc
titulo: "Indice de Conceptos"
actualizado: {{TODAY}}
---

# Indice de Conceptos — {{NAME}}

> Cada termino del dominio tiene **una** ficha dueña. Lo demas enlaza.

_sin conceptos todavia_
'@

$mocDecisiones = @'
---
tipo: moc
titulo: "Indice de Decisiones"
actualizado: {{TODAY}}
---

# Indice de Decisiones — {{NAME}}

> ADRs en orden cronologico. Inmutables. Los superados quedan listados, no se borran.

| ID | Titulo | Status | Fecha |
|---|---|---|---|
| — | _sin decisiones todavia_ | — | — |
'@

$mocFuentes = @'
---
tipo: moc
titulo: "Indice de Fuentes"
actualizado: {{TODAY}}
---

# Indice de Fuentes — {{NAME}}

> Fichas que reemplazan documentos externos en el contexto.

_sin fuentes todavia_
'@

Write-File (Join-Path $Root 'vault\MOCs\00 - Indice de Specs.md')       $mocSpecs
Write-File (Join-Path $Root 'vault\MOCs\01 - Indice de Conceptos.md')   $mocConceptos
Write-File (Join-Path $Root 'vault\MOCs\02 - Indice de Decisiones.md')  $mocDecisiones
Write-File (Join-Path $Root 'vault\MOCs\03 - Indice de Fuentes.md')     $mocFuentes

# --- AGENT-INDEX (archivo 1 de 2 de orientacion) -----------------------------

$agentIndex = @'
---
tipo: agent-index
proyecto: "{{NAME}}"
actualizado: {{TODAY}}
---

# AGENT-INDEX — {{NAME}}

> Superficie de orientacion del agente. Junto con `STATE.md` son los **unicos dos
> archivos** que se leen al arrancar. Todo lo demas se alcanza por enlaces, bajo
> demanda. Mantener este archivo por debajo de 60 lineas: si crece, el detalle va a un MOC.

## Entradas
- [[00 - Indice de Specs]] — que se esta construyendo y en que estado
- [[01 - Indice de Conceptos]] — vocabulario del dominio
- [[02 - Indice de Decisiones]] — por que las cosas son como son
- [[03 - Indice de Fuentes]] — documentos externos ya destilados

## Como consultar antes de responder
```bash
graphify query "<pregunta>"        # subgrafo acotado
graphify affected "<nodo>"          # que queda obsoleto si esto cambia
graphify path "<A>" "<B>"           # como se relacionan dos cosas
graphify explain "<nodo>"           # que es un nodo y sus vecinos
```

## Invariantes
Viven en `.specify/memory/constitution.md`. No se copian aca.

## Perfil
`{{PROFILE}}`
'@

Write-File (Join-Path $Root 'vault\AGENT-INDEX.md') $agentIndex

# --- STATE.md (archivo 2 de 2) -----------------------------------------------

$stateMd = @'
---
tipo: state
proyecto: "{{NAME}}"
actualizado: {{TODAY}}
---

# STATE — {{NAME}}

> **Se sobreescribe, nunca se acumula.** Maximo 40 lineas.
> Lo que es historia va a un ADR inmutable en `vault/Decisiones/`.
> Si aparece un segundo archivo de estado o handoff, eso es `STATE-SPRAWL`: corregirlo.

## Donde estamos
Proyecto recien montado. Falta la entrevista de la Fase 1.

## Spec activo
ninguno

## Bloqueos
ninguno

## Proximo paso
Correr `/full-autodev --resume` para la entrevista y la constitucion.
'@

Write-File (Join-Path $Root 'STATE.md') $stateMd

# --- Obsidian: la raiz ES el vault -------------------------------------------

$obsidianApp = @'
{
  "useMarkdownLinks": false,
  "newFileFolderPath": "vault/Conceptos",
  "attachmentFolderPath": "vault/Fuentes",
  "alwaysUpdateLinks": true,
  "readableLineLength": true
}
'@

Write-File (Join-Path $Root '.obsidian\app.json') $obsidianApp

# --- conector MCP de graphify ------------------------------------------------

$mcpJson = @'
{
  "mcpServers": {
    "graphify": {
      "command": "graphify-mcp",
      "args": ["graphify-out/graph.json"]
    }
  }
}
'@

Write-File (Join-Path $Root '.mcp.json') $mcpJson

# --- CLAUDE.md: manual operativo ---------------------------------------------

$manual = @'
# {{NAME}}

Proyecto gestionado por la skill `full-autodev`. Perfil: `{{PROFILE}}`.

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
'@

$claudeMd = Join-Path $Root 'CLAUDE.md'
if (Test-Path -LiteralPath $claudeMd) {
    $existing = Get-Content -LiteralPath $claudeMd -Raw -Encoding UTF8
    if ($existing -notmatch 'Ley de Due') {
        if (-not $WhatIfOnly) {
            $merged = $existing.TrimEnd() + "`r`n`r`n---`r`n`r`n" + (Expand-Tokens $manual)
            [System.IO.File]::WriteAllText($claudeMd, $merged, $Utf8NoBom)
            $script:Created += "$claudeMd (seccion agregada)"
        }
    } else {
        $script:Skipped += $claudeMd
    }
} else {
    Write-File $claudeMd $manual
}

# --- .gitignore --------------------------------------------------------------

$giBlock = @'
# full-autodev: indice derivado, se reconstruye con `graphify update .`
graphify-out/
# historial de compuertas: util local, ruidoso en diffs
.gates/history.jsonl
# anti-slop: registro local del scanner (solo con --record)
.anti-slop/
.obsidian/workspace.json
.obsidian/workspace-mobile.json
'@

$gi = Join-Path $Root '.gitignore'
if (Test-Path -LiteralPath $gi) {
    $giContent = Get-Content -LiteralPath $gi -Raw -Encoding UTF8
    if ($giContent -notmatch 'graphify-out') {
        if (-not $WhatIfOnly) {
            [System.IO.File]::WriteAllText($gi, ($giContent.TrimEnd() + "`r`n`r`n" + $giBlock), $Utf8NoBom)
            $script:Created += "$gi (bloque agregado)"
        }
    } else { $script:Skipped += $gi }
} else {
    Write-File $gi $giBlock
}

# --- compuertas deterministas: gates.toml + feedback + hook pre-commit -------

$gatesToml = @'
# Compuertas deterministas — {{NAME}}
# Corre con: python "$env:USERPROFILE\.claude\skills\full-autodev\references\gates.py"
#
# severity = "block" -> exit 1, bloquea el commit
# severity = "warn"  -> se reporta, no bloquea

[project]
name = "{{NAME}}"

[conventions]
specs_glob    = "specs/**/*.md"
skip_prefixes = ["_"]
req_pattern   = 'RQ-[A-Z0-9]+-\d{3}'
state_line    = '\*\*Estado:\*\*\s*([^·|\n]+)'
closed_states = ["cerrada", "cerrado", "vigente", "aprobada", "aprobado"]
ears_verb     = 'EL SISTEMA DEBER[ÁA]'
probe_pattern = 'V-\d{2}'

# Dueño unico del nivel de madurez: columnas Nivel/Limite del MOC de specs (G-N1)
maturity_file     = "vault/MOCs/00 - Indice de Specs.md"

# Rellenar cuando el proyecto los tenga; vacio = compuerta desactivada
references_file   = ""
decisions_file    = ""

state_file         = "STATE.md"
sprawl_patterns    = ["*handoff*.md", "*estado*.md", "*context*.md", "*traspaso*.md"]
# prefijos que SLOP-SCAN no juzga: artefactos de terceros (p. ej. lo que mando el cliente)
slop_exclude       = []
sprawl_exempt_dirs = [".git", "graphify-out", ".gates", "vault/Decisiones"]

[gates."G-REF"]
enabled = true
severity = "block"

[gates."G-EARS"]
enabled = true
severity = "block"

[gates."G-VERIF"]
enabled = true
severity = "block"

[gates."TRAZA"]
enabled = true
severity = "warn"

[gates."G-N1"]
enabled = true
severity = "block"

[gates."REF-DANGLING"]
enabled = false
severity = "warn"

[gates."DE-DANGLING"]
enabled = false
severity = "warn"

[gates."STATE-SPRAWL"]
enabled = true
severity = "warn"

[gates."GRAPH-MISSING"]
enabled = true
severity = "warn"

[gates."DERIVED-COMMITTED"]
enabled = true
severity = "warn"

# Scanner determinista del plugin anti-slop sobre los archivos cambiados.
# Nace en "warn": se promueve a "block" cuando .gates/history.jsonl muestre que no da
# falsos positivos en este proyecto (Fase 6). Sin plugin o sin node, avisa y no bloquea.
[gates."SLOP-SCAN"]
enabled = true
severity = "warn"

# Todo [[enlace]] del vault y de specs/ resuelve a una nota (nombre = ID exacto).
# Un enlace roto es una arista que el grafo no tiene.
[gates."WIKI-DANGLING"]
enabled = true
severity = "warn"

# Documento de mas de doc_max_lines (200): mirar si tiene partes que se leen en momentos
# distintos. Por defecto mira vault/ y CLAUDE.md; para sumar docs operativos, en [conventions]:
#   doc_size_globs = ["vault/**/*.md", "CLAUDE.md", "docs/DESPLIEGUE.md"]
[gates."DOC-SIZE"]
enabled = true
severity = "warn"

# Nota de vault/ o docs/ que ninguna otra enlaza ni nombra: el agente no llega a ella.
[gates."DOC-ORPHAN"]
enabled = true
severity = "warn"
'@

$feedbackMd = @'
# Retroalimentacion de compuertas — {{NAME}}

Linea de mejora del andamiaje. `gates.py --stats` lee este archivo y muestra lo pendiente.
Sin esto, el linter se congela en las reglas del primer dia.

Se registran **tres cosas y nada mas**:

1. **Falso positivo** — la compuerta bloqueo algo correcto. Es el mas caro: ensena a saltarse
   el linter con `--no-verify`, y desde ahi la compuerta ya no existe.
2. **Falla no atrapada** — algo se rompio y ninguna compuerta lo vio. Es una regla que falta.
3. **Regla muerta** — `--stats` la muestra sin disparar nunca. O el proyecto no la necesita,
   o esta mal escrita y no puede disparar.

Resolver una observacion es una de dos: ajustar `gates.toml` (local a este proyecto), o
**promover el cambio a la plantilla** en `~\.claude\skills\full-autodev\references\gates.py`
y anotarlo en su `CHANGELOG.md`. Lo segundo mejora todos los proyectos, no solo este.

Correccion con la cicatriz a la vista: una observacion resuelta no se borra, se marca `- [x]`
con la fecha y que cambio.

---

## Pendientes

_ninguna todavia_

## Resueltas

_ninguna todavia_
'@

Write-File (Join-Path $Root 'gates.toml')           $gatesToml
Write-File (Join-Path $Root '.gates\feedback.md')   $feedbackMd

if ($hasGit -and -not $WhatIfOnly) {
    $hookPath = Join-Path $Root '.git\hooks\pre-commit'
    if (-not (Test-Path -LiteralPath $hookPath)) {
        $hook = "#!/bin/sh`n" +
                "# full-autodev: las compuertas 'block' bloquean el commit.`n" +
                "GATES=`"`$HOME/.claude/skills/full-autodev/references/gates.py`"`n" +
                "[ -f `"`$GATES`" ] || exit 0`n" +
                "python `"`$GATES`" --root . || {`n" +
                "  echo `"`"`n" +
                "  echo `"commit bloqueado por una compuerta. Para saltarla a conciencia: git commit --no-verify`"`n" +
                "  exit 1`n" +
                "}`n"
        New-Item -ItemType Directory -Path (Split-Path -Parent $hookPath) -Force | Out-Null
        [System.IO.File]::WriteAllText($hookPath, $hook, (New-Object System.Text.UTF8Encoding $false))
        $script:Created += $hookPath
        Write-Host "  + compuertas: hook pre-commit (G-REF, G-EARS, G-VERIF, G-N1 bloquean)"
    } else {
        $script:Skipped += $hookPath
    }
}

# --- graphify: seccion CLAUDE.md + hook PreToolUse + hooks git ---------------

if (-not $WhatIfOnly) {
    Push-Location $Root
    try {
        Invoke-Step 'graphify claude install' {
            & graphify claude install 2>&1 | Out-Null
            Write-Host "  + graphify: seccion CLAUDE.md + hook PreToolUse"
        }
        if ($hasGit) {
            Invoke-Step 'graphify hook install' {
                & graphify hook install 2>&1 | Out-Null
                Write-Host "  + graphify: hooks git post-commit/post-checkout"
            }
        }
    } finally { Pop-Location }
}

# --- reporte -----------------------------------------------------------------

Write-Host ""
Write-Host "Resultado" -ForegroundColor Cyan
Write-Host "  creados                : $($script:Created.Count)"
Write-Host "  ya existian (intactos) : $($script:Skipped.Count)"
if ($script:Failed.Count -gt 0) {
    Write-Host "  fallos                 : $($script:Failed.Count)" -ForegroundColor Yellow
    $script:Failed | ForEach-Object { Write-Host "    - $_" -ForegroundColor Yellow }
}
Write-Host ""
Write-Host "Siguiente: Fase 1 (entrevista). NO construir el grafo todavia:" -ForegroundColor Cyan
Write-Host "  un proyecto recien montado no tiene nada que extraer."
Write-Host ""
