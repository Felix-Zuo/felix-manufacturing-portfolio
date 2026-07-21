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

$InputPath = Join-Path $RepoRoot "production\renders\hold-loops\mobile\process\frame-%04d.png"
$OutputPath = Join-Path $RepoRoot "public\media\holds\process-mobile.mp4"

$FirstFrame = $InputPath -replace "%04d", "0001"
if (-not (Test-Path -LiteralPath $FirstFrame)) {
    throw "Mobile process loop frames were not found at $FirstFrame"
}

& $Ffmpeg `
    -y `
    -hide_banner `
    -loglevel warning `
    -framerate 24 `
    -start_number 1 `
    -i $InputPath `
    -filter_complex "[0:v]split=2[base][firstSource];[firstSource]trim=end_frame=1,setpts=PTS-STARTPTS,tpad=stop_mode=clone`:stop_duration=1.5[first];[base][first]xfade=transition=fade`:duration=0.25`:offset=1.25,trim=end_frame=36,setpts=PTS-STARTPTS,fps=24,scale=720:1280`:flags=lanczos,format=yuv420p[loop]" `
    -map "[loop]" `
    -an `
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
