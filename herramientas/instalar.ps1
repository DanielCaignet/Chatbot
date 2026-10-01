<#
.SYNOPSIS
  Prepara un PC para continuar chatbot-richard con Claude Code.

.DESCRIPTION
  Idempotente. Ejecutar desde la raiz del repo:
    powershell -ExecutionPolicy Bypass -File herramientas\instalar.ps1
    powershell -ExecutionPolicy Bypass -File herramientas\instalar.ps1 -SoloVerificar

  1. Verifica los requisitos del sistema (git, node, python, uv, claude).
  2. Copia la skill full-autodev de herramientas\ a ~\.claude\skills\ (respalda la anterior).
  3. Ejecuta stack.ps1 de la skill: graphify, Spec Kit, markitdown y los plugins de Claude Code
     fijados al commit revisado.
  4. Instala los hooks git del repo (compuertas pre-commit y reconstruccion del grafo).
  5. Reconstruye el grafo (graphify update .).
#>
[CmdletBinding()]
param([switch]$SoloVerificar)

$ErrorActionPreference = 'Continue'
$Repo  = Split-Path -Parent $PSScriptRoot
$Falta = @()

function Test-Cmd([string]$c) { [bool](Get-Command $c -ErrorAction SilentlyContinue) }

Write-Host "chatbot-richard: preparacion del PC" -ForegroundColor Cyan

# 1. Requisitos del sistema: no se instalan solos, se indica el comando.
$Requisitos = @(
    @{ Cmd = 'git';    Como = 'winget install --id Git.Git -e' }
    @{ Cmd = 'node';   Como = 'winget install --id OpenJS.NodeJS.LTS -e' }
    @{ Cmd = 'python'; Como = 'winget install --id Python.Python.3.13 -e' }
    @{ Cmd = 'uv';     Como = 'winget install --id astral-sh.uv -e' }
    @{ Cmd = 'claude'; Como = 'npm install -g @anthropic-ai/claude-code   (luego: claude update)' }
    @{ Cmd = 'gh';     Como = 'winget install --id GitHub.cli -e   (luego: gh auth login)' }
    @{ Cmd = 'ssh';    Como = 'Configuracion > Sistema > Caracteristicas opcionales > Cliente OpenSSH' }
)
foreach ($r in $Requisitos) {
    if (Test-Cmd $r.Cmd) {
        $flag = if ($r.Cmd -eq 'ssh') { '-V' } else { '--version' }
        $v = (& $r.Cmd $flag 2>&1 | Select-Object -First 1)
        Write-Host "  ok   $($r.Cmd)  $v"
    } else {
        $Falta += $r.Cmd
        Write-Host "  FALTA $($r.Cmd)  ->  $($r.Como)" -ForegroundColor Yellow
    }
}
if ($Falta | Where-Object { $_ -in 'git','python','uv','claude' }) {
    Write-Host ""
    Write-Host "Instala lo que falta, abre una terminal nueva y vuelve a ejecutar este script." -ForegroundColor Yellow
    exit 1
}

# 2. Skill full-autodev en el perfil del usuario (sus scripts usan esa ruta).
$SkillSrc = Join-Path $PSScriptRoot 'full-autodev'
$SkillDst = Join-Path $env:USERPROFILE '.claude\skills\full-autodev'
if ($SoloVerificar) {
    if (Test-Path (Join-Path $SkillDst 'SKILL.md')) { Write-Host "  ok   skill full-autodev" }
    else { Write-Host "  FALTA skill full-autodev" -ForegroundColor Yellow; $Falta += 'full-autodev' }
} else {
    if (Test-Path $SkillDst) {
        $bak = "$SkillDst.bak-$(Get-Date -Format yyyyMMdd-HHmmss)"
        Move-Item $SkillDst $bak
        Write-Host "  skill anterior respaldada en $bak"
    }
    New-Item -ItemType Directory -Force (Split-Path $SkillDst) | Out-Null
    Copy-Item $SkillSrc $SkillDst -Recurse
    Write-Host "  ok   skill full-autodev copiada a $SkillDst"
}

# 3. CLIs y plugins fijados (lo hace la propia skill).
$Stack = Join-Path $SkillDst 'references\stack.ps1'
if (Test-Path $Stack) {
    if ($SoloVerificar) { & $Stack -CheckOnly } else { & $Stack }
}

# 4. Hooks git (no viajan con el repo).
$Hooks = Join-Path $Repo '.git\hooks'
if (-not $SoloVerificar -and (Test-Path $Hooks)) {
    Copy-Item (Join-Path $PSScriptRoot 'hooks\pre-commit') (Join-Path $Hooks 'pre-commit') -Force
    Write-Host "  ok   hook pre-commit (compuertas gates.py)"
    if (Test-Cmd 'graphify') {
        Push-Location $Repo
        & graphify hook install 2>&1 | Select-Object -Last 1 | Out-Host
        # 5. Grafo: es derivado y no esta en git; se reconstruye aca.
        & graphify update . 2>&1 | Select-Object -Last 2 | Out-Host
        Pop-Location
    }
}

Write-Host ""
if ($Falta) { Write-Host "Pendiente: $($Falta -join ', ')" -ForegroundColor Yellow }
else { Write-Host "Listo. Abre Claude Code en la raiz del repo y escribe: /full-autodev --resume" -ForegroundColor Green }
Write-Host "Opcional: hook que obliga a usar context-mode, ver docs\COMO-CONTINUAR.md (seccion 4)."
