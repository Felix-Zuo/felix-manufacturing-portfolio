param(
    [ValidateSet("Proof", "Fallback", "Public")]
    [string]$Mode = "Proof",
    [string]$Python = "python",
    [string]$Ffmpeg
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$ShowcaseRoot = Split-Path -Parent $RepoRoot
$Generator = Join-Path $PSScriptRoot "control_room_loop\generate_loop.py"
$ResolvedFfmpeg = if ($Ffmpeg) {
    $Ffmpeg
} else {
    Join-Path $ShowcaseRoot "tools\ffmpeg-release-essentials\ffmpeg-8.1.2-essentials_build\bin\ffmpeg.exe"
}

if (-not (Test-Path -LiteralPath $Generator)) {
    throw "Control-room loop generator is missing: $Generator"
}
if (-not (Test-Path -LiteralPath $ResolvedFfmpeg)) {
    throw "FFmpeg is missing: $ResolvedFfmpeg"
}

$ModeArgument = $Mode.ToLowerInvariant()
& $Python $Generator --mode $ModeArgument --ffmpeg $ResolvedFfmpeg
if ($LASTEXITCODE -ne 0) {
    throw "Control-room $ModeArgument loop failed with exit code $LASTEXITCODE"
}
