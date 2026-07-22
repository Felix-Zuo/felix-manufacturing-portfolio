param(
    [string]$Ffmpeg,
    [ValidateRange(0, 51)]
    [int]$DesktopCrf = 21,
    [ValidateRange(0, 51)]
    [int]$MobileCrf = 22
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$ShowcaseRoot = Split-Path -Parent $RepoRoot
$Ffmpeg = if ($Ffmpeg) {
    $Ffmpeg
} else {
    Join-Path $ShowcaseRoot "tools\ffmpeg-release-essentials\ffmpeg-8.1.2-essentials_build\bin\ffmpeg.exe"
}
$MediaRoot = Join-Path $RepoRoot "public\media"
$HoldRoot = Join-Path $MediaRoot "holds"
$HoldSourceRoot = Join-Path $MediaRoot "hold-sources"

$Chapters = @(
    "origin",
    "notice",
    "takt",
    "visibility",
    "system",
    "close"
)

foreach ($Profile in @(
    @{ Name = "desktop"; Scale = "1600:900"; Crf = $DesktopCrf },
    @{ Name = "mobile"; Scale = "720:1280"; Crf = $MobileCrf }
)) {
    foreach ($Chapter in $Chapters) {
        $Source = Join-Path $HoldSourceRoot "$Chapter-$($Profile.Name).mp4"
        if (-not (Test-Path -LiteralPath $Source)) {
            throw "Missing dedicated fixed-camera environmental loop $Source"
        }
        $Output = Join-Path $HoldRoot "$Chapter-$($Profile.Name).mp4"
        $Filter = "fps=24,scale=$($Profile.Scale)`:flags=lanczos,format=yuv420p"

        & $Ffmpeg `
            -y `
            -hide_banner `
            -loglevel warning `
            -i $Source `
            -vf $Filter `
            -an `
            -c:v libx264 `
            -preset slow `
            -crf $Profile.Crf `
            -pix_fmt yuv420p `
            -movflags +faststart `
            -g 24 `
            -keyint_min 24 `
            -sc_threshold 0 `
            $Output

        if ($LASTEXITCODE -ne 0) {
            throw "Environmental hold encode failed for $Chapter $($Profile.Name)"
        }
    }
}

Get-ChildItem -LiteralPath $HoldRoot -Filter "*.mp4" |
    Sort-Object Name |
    Select-Object Name, Length
