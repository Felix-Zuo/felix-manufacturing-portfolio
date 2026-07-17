param(
    [string]$Ffmpeg,
    [ValidateRange(0, 51)]
    [int]$DesktopCrf = 21,
    [ValidateRange(0, 51)]
    [int]$MobileCrf = 22,
    [switch]$SkipStreams,
    [switch]$SkipLoops
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

$FrameRate = 24
$FrameCount = 912
$MediaDir = Join-Path $RepoRoot "public\media"
$HoldDir = Join-Path $MediaDir "holds"
$DesktopFrames = Join-Path $RepoRoot "production\renders\desktop-frames\frame-%04d.png"
$MobileFrames = Join-Path $RepoRoot "production\renders\mobile-frames\frame-%04d.png"
$DesktopStream = Join-Path $MediaDir "felix-journey-stream-desktop.mp4"
$MobileStream = Join-Path $MediaDir "felix-journey-stream-mobile.mp4"

New-Item -ItemType Directory -Force -Path $MediaDir, $HoldDir | Out-Null

function Assert-FrameSequence {
    param([string]$Mode)

    $FrameDir = Join-Path $RepoRoot "production\renders\$Mode-frames"
    $Missing = @(
        for ($Frame = 1; $Frame -le $FrameCount; $Frame++) {
            $FramePath = Join-Path $FrameDir ("frame-{0:D4}.png" -f $Frame)
            if (-not (Test-Path -LiteralPath $FramePath)) {
                $Frame
            }
        }
    )

    if ($Missing.Count -gt 0) {
        throw "$Mode render sequence is missing $($Missing.Count) frame(s)"
    }
}

function Invoke-Ffmpeg {
    param([string[]]$Arguments)

    & $Ffmpeg @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "ffmpeg failed with exit code $LASTEXITCODE"
    }
}

function New-StreamMaster {
    param(
        [string]$InputPattern,
        [string]$OutputPath,
        [string]$Scale,
        [int]$Crf
    )

    $Arguments = @(
        "-y",
        "-hide_banner",
        "-loglevel", "warning",
        "-framerate", "$FrameRate",
        "-start_number", "1",
        "-i", $InputPattern,
        "-frames:v", "$FrameCount",
        "-an",
        "-vf", "scale=$Scale`:flags=lanczos",
        "-c:v", "libx264",
        "-preset", "slow",
        "-crf", "$Crf",
        "-pix_fmt", "yuv420p",
        "-color_primaries", "bt709",
        "-color_trc", "bt709",
        "-colorspace", "bt709",
        "-color_range", "tv",
        "-movflags", "+faststart",
        "-flags", "+cgop",
        "-x264-params", "keyint=12:min-keyint=12:scenecut=0:open-gop=0:colorprim=bt709:transfer=bt709:colormatrix=bt709",
        "-g", "12",
        "-keyint_min", "12",
        "-sc_threshold", "0",
        $OutputPath
    )

    Invoke-Ffmpeg -Arguments $Arguments
}

function New-ForwardLoop {
    param(
        [string]$InputPath,
        [string]$OutputPath,
        [int]$StartFrame,
        [int]$ForwardFrames,
        [string]$Scale,
        [int]$Crf
    )

    $StartIndex = [Math]::Max($StartFrame - 1, 0)
    $EndIndex = [Math]::Min($StartIndex + $ForwardFrames, $FrameCount)
    $DurationSeconds = $ForwardFrames / $FrameRate
    $BlendSeconds = [Math]::Min(0.25, $DurationSeconds / 3.0)
    $BlendOffset = $DurationSeconds - $BlendSeconds
    $Filter = "[0:v]trim=start_frame=$StartIndex`:end_frame=$EndIndex,setpts=PTS-STARTPTS,split=2[base][firstSource];[firstSource]trim=end_frame=1,setpts=PTS-STARTPTS,tpad=stop_mode=clone`:stop_duration=$DurationSeconds[first];[base][first]xfade=transition=fade`:duration=$BlendSeconds`:offset=$BlendOffset,trim=end_frame=$ForwardFrames,setpts=PTS-STARTPTS,fps=$FrameRate,scale=$Scale`:flags=lanczos,format=yuv420p[loop]"

    $Arguments = @(
        "-y",
        "-hide_banner",
        "-loglevel", "warning",
        "-i", $InputPath,
        "-filter_complex", $Filter,
        "-map", "[loop]",
        "-an",
        "-c:v", "libx264",
        "-preset", "slow",
        "-crf", "$Crf",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "-g", "24",
        "-keyint_min", "24",
        "-sc_threshold", "0",
        $OutputPath
    )

    Invoke-Ffmpeg -Arguments $Arguments
}

Assert-FrameSequence -Mode "desktop"
Assert-FrameSequence -Mode "mobile"

if (-not $SkipStreams) {
    New-StreamMaster -InputPattern $DesktopFrames -OutputPath $DesktopStream -Scale "1600:900" -Crf $DesktopCrf
    New-StreamMaster -InputPattern $MobileFrames -OutputPath $MobileStream -Scale "720:1280" -Crf $MobileCrf
}

if (-not $SkipLoops) {
    if (-not (Test-Path -LiteralPath $DesktopStream) -or -not (Test-Path -LiteralPath $MobileStream)) {
        throw "Stream masters are required before building chapter loops"
    }

    $Chapters = @(
        @{ Id = "origin"; Frame = 1; Frames = 30 },
        @{ Id = "impact"; Frame = 169; Frames = 24 },
        @{ Id = "process"; Frame = 301; Frames = 36 },
        @{ Id = "notice"; Frame = 433; Frames = 24 },
        @{ Id = "takt"; Frame = 553; Frames = 36 },
        @{ Id = "visibility"; Frame = 673; Frames = 24 },
        @{ Id = "system"; Frame = 793; Frames = 24 },
        @{ Id = "close"; Frame = 877; Frames = 24 }
    )

    foreach ($Chapter in $Chapters) {
        $DesktopOutput = Join-Path $HoldDir "$($Chapter.Id)-desktop.mp4"
        $MobileOutput = Join-Path $HoldDir "$($Chapter.Id)-mobile.mp4"
        New-ForwardLoop -InputPath $DesktopStream -OutputPath $DesktopOutput -StartFrame $Chapter.Frame -ForwardFrames $Chapter.Frames -Scale "1600:900" -Crf 21
        New-ForwardLoop -InputPath $MobileStream -OutputPath $MobileOutput -StartFrame $Chapter.Frame -ForwardFrames $Chapter.Frames -Scale "720:1280" -Crf 22
    }
}

$Outputs = @($DesktopStream, $MobileStream)
$Outputs += Get-ChildItem -LiteralPath $HoldDir -Filter "*.mp4" | Select-Object -ExpandProperty FullName
Get-Item -LiteralPath $Outputs | Select-Object FullName, Length
