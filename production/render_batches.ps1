param(
    [ValidateSet("desktop", "mobile")]
    [string]$Mode = "desktop",
    [ValidateRange(1, 256)]
    [int]$Samples = 64,
    [ValidateRange(12, 240)]
    [int]$BatchSize = 96,
    [ValidateRange(1, 1000000)]
    [int]$FrameStart = 1,
    [ValidateRange(0, 1000000)]
    [int]$FrameEnd = 0,
    [ValidateRange(0.001, 86400.0)]
    [double]$Duration = 38.0,
    [string]$Blender,
    [switch]$Fresh
)

$ErrorActionPreference = "Stop"

if (-not ("Codex.PowerRequest" -as [type])) {
    Add-Type -TypeDefinition @"
using System.Runtime.InteropServices;

namespace Codex {
    public static class PowerRequest {
        [DllImport("kernel32.dll", SetLastError = true)]
        public static extern uint SetThreadExecutionState(uint esFlags);
    }
}
"@
}

# Long background renders must not cross a Modern Standby transition. The
# NVIDIA driver can time out while Blender still owns an active render context.
$ExecutionState = [Codex.PowerRequest]::SetThreadExecutionState([uint32]2147483651)
if ($ExecutionState -eq 0) {
    throw "Failed to keep the system awake for the render session"
}

try {
$RepoRoot = Split-Path -Parent $PSScriptRoot
$RenderRoot = Join-Path $RepoRoot "production\renders"
$FrameDir = Join-Path $RenderRoot "$Mode-frames"
$ArchiveRoot = Join-Path $RenderRoot "archive"
$RenderScript = Join-Path $PSScriptRoot "render_final.ps1"
$FullFrameEnd = [int][Math]::Round($Duration * 24)
$ResolvedFrameEnd = if ($FrameEnd -eq 0) { $FullFrameEnd } else { $FrameEnd }

if ($FrameStart -gt $ResolvedFrameEnd -or $ResolvedFrameEnd -gt $FullFrameEnd) {
    throw "Frame range must be within 1-$FullFrameEnd, got $FrameStart-$ResolvedFrameEnd"
}

if ($Fresh -and (Test-Path -LiteralPath $FrameDir)) {
    $ResolvedRenderRoot = [System.IO.Path]::GetFullPath($RenderRoot)
    $ResolvedFrameDir = [System.IO.Path]::GetFullPath($FrameDir)
    if (-not $ResolvedFrameDir.StartsWith($ResolvedRenderRoot + [System.IO.Path]::DirectorySeparatorChar)) {
        throw "Refusing to archive frame directory outside $ResolvedRenderRoot"
    }
    New-Item -ItemType Directory -Force -Path $ArchiveRoot | Out-Null
    $Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $ArchivePath = Join-Path $ArchiveRoot "$Mode-frames-$Timestamp"
    Move-Item -LiteralPath $ResolvedFrameDir -Destination $ArchivePath
    Write-Host "Archived previous frames to $ArchivePath"
}

New-Item -ItemType Directory -Force -Path $FrameDir | Out-Null
$ProgressPath = Join-Path $FrameDir "batch-progress.json"

for ($BatchStart = $FrameStart; $BatchStart -le $ResolvedFrameEnd; $BatchStart += $BatchSize) {
    $BatchEnd = [Math]::Min($BatchStart + $BatchSize - 1, $ResolvedFrameEnd)
    Write-Host "Rendering $Mode frames $BatchStart-$BatchEnd of $ResolvedFrameEnd"
    $RenderArgs = @{
        Mode = $Mode
        Samples = $Samples
        Duration = $Duration
        FrameStart = $BatchStart
        FrameEnd = $BatchEnd
        Resume = $true
    }
    if ($Blender) {
        $RenderArgs.Blender = $Blender
    }
    & $RenderScript @RenderArgs

    $RenderedCount = @(Get-ChildItem -LiteralPath $FrameDir -Filter "frame-*.png" -File).Count
    $Progress = [ordered]@{
        mode = $Mode
        samples = $Samples
        frameStart = $FrameStart
        frameEnd = $ResolvedFrameEnd
        lastCompletedFrame = $BatchEnd
        renderedFrameCount = $RenderedCount
        updatedAt = (Get-Date).ToString("o")
    }
    $Progress | ConvertTo-Json | Set-Content -LiteralPath $ProgressPath -Encoding UTF8
}

Write-Host "Completed $Mode frame batches $FrameStart-$ResolvedFrameEnd"
}
finally {
    [void][Codex.PowerRequest]::SetThreadExecutionState([uint32]2147483648)
}
