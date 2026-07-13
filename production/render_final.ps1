param(
    [ValidateSet("desktop", "mobile")]
    [string]$Mode = "desktop",
    [ValidateRange(1, 256)]
    [int]$Samples = 64,
    [string]$Blender
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

& $Blender --background --factory-startup --python-exit-code 1 --python $Script -- --mode $Mode --samples $Samples
if ($LASTEXITCODE -ne 0) {
    throw "$Mode render failed with exit code $LASTEXITCODE"
}
