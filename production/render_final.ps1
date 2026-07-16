param(
    [ValidateSet("desktop", "mobile")]
    [string]$Mode = "desktop",
    [ValidateRange(1, 256)]
    [int]$Samples = 64,
    [ValidateRange(0, 7680)]
    [int]$Width = 0,
    [ValidateRange(0, 7680)]
    [int]$Height = 0,
    [ValidateRange(0, 100000)]
    [int]$RenderStart = 0,
    [ValidateRange(0, 100000)]
    [int]$RenderEnd = 0,
    [string]$Blender,
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

$Arguments = @(
    "--background",
    "--factory-startup",
    "--python-exit-code", "1",
    "--python", $Script,
    "--",
    "--mode", $Mode,
    "--duration", $Duration,
    "--samples", $Samples
)
if (($Width -eq 0) -xor ($Height -eq 0)) {
    throw "Width and Height must be provided together"
}
if ($Width -gt 0) {
    $Arguments += @("--width", $Width, "--height", $Height)
}
if (($RenderStart -eq 0) -xor ($RenderEnd -eq 0)) {
    throw "RenderStart and RenderEnd must be provided together"
}
if ($RenderStart -gt 0) {
    if ($RenderEnd -lt $RenderStart) {
        throw "RenderEnd must be greater than or equal to RenderStart"
    }
    $Arguments += @("--render-start", $RenderStart, "--render-end", $RenderEnd)
}

& $Blender @Arguments
if ($LASTEXITCODE -ne 0) {
    throw "$Mode render failed with exit code $LASTEXITCODE"
}
