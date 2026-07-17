param(
    [ValidateSet("desktop", "mobile")]
    [string]$Mode = "desktop",
    [ValidateRange(1, 256)]
    [int]$Samples = 64,
    [string]$Blender,
    [ValidateRange(0.001, 86400.0)]
    [double]$Duration = 38.0,
    [ValidateRange(1, 1000000)]
    [int]$FrameStart = 1,
    [ValidateRange(0, 1000000)]
    [int]$FrameEnd = 0,
    [switch]$Resume
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
$FullFrameEnd = [int][Math]::Round($Duration * 24)
$ResolvedFrameEnd = if ($FrameEnd -eq 0) { $FullFrameEnd } else { $FrameEnd }
if ($FrameStart -gt $ResolvedFrameEnd -or $ResolvedFrameEnd -gt $FullFrameEnd) {
    throw "Frame range must be within 1-$FullFrameEnd, got $FrameStart-$ResolvedFrameEnd"
}

$Arguments = @(
    "--background",
    "--factory-startup",
    "--python-exit-code", "1",
    "--python", $Script,
    "--",
    "--mode", $Mode,
    "--duration", $Duration,
    "--samples", $Samples,
    "--frame-start", $FrameStart,
    "--frame-end", $ResolvedFrameEnd
)
if ($Resume) {
    $Arguments += "--resume"
}

& $Blender @Arguments
if ($LASTEXITCODE -ne 0) {
    throw "$Mode render failed with exit code $LASTEXITCODE"
}
