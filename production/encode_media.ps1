param(
    [ValidateSet("desktop", "mobile")]
    [string]$Mode = "desktop",
    [string]$Ffmpeg,
    [ValidateRange(0.001, 86400.0)]
    [double]$Duration = 38.0,
    [ValidateRange(0, 51)]
    [int]$MainCrf = 18,
    [ValidateRange(0, 51)]
    [int]$FallbackCrf = 21,
    [switch]$SkipFallback
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
$FallbackOutput = Join-Path $MediaDir "felix-journey-$Mode-720.mp4"
$FrameRate = 24
$FrameCount = $Duration * $FrameRate

if ([Math]::Abs($FrameCount - [Math]::Round($FrameCount)) -gt 0.000001) {
    throw "Duration $Duration does not resolve to a whole frame at $FrameRate fps"
}

$ExpectedFrameCount = [int][Math]::Round($FrameCount)
$MissingFrames = @(
    for ($Frame = 1; $Frame -le $ExpectedFrameCount; $Frame++) {
        $FramePath = Join-Path $FrameDir ("frame-{0:D4}.png" -f $Frame)
        if (-not (Test-Path -LiteralPath $FramePath)) {
            $Frame
        }
    }
)

New-Item -ItemType Directory -Force -Path $MediaDir | Out-Null

if ($MissingFrames.Count -gt 0) {
    $MissingPreview = ($MissingFrames | Select-Object -First 8 | ForEach-Object { "F{0:D4}" -f $_ }) -join ", "
    throw "Missing $($MissingFrames.Count) of $ExpectedFrameCount required render frames in $FrameDir ($MissingPreview)"
}

& $Ffmpeg `
    -y `
    -framerate $FrameRate `
    -start_number 1 `
    -i (Join-Path $FrameDir "frame-%04d.png") `
    -frames:v $ExpectedFrameCount `
    -an `
    -c:v libx264 `
    -preset slow `
    -crf $MainCrf `
    -pix_fmt yuv420p `
    -color_primaries bt709 `
    -color_trc bt709 `
    -colorspace bt709 `
    -color_range tv `
    -movflags +faststart `
    -flags +cgop `
    -x264-params "keyint=6:min-keyint=6:scenecut=0:open-gop=0:colorprim=bt709:transfer=bt709:colormatrix=bt709" `
    -g 6 `
    -keyint_min 6 `
    -sc_threshold 0 `
    $Output

if ($LASTEXITCODE -ne 0) {
    throw "$Mode video encoding failed with exit code $LASTEXITCODE"
}

if (-not $SkipFallback) {
    $FallbackScale = if ($Mode -eq "desktop") { "1280:720" } else { "720:1280" }
    & $Ffmpeg `
        -y `
        -framerate $FrameRate `
        -start_number 1 `
        -i (Join-Path $FrameDir "frame-%04d.png") `
        -frames:v $ExpectedFrameCount `
        -an `
        -vf "scale=$FallbackScale`:flags=lanczos" `
        -c:v libx264 `
        -preset slow `
        -crf $FallbackCrf `
        -pix_fmt yuv420p `
        -color_primaries bt709 `
        -color_trc bt709 `
        -colorspace bt709 `
        -color_range tv `
        -movflags +faststart `
        -flags +cgop `
        -x264-params "keyint=6:min-keyint=6:scenecut=0:open-gop=0:colorprim=bt709:transfer=bt709:colormatrix=bt709" `
        -g 6 `
        -keyint_min 6 `
        -sc_threshold 0 `
        $FallbackOutput

    if ($LASTEXITCODE -ne 0) {
        throw "$Mode fallback encoding failed with exit code $LASTEXITCODE"
    }
}

$PosterFrameNumber = [Math]::Min(91, $ExpectedFrameCount)
$PosterInput = Join-Path $FrameDir ("frame-{0:D4}.png" -f $PosterFrameNumber)
$PosterName = if ($Mode -eq "desktop") { "felix-journey-poster.webp" } else { "felix-journey-mobile-poster.webp" }
$PosterOutput = Join-Path $MediaDir $PosterName

& $Ffmpeg `
    -y `
    -i $PosterInput `
    -frames:v 1 `
    -c:v libwebp `
    -quality 88 `
    $PosterOutput

if ($LASTEXITCODE -ne 0) {
    throw "$Mode poster encoding failed with exit code $LASTEXITCODE"
}

$Outputs = @($Output, $PosterOutput)
if (-not $SkipFallback) {
    $Outputs += $FallbackOutput
}
Get-Item $Outputs | Select-Object FullName, Length
