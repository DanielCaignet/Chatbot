<#
.SYNOPSIS
  Verifica e instala el stack full-autodev: CLIs (graphify, Spec Kit) y plugins de Claude Code.

.DESCRIPTION
  Idempotente. Instala solo lo que falta; nunca actualiza lo que ya esta.
  Cada plugin lleva el commit que se reviso antes de adoptarlo (skills, agentes, hooks,
  scripts y MCP leidos en busca de exfiltracion, instrucciones ocultas y red). Si lo
  instalado no coincide con ese commit, se AVISA: una skill es texto que el agente obedece,
  y un commit nuevo es contenido no revisado. Revisar y actualizar $Plugins aca; no
  actualizar a ciegas.

  Los marketplaces cuyo nombre choca con otro (tres repos se declaran "anti-slop") se
  instalan desde una copia local en ~/.claude/plugins-local/<nombre>, fijada al commit
  revisado, con SOLO el campo name de marketplace.json cambiado.

.EXAMPLE
  .\stack.ps1              # verifica e instala lo que falta
  .\stack.ps1 -CheckOnly   # solo reporta
#>
[CmdletBinding()]
param([switch]$CheckOnly)

$ErrorActionPreference = 'Continue'
$script:Missing = @(); $script:Installed = @(); $script:Drift = @()

# --- CLIs ------------------------------------------------------------------------------
# Install = $null -> no se instala solo (requisito del sistema): se reporta.
$Tools = @(
    @{ Cmd = 'git';          Install = $null }
    @{ Cmd = 'node';         Install = $null }
    @{ Cmd = 'python';       Install = $null }
    @{ Cmd = 'uv';           Install = $null }
    @{ Cmd = 'claude';       Install = $null }
    # version fijada y con el extra [mcp]: sin el, graphify-mcp responde --help pero no arranca
    # (ImportError: mcp not installed). Verificado 2026-09-23: tools/list devuelve 10 tools.
    @{ Cmd = 'graphify';     Install = { uv tool install 'graphifyy[mcp]==0.9.67' } }
    @{ Cmd = 'graphify-mcp'; Install = { uv tool install 'graphifyy[mcp]==0.9.67' } }
    @{ Cmd = 'specify';      Install = { uv tool install specify-cli --from git+https://github.com/github/spec-kit.git } }
    # fuentes binarias (PDF, DOCX) a texto citable: sin esto el agente cita de memoria
    @{ Cmd = 'markitdown';   Install = { uv tool install 'markitdown[pdf,docx]' } }
    # proxy local de calentamiento de cache; revisado en 2b030cd (unico destino api.anthropic.com,
    # log solo de metadatos en ~/.claude-thermos/logs). Uso: `claude-thermos` en vez de `claude`.
    @{ Cmd = 'claude-thermos'; Install = { uv tool install 'git+https://github.com/izeigerman/claude-thermos@2b030cdd9e49175ace5e64097e07b83751e24e2d' } }
    # verificacion de UI por CLI; revisado 2026-09-29 en v0.38.1 (aff6125c), apto con condiciones
    # (calidad.md). No correr `agent-browser upgrade`. Solo instala si el hash npm coincide.
    @{ Cmd = 'agent-browser'; Install = {
        $want = 'sha512-k58FCz0yUOCANoNkMiqJe+H2y6r6sUZazqXsWF+MYq1iRC42PjtLcBoag6SSTOD/FRQppvPDvE5HDYEhclvnhw=='
        if ((npm view agent-browser@0.38.1 dist.integrity).Trim() -eq $want) { npm i -g agent-browser@0.38.1 }
        else { Write-Host '  ! hash npm de agent-browser@0.38.1 no coincide con el revisado' -ForegroundColor Red }
    } }
)

# --- plugins (commit revisado 2026-09-23) -----------------------------------------------
$Plugins = @(
    @{ Id = 'context-mode@context-mode';              Repo = 'mksglu/context-mode';          Sha = 'f889a0537dc1fd264bb5e39299db8f9be1ef3fb6' }
    @{ Id = 'anti-slop@anti-slop';                    Repo = 'TheMizeGuy/anti-slop';         Sha = 'd27813bb71e67302498b3cf76aa62429d2321ce6' }
    @{ Id = 'anti-slop@anti-slop-marketplace';        Repo = 'paslavskyi/anti-slop';         Sha = '539ed54c1bb7efb9799cf3b88a5cde7dd30b4988' }
    @{ Id = 'thermos@thermos-local';                  Repo = 'theocarranza/thermos-claude';  Sha = 'ffe74b3b2189276204970df4ec912d3cc9bd6b47' }
    @{ Id = 'anti-slop@anti-slop-luantaraschi';       Repo = 'luantaraschi/anti-slop';       Sha = 'c6605b26f259f65dfab4179bde9dbe880e5ff630'; Local = $true }
    @{ Id = 'antislop@antislop-miqdadbadjuber';       Repo = 'miqdadbadjuber/anti-slop';     Sha = '0e384b7bff3301c8ec56dea300330772fed28e6a'; Local = $true }
)

function Test-Cmd([string]$c) { [bool](Get-Command $c -ErrorAction SilentlyContinue) }

Write-Host "full-autodev stack" -ForegroundColor Cyan

foreach ($t in $Tools) {
    if (Test-Cmd $t.Cmd) { continue }
    if ($CheckOnly -or -not $t.Install -or -not (Test-Cmd 'uv')) {
        $script:Missing += $t.Cmd
        Write-Host "  ! falta $($t.Cmd)" -ForegroundColor Yellow
        continue
    }
    & $t.Install 2>&1 | Select-Object -Last 1 | Out-Host
    if (Test-Cmd $t.Cmd) { $script:Installed += $t.Cmd } else { $script:Missing += $t.Cmd }
}

# --- Antigravity: la extraccion SEMANTICA del grafo corre ahi (regla del usuario) ---------
# Claude solo hace `graphify update .` (AST, sin LLM). El pase semantico (docs, specs, vault)
# se lanza desde el agente de Antigravity con `/graphify .` en la raiz del proyecto.
$agSkill = Join-Path $env:USERPROFILE '.gemini\config\skills\graphify\SKILL.md'
$agApp   = Test-Path (Join-Path $env:LOCALAPPDATA 'Programs\Antigravity')
if (-not $agApp) {
    $script:Missing += 'Antigravity (app)'
    Write-Host "  ! falta Antigravity: sin el, el grafo queda solo con AST" -ForegroundColor Yellow
} elseif (-not (Test-Path $agSkill)) {
    if ($CheckOnly) { $script:Missing += 'graphify@antigravity' }
    elseif (Test-Cmd 'graphify') { & graphify install --platform antigravity 2>&1 | Select-Object -Last 1 | Out-Host; $script:Installed += 'graphify@antigravity' }
}

if (-not (Test-Cmd 'claude')) {
    Write-Host "  ! sin CLI claude: no se pueden verificar los plugins" -ForegroundColor Yellow
} else {
    $list = (& claude plugin list 2>&1) -join "`n"
    $localRoot = Join-Path $env:USERPROFILE '.claude\plugins-local'
    $mktRoot   = Join-Path $env:USERPROFILE '.claude\plugins\marketplaces'
    foreach ($p in $Plugins) {
        $mkt = $p.Id.Split('@')[1]
        if ($list -notmatch [regex]::Escape($p.Id)) {
            if ($CheckOnly) { $script:Missing += $p.Id; Write-Host "  ! falta plugin $($p.Id)" -ForegroundColor Yellow; continue }
            if ($p.Local) {
                $dir = Join-Path $localRoot $mkt
                if (-not (Test-Path $dir)) { git -c core.longpaths=true clone -q "https://github.com/$($p.Repo)" $dir }
                git -C $dir -c advice.detachedHead=false checkout -q $p.Sha
                $mf = Join-Path $dir '.claude-plugin\marketplace.json'
                $m = Get-Content $mf -Raw -Encoding UTF8 | ConvertFrom-Json
                $m.name = $mkt
                [IO.File]::WriteAllText($mf, ($m | ConvertTo-Json -Depth 20), (New-Object Text.UTF8Encoding $false))
                git -C $dir update-index --skip-worktree .claude-plugin/marketplace.json
                & claude plugin marketplace add $dir 2>&1 | Select-Object -Last 1 | Out-Host
            } else {
                & claude plugin marketplace add $p.Repo 2>&1 | Select-Object -Last 1 | Out-Host
            }
            & claude plugin install $p.Id --scope user 2>&1 | Select-Object -Last 1 | Out-Host
            $script:Installed += $p.Id
        }
        # deriva respecto del commit revisado
        $src = if ($p.Local) { Join-Path $localRoot $mkt } else { Join-Path $mktRoot $mkt }
        $head = (git -C $src rev-parse HEAD 2>$null)
        if ($head -and $head.Trim() -ne $p.Sha) {
            $script:Drift += "$($p.Id): instalado $($head.Trim().Substring(0,8)), revisado $($p.Sha.Substring(0,8))"
        }
    }
}

Write-Host ""
Write-Host "  instalados ahora : $(if ($script:Installed) { $script:Installed -join ', ' } else { 'nada' })"
if ($script:Missing) { Write-Host "  faltan           : $($script:Missing -join ', ')" -ForegroundColor Yellow }
if ($script:Drift) {
    Write-Host "  SIN REVISAR (commit distinto al revisado; leer skills/hooks antes de usar):" -ForegroundColor Yellow
    $script:Drift | ForEach-Object { Write-Host "    - $_" -ForegroundColor Yellow }
}
if (-not $script:Missing -and -not $script:Drift) { Write-Host "  stack completo y en los commits revisados" -ForegroundColor Green }
exit ([int]([bool]$script:Missing))
