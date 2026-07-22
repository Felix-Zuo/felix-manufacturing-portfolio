$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$HoldRoot = Join-Path $RepoRoot "public\media\holds"
$RetiredChapters = @(
    "origin",
    "impact",
    "notice",
    "takt",
    "visibility",
    "system",
    "close"
)

$Rejected = foreach ($Profile in @("desktop", "mobile")) {
    foreach ($Chapter in $RetiredChapters) {
        $Path = Join-Path $HoldRoot "$Chapter-$Profile.mp4"
        if (Test-Path -LiteralPath $Path) {
            $Path
        }
    }
}

if ($Rejected) {
    throw "Camera-derived chapter holds are retired. Remove: $($Rejected -join ', ')"
}

Write-Output "PASS: only explicitly approved fixed-camera holds may be published."
