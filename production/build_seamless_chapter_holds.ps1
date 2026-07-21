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

$Chapters = @(
    @{ Id = "origin"; Start = 1; Frames = 60 },
    @{ Id = "notice"; Start = 433; Frames = 36 },
    @{ Id = "takt"; Start = 553; Frames = 48 },
    @{ Id = "visibility"; Start = 673; Frames = 36 },
    @{ Id = "system"; Start = 793; Frames = 36 },
    @{ Id = "close"; Start = 877; Frames = 36 }
)

foreach ($Profile in @(
    @{ Name = "desktop"; Scale = "1600:900"; Crf = $DesktopCrf },
    @{ Name = "mobile"; Scale = "720:1280"; Crf = $MobileCrf }
)) {
    $Master = Join-Path $MediaRoot "felix-journey-stream-$($Profile.Name).mp4"
    if (-not (Test-Path -LiteralPath $Master)) {
        throw "Missing journey stream $Master"
    }

    foreach ($Chapter in $Chapters) {
        $StartIndex = [Math]::Max($Chapter.Start - 1, 0)
        $EndIndex = $StartIndex + $Chapter.Frames
        $Output = Join-Path $HoldRoot "$($Chapter.Id)-$($Profile.Name).mp4"
        $Filter = "[0:v]trim=start_frame=$StartIndex`:end_frame=$EndIndex,setpts=PTS-STARTPTS,split=2[f][r0];[r0]reverse,setpts=PTS-STARTPTS[r];[f][r]concat=n=2`:v=1`:a=0,fps=24,scale=$($Profile.Scale)`:flags=lanczos,format=yuv420p[loop]"

        & $Ffmpeg `
            -y `
            -hide_banner `
            -loglevel warning `
            -i $Master `
            -filter_complex $Filter `
            -map "[loop]" `
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
            throw "Seamless hold failed for $($Chapter.Id) $($Profile.Name)"
        }
    }
}

Get-ChildItem -LiteralPath $HoldRoot -Filter "*.mp4" |
    Sort-Object Name |
    Select-Object Name, Length
