param(
    [string]$Blender,
    [switch]$Mobile,
    [int]$Samples = 12,
    [ValidateSet(1, 2)]
    [int]$RenderStep = 1,
    [ValidateRange(0.001, 86400.0)]
    [double]$Duration = 38.0
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$ShowcaseRoot = Split-Path -Parent $RepoRoot
$Blender = if ($Blender) {
    $Blender
} else {
    Join-Path $ShowcaseRoot "tools\blender-4.5.11-windows-x64\blender.exe"
}
$Script = Join-Path $RepoRoot "production\blender\build_scene.py"
$Mode = if ($Mobile) { "playblast-mobile" } else { "playblast" }

& $Blender --background --factory-startup --python-exit-code 1 --python $Script -- --mode $Mode --duration $Duration --samples $Samples --render-step $RenderStep
if ($LASTEXITCODE -ne 0) {
    throw "$Mode render failed with exit code $LASTEXITCODE"
}
