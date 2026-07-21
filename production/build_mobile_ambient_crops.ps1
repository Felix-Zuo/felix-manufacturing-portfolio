param(
    [string]$Ffmpeg,
    [ValidateRange(0, 51)]
    [int]$Crf = 22
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$ShowcaseRoot = Split-Path -Parent $RepoRoot
$Ffmpeg = if ($Ffmpeg) {
    $Ffmpeg
} else {
    Join-Path $ShowcaseRoot "tools\ffmpeg-release-essentials\ffmpeg-8.1.2-essentials_build\bin\ffmpeg.exe"
}

if (-not (Test-Path -LiteralPath $Ffmpeg)) {
    throw "ffmpeg was not found at $Ffmpeg"
}

$InputPath = Join-Path $RepoRoot "public\media\holds\process-desktop.mp4"
$OutputPath = Join-Path $RepoRoot "public\media\holds\process-mobile.mp4"

if (-not (Test-Path -LiteralPath $InputPath)) {
    throw "Desktop process loop was not found at $InputPath"
}

& $Ffmpeg `
    -y `
    -hide_banner `
    -loglevel warning `
    -i $InputPath `
    -an `
    -vf "crop=506:900:600:0,scale=720:1280:flags=lanczos,format=yuv420p" `
    -c:v libx264 `
    -preset slow `
    -crf $Crf `
    -pix_fmt yuv420p `
    -movflags +faststart `
    -g 24 `
    -keyint_min 24 `
    -sc_threshold 0 `
    $OutputPath

if ($LASTEXITCODE -ne 0) {
    throw "ffmpeg failed with exit code $LASTEXITCODE"
}

Get-Item -LiteralPath $OutputPath | Select-Object FullName, Length
