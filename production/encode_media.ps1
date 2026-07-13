param(
    [ValidateSet("desktop", "mobile")]
    [string]$Mode = "desktop",
    [string]$Ffmpeg
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$ShowcaseRoot = Split-Path -Parent $RepoRoot
$Ffmpeg = if ($Ffmpeg) {
    $Ffmpeg
} else {
    Join-Path $ShowcaseRoot "tools\ffmpeg-release-essentials\ffmpeg-8.1.2-essentials_build\bin\ffmpeg.exe"
}
$FrameDir = Join-Path $RepoRoot "production\renders\$Mode-frames"
$MediaDir = Join-Path $RepoRoot "public\media"
$Output = Join-Path $MediaDir "felix-journey-$Mode.mp4"

New-Item -ItemType Directory -Force -Path $MediaDir | Out-Null

if (-not (Test-Path (Join-Path $FrameDir "frame-0001.png"))) {
    throw "Missing render frames in $FrameDir"
}

& $Ffmpeg `
    -y `
    -framerate 24 `
    -start_number 1 `
    -i (Join-Path $FrameDir "frame-%04d.png") `
    -an `
    -c:v libx264 `
    -preset slow `
    -crf 19 `
    -pix_fmt yuv420p `
    -movflags +faststart `
    -g 12 `
    -keyint_min 12 `
    -sc_threshold 0 `
    $Output

if ($LASTEXITCODE -ne 0) {
    throw "$Mode video encoding failed with exit code $LASTEXITCODE"
}

if ($Mode -eq "desktop") {
    & $Ffmpeg `
        -y `
        -i (Join-Path $FrameDir "frame-0054.png") `
        -frames:v 1 `
        -c:v libwebp `
        -quality 88 `
        (Join-Path $MediaDir "felix-journey-poster.webp")

    if ($LASTEXITCODE -ne 0) {
        throw "Poster encoding failed with exit code $LASTEXITCODE"
    }
} else {
    & $Ffmpeg `
        -y `
        -i (Join-Path $FrameDir "frame-0054.png") `
        -frames:v 1 `
        -c:v libwebp `
        -quality 88 `
        (Join-Path $MediaDir "felix-journey-mobile-poster.webp")

    if ($LASTEXITCODE -ne 0) {
        throw "Mobile poster encoding failed with exit code $LASTEXITCODE"
    }
}

Get-Item $Output | Select-Object FullName, Length
