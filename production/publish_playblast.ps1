param(
    [ValidateSet("desktop", "mobile")]
    [string]$Mode = "desktop",
    [ValidateSet(1, 2)]
    [int]$RenderStep = 1,
    [ValidateRange(0.001, 86400.0)]
    [double]$Duration = 38.0,
    [string]$Ffmpeg,
    [string]$Ffprobe
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$ShowcaseRoot = Split-Path -Parent $RepoRoot
$Ffmpeg = if ($Ffmpeg) {
    $Ffmpeg
} else {
    Join-Path $ShowcaseRoot "tools\ffmpeg-release-essentials\ffmpeg-8.1.2-essentials_build\bin\ffmpeg.exe"
}
$Ffprobe = if ($Ffprobe) {
    $Ffprobe
} else {
    Join-Path (Split-Path -Parent $Ffmpeg) "ffprobe.exe"
}

$FrameRate = 24
$ExpectedFrames = [int][Math]::Round($Duration * $FrameRate)
$PlayblastDir = Join-Path $RepoRoot "production\renders\playblast"
$MediaDir = Join-Path $RepoRoot "public\media"
$SourcePattern = "felix-journey-$Mode-playblast*.mp4"
$Source = Get-ChildItem -LiteralPath $PlayblastDir -Filter $SourcePattern |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

if (-not $Source) {
    throw "No $Mode playblast matches $SourcePattern in $PlayblastDir"
}

New-Item -ItemType Directory -Force -Path $MediaDir | Out-Null
$Output = Join-Path $MediaDir "felix-journey-$Mode.mp4"
$TemporaryOutput = Join-Path $PlayblastDir "felix-journey-$Mode-publish-temp.mp4"
$PosterName = if ($Mode -eq "desktop") {
    "felix-journey-poster.webp"
} else {
    "felix-journey-mobile-poster.webp"
}
$PosterOutput = Join-Path $MediaDir $PosterName
$SourceProbeJson = & $Ffprobe -v error -show_entries "format=duration" -of json $Source.FullName
if ($LASTEXITCODE -ne 0) {
    throw "$Mode source probe failed with exit code $LASTEXITCODE"
}
$SourceDuration = [double](($SourceProbeJson | ConvertFrom-Json).format.duration)
$Retiming = ""
if ($RenderStep -eq 2) {
    if ([Math]::Abs($SourceDuration - ($Duration / 2.0)) -le 0.05) {
        # Compatibility with playblasts created before build_scene reasserted
        # the half-rate container fps after lookdev.
        $Retiming = "setpts=2.0*PTS,"
    } elseif ([Math]::Abs($SourceDuration - $Duration) -gt 0.05) {
        throw "$Mode half-rate source duration is $SourceDuration; expected $Duration or $($Duration / 2.0)"
    }
}
$Filter = if ($RenderStep -eq 2) {
    "${Retiming}minterpolate=fps=24:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,tpad=stop_mode=clone:stop_duration=0.125"
} else {
    "fps=24,tpad=stop_mode=clone:stop_duration=0.125"
}

& $Ffmpeg `
    -y `
    -i $Source.FullName `
    -an `
    -vf $Filter `
    -frames:v $ExpectedFrames `
    -c:v libx264 `
    -preset medium `
    -crf 18 `
    -pix_fmt yuv420p `
    -color_primaries bt709 `
    -color_trc bt709 `
    -colorspace bt709 `
    -color_range tv `
    -movflags +faststart `
    -flags +cgop `
    -x264-params "keyint=12:min-keyint=12:scenecut=0:open-gop=0:colorprim=bt709:transfer=bt709:colormatrix=bt709" `
    -g 12 `
    -keyint_min 12 `
    -sc_threshold 0 `
    $TemporaryOutput

if ($LASTEXITCODE -ne 0) {
    throw "$Mode playblast publishing failed with exit code $LASTEXITCODE"
}

$ProbeJson = & $Ffprobe `
    -v error `
    -count_frames `
    -select_streams v:0 `
    -show_entries "stream=nb_read_frames,avg_frame_rate,width,height:format=duration" `
    -of json `
    $TemporaryOutput
if ($LASTEXITCODE -ne 0) {
    throw "$Mode playblast probe failed with exit code $LASTEXITCODE"
}
$Probe = $ProbeJson | ConvertFrom-Json
$FrameCount = [int]$Probe.streams[0].nb_read_frames
$EncodedDuration = [double]$Probe.format.duration
if ($FrameCount -ne $ExpectedFrames) {
    throw "$Mode output has $FrameCount frames; expected $ExpectedFrames"
}
if ([Math]::Abs($EncodedDuration - $Duration) -gt 0.001) {
    throw "$Mode output duration is $EncodedDuration; expected $Duration"
}

Copy-Item -LiteralPath $TemporaryOutput -Destination $Output -Force
Remove-Item -LiteralPath $TemporaryOutput -Force

$PosterTime = [Math]::Min(3.75, [Math]::Max($Duration - 0.05, 0.0))
& $Ffmpeg `
    -y `
    -ss $PosterTime `
    -i $Output `
    -frames:v 1 `
    -c:v libwebp `
    -quality 88 `
    $PosterOutput
if ($LASTEXITCODE -ne 0) {
    throw "$Mode poster generation failed with exit code $LASTEXITCODE"
}

[pscustomobject]@{
    Mode = $Mode
    Source = $Source.FullName
    Output = $Output
    Width = [int]$Probe.streams[0].width
    Height = [int]$Probe.streams[0].height
    Frames = $FrameCount
    FrameRate = $Probe.streams[0].avg_frame_rate
    Duration = $EncodedDuration
}
