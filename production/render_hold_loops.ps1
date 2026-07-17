param(
    [ValidateSet("desktop", "mobile")]
    [string]$Mode = "desktop",
    [ValidateSet("process", "takt")]
    [string[]]$Chapters = @("process", "takt"),
    [ValidateRange(1, 128)]
    [int]$Samples = 24,
    [string]$Blender,
    [string]$Ffmpeg,
    [switch]$Resume
)

$ErrorActionPreference = "Stop"

if (-not ("Codex.HoldLoopPowerRequest" -as [type])) {
    Add-Type -TypeDefinition @"
using System.Runtime.InteropServices;

namespace Codex {
    public static class HoldLoopPowerRequest {
        [DllImport("kernel32.dll", SetLastError = true)]
        public static extern uint SetThreadExecutionState(uint esFlags);
    }
}
"@
}

$ExecutionState = [Codex.HoldLoopPowerRequest]::SetThreadExecutionState([uint32]2147483651)
if ($ExecutionState -eq 0) {
    throw "Failed to keep the system awake for the hold-loop render"
}

try {
    $RepoRoot = Split-Path -Parent $PSScriptRoot
    $ShowcaseRoot = Split-Path -Parent $RepoRoot
    $Blender = if ($Blender) {
        $Blender
    } else {
        Join-Path $ShowcaseRoot "tools\blender-4.5.11-windows-x64\blender.exe"
    }
    $Ffmpeg = if ($Ffmpeg) {
        $Ffmpeg
    } else {
        Join-Path $ShowcaseRoot "tools\ffmpeg-release-essentials\ffmpeg-8.1.2-essentials_build\bin\ffmpeg.exe"
    }
    $Scene = Join-Path $RepoRoot "production\scenes\felix-journey-$Mode.blend"
    $Script = Join-Path $RepoRoot "production\blender\render_hold_loop.py"
    $RenderRoot = Join-Path $RepoRoot "production\renders\hold-loops\$Mode"
    $MediaRoot = Join-Path $RepoRoot "public\media\holds"
    $Scale = if ($Mode -eq "desktop") { "1600:900" } else { "720:1280" }
    $Crf = if ($Mode -eq "desktop") { 20 } else { 21 }

    $Specs = @{
        process = @{ Start = 301; Frames = 36 }
        takt = @{ Start = 553; Frames = 48 }
    }

    foreach ($Chapter in $Chapters) {
        $Spec = $Specs[$Chapter]
        $Output = Join-Path $RenderRoot $Chapter
        New-Item -ItemType Directory -Force -Path $Output, $MediaRoot | Out-Null

        $Arguments = @(
            "--background",
            "--factory-startup",
            $Scene,
            "--python-exit-code", "1",
            "--python", $Script,
            "--",
            "--mode", $Mode,
            "--chapter", $Chapter,
            "--start-frame", $Spec.Start,
            "--frame-count", $Spec.Frames,
            "--samples", $Samples,
            "--output", $Output
        )
        if ($Resume) {
            $Arguments += "--resume"
        }

        & $Blender @Arguments
        if ($LASTEXITCODE -ne 0) {
            throw "$Mode $Chapter Blender render failed with exit code $LASTEXITCODE"
        }

        $DurationSeconds = $Spec.Frames / 24
        $BlendSeconds = [Math]::Min(0.25, $DurationSeconds / 3)
        $BlendOffset = $DurationSeconds - $BlendSeconds
        $Filter = "[0:v]split=2[base][firstSource];[firstSource]trim=end_frame=1,setpts=PTS-STARTPTS,tpad=stop_mode=clone`:stop_duration=$DurationSeconds[first];[base][first]xfade=transition=fade`:duration=$BlendSeconds`:offset=$BlendOffset,trim=end_frame=$($Spec.Frames),setpts=PTS-STARTPTS,fps=24,scale=$Scale`:flags=lanczos,format=yuv420p[loop]"
        $MediaOutput = Join-Path $MediaRoot "$Chapter-$Mode.mp4"

        & $Ffmpeg `
            -y `
            -hide_banner `
            -loglevel warning `
            -framerate 24 `
            -start_number 1 `
            -i (Join-Path $Output "frame-%04d.png") `
            -filter_complex $Filter `
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
            $MediaOutput

        if ($LASTEXITCODE -ne 0) {
            throw "$Mode $Chapter loop encoding failed with exit code $LASTEXITCODE"
        }
    }

    Get-Item ($Chapters | ForEach-Object { Join-Path $MediaRoot "$_-$Mode.mp4" }) |
        Select-Object FullName, Length
}
finally {
    [void][Codex.HoldLoopPowerRequest]::SetThreadExecutionState([uint32]2147483648)
}
