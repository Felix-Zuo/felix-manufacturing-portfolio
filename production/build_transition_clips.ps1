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

if (-not (Test-Path -LiteralPath $Ffmpeg)) {
    throw "ffmpeg was not found at $Ffmpeg"
}

$OutputFrameRate = 24
$OutputDir = Join-Path $RepoRoot "public\media\transitions"
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

$Segments = @(
    @{ From = "origin"; To = "impact"; Start = 1; End = 228 },
    @{ From = "impact"; To = "process"; Start = 228; End = 301 },
    @{ From = "process"; To = "notice"; Start = 301; End = 433 },
    @{ From = "notice"; To = "takt"; Start = 433; End = 553 },
    @{ From = "takt"; To = "visibility"; Start = 553; End = 673 },
    @{ From = "visibility"; To = "system"; Start = 673; End = 793 },
    @{ From = "system"; To = "contact"; Start = 793; End = 904 }
)

function Invoke-Ffmpeg {
    param([string[]]$Arguments)

    & $Ffmpeg @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "ffmpeg failed with exit code $LASTEXITCODE"
    }
}

foreach ($Segment in $Segments) {
    $FrameCount = $Segment.End - $Segment.Start + 1

    foreach ($Profile in @(
        @{ Name = "desktop"; Scale = "1600:900"; Crf = $DesktopCrf },
        @{ Name = "mobile"; Scale = "720:1280"; Crf = $MobileCrf }
    )) {
        $InputPattern = Join-Path $RepoRoot (
            "production\renders\{0}-frames\frame-%04d.png" -f $Profile.Name
        )
        $FirstFrame = Join-Path $RepoRoot (
            "production\renders\{0}-frames\frame-{1:D4}.png" -f $Profile.Name, $Segment.Start
        )
        $LastFrame = Join-Path $RepoRoot (
            "production\renders\{0}-frames\frame-{1:D4}.png" -f $Profile.Name, $Segment.End
        )
        if (-not (Test-Path -LiteralPath $FirstFrame) -or -not (Test-Path -LiteralPath $LastFrame)) {
            throw "Missing source frames for $($Segment.From)-$($Segment.To) $($Profile.Name)"
        }

        $OutputPath = Join-Path $OutputDir (
            "{0}-to-{1}-{2}.mp4" -f $Segment.From, $Segment.To, $Profile.Name
        )

        $Arguments = @(
            "-y",
            "-hide_banner",
            "-loglevel", "warning",
            "-framerate", "$OutputFrameRate",
            "-start_number", "$($Segment.Start)",
            "-i", $InputPattern,
            "-frames:v", "$FrameCount",
            "-an",
            "-vf", "scale=$($Profile.Scale):flags=lanczos,format=yuv420p",
            "-c:v", "libx264",
            "-preset", "slow",
            "-crf", "$($Profile.Crf)",
            "-profile:v", "high",
            "-pix_fmt", "yuv420p",
            "-color_primaries", "bt709",
            "-color_trc", "bt709",
            "-colorspace", "bt709",
            "-color_range", "tv",
            "-movflags", "+faststart",
            "-flags", "+cgop",
            "-x264-params", "keyint=24:min-keyint=12:scenecut=0:open-gop=0:colorprim=bt709:transfer=bt709:colormatrix=bt709",
            "-g", "24",
            "-keyint_min", "12",
            "-sc_threshold", "0",
            $OutputPath
        )

        Invoke-Ffmpeg -Arguments $Arguments
    }
}

Get-ChildItem -LiteralPath $OutputDir -Filter "*.mp4" |
    Sort-Object Name |
    Select-Object Name, Length
