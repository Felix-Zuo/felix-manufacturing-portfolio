param(
    [string]$Ffmpeg,
    [ValidateRange(0, 100)]
    [int]$DesktopQuality = 86,
    [ValidateRange(0, 100)]
    [int]$MobileQuality = 84
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

$OutputDir = Join-Path $RepoRoot "public\media\chapters"
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

$Chapters = @(
    @{ Id = "origin"; Frame = 1 },
    @{ Id = "impact"; Frame = 228 },
    @{ Id = "process"; Frame = 301 },
    @{ Id = "notice"; Frame = 433 },
    @{ Id = "takt"; Frame = 553 },
    @{ Id = "visibility"; Frame = 673 },
    @{ Id = "system"; Frame = 793 },
    @{ Id = "close"; Frame = 904 }
)

foreach ($Chapter in $Chapters) {
    foreach ($Profile in @(
        @{ Name = "desktop"; Quality = $DesktopQuality },
        @{ Name = "mobile"; Quality = $MobileQuality }
    )) {
        $SourceProfile = $Profile.Name
        $InputPath = Join-Path $RepoRoot (
            "production\renders\{0}-frames\frame-{1:D4}.png" -f $SourceProfile, $Chapter.Frame
        )
        $OutputPath = Join-Path $OutputDir (
            "{0}-{1}.webp" -f $Chapter.Id, $Profile.Name
        )

        if (-not (Test-Path -LiteralPath $InputPath)) {
            throw "Missing chapter source frame: $InputPath"
        }

        $Arguments = @(
            "-y",
            "-hide_banner",
            "-loglevel", "warning",
            "-i", $InputPath
        )
        $Arguments += @(
            "-frames:v", "1",
            "-c:v", "libwebp",
            "-quality", "$($Profile.Quality)",
            "-compression_level", "6",
            $OutputPath
        )

        & $Ffmpeg @Arguments

        if ($LASTEXITCODE -ne 0) {
            throw "ffmpeg failed for $($Chapter.Id) $($Profile.Name)"
        }
    }
}

Get-ChildItem -LiteralPath $OutputDir -Filter "*.webp" |
    Sort-Object Name |
    Select-Object Name, Length
