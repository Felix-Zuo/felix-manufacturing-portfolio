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
$MediaRoot = Join-Path $RepoRoot "public\media\transitions"

$Segments = @(
    @{ From = "origin"; To = "impact" },
    @{ From = "impact"; To = "process" },
    @{ From = "process"; To = "notice" },
    @{ From = "notice"; To = "takt" },
    @{ From = "takt"; To = "visibility" },
    @{ From = "visibility"; To = "system" },
    @{ From = "system"; To = "contact" }
)

foreach ($Segment in $Segments) {
    foreach ($Profile in @(
        @{ Name = "desktop"; Crf = $DesktopCrf },
        @{ Name = "mobile"; Crf = $MobileCrf }
    )) {
        $Input = Join-Path $MediaRoot "$($Segment.From)-to-$($Segment.To)-$($Profile.Name).mp4"
        $Output = Join-Path $MediaRoot "$($Segment.To)-to-$($Segment.From)-$($Profile.Name).mp4"
        if (-not (Test-Path -LiteralPath $Input)) {
            throw "Missing forward transition $Input"
        }

        & $Ffmpeg `
            -y `
            -hide_banner `
            -loglevel warning `
            -i $Input `
            -an `
            -vf "reverse,setpts=PTS-STARTPTS,fps=30,format=yuv420p" `
            -c:v libx264 `
            -preset slow `
            -crf $Profile.Crf `
            -pix_fmt yuv420p `
            -color_primaries bt709 `
            -color_trc bt709 `
            -colorspace bt709 `
            -movflags +faststart `
            -g 30 `
            -keyint_min 15 `
            -sc_threshold 0 `
            $Output

        if ($LASTEXITCODE -ne 0) {
            throw "Reverse transition failed for $($Segment.To)-to-$($Segment.From) $($Profile.Name)"
        }
    }
}

Get-ChildItem -LiteralPath $MediaRoot -Filter "*.mp4" |
    Sort-Object Name |
    Select-Object Name, Length
