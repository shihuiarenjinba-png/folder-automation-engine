<#
Capture a real application-window screenshot on a disposable GitHub-hosted
Windows runner. This is automated CI evidence only: it is not human GUI QA,
Store artwork, signing evidence, or release approval.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$ExecutablePath,
    [Parameter(Mandatory=$true)][string]$EvidenceDirectory,
    [switch]$EphemeralRunner
)
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

if (-not $EphemeralRunner -or $env:GITHUB_ACTIONS -ne "true" -or
    $env:RUNNER_ENVIRONMENT -ne "github-hosted" -or $env:OS -ne "Windows_NT") {
    throw "GUI screenshot smoke is restricted to disposable GitHub-hosted Windows"
}

$exe = (Resolve-Path -LiteralPath $ExecutablePath -ErrorAction Stop).Path
if ([IO.Path]::GetFileName($exe) -cne "FolderAutomationEngine.exe") {
    throw "Unexpected executable name"
}
if (Test-Path -LiteralPath $EvidenceDirectory) {
    throw "Evidence directory already exists; refusing overwrite"
}
[void](New-Item -ItemType Directory -Path $EvidenceDirectory -ErrorAction Stop)
$evidence = (Resolve-Path -LiteralPath $EvidenceDirectory).Path
$screenshot = Join-Path $evidence "folder-automation-engine-ci-window.png"
$reportPath = Join-Path $evidence "gui-smoke-report.json"
$sourceCommit = (& git -C (Join-Path $PSScriptRoot "..") rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $sourceCommit -notmatch '^[0-9a-fA-F]{40}$') {
    throw "Unable to resolve exact source commit"
}
$exeHash = (Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLowerInvariant()

Add-Type -AssemblyName System.Drawing
Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class FolderQaWindowCapture {
    [StructLayout(LayoutKind.Sequential)]
    public struct RECT { public int Left; public int Top; public int Right; public int Bottom; }
    [DllImport("user32.dll")]
    public static extern bool GetWindowRect(IntPtr hWnd, out RECT rect);
    [DllImport("user32.dll")]
    public static extern bool SetForegroundWindow(IntPtr hWnd);
}
'@

$process = $null
$failure = ""
$title = ""
$width = 0
$height = 0
$responding = $false
$closedNormally = $false
try {
    $process = Start-Process -FilePath $exe -PassThru -ErrorAction Stop
    $deadline = [DateTime]::UtcNow.AddSeconds(20)
    do {
        Start-Sleep -Milliseconds 250
        $process.Refresh()
    } while (-not $process.HasExited -and $process.MainWindowHandle -eq [IntPtr]::Zero -and
             [DateTime]::UtcNow -lt $deadline)
    if ($process.HasExited) { throw "GUI process exited before its window was available" }
    if ($process.MainWindowHandle -eq [IntPtr]::Zero) { throw "GUI window handle was not available within 20 seconds" }
    $title = [string]$process.MainWindowTitle
    if ($title -cne "Folder Automation Engine") { throw "Unexpected window title: $title" }
    $responding = [bool]$process.Responding
    if (-not $responding) { throw "GUI process is not responding" }

    $rect = New-Object FolderQaWindowCapture+RECT
    if (-not [FolderQaWindowCapture]::GetWindowRect($process.MainWindowHandle, [ref]$rect)) {
        throw "GetWindowRect failed"
    }
    $width = $rect.Right - $rect.Left
    $height = $rect.Bottom - $rect.Top
    if ($width -lt 720 -or $height -lt 570) { throw "Captured window is below the product minimum size" }
    [void][FolderQaWindowCapture]::SetForegroundWindow($process.MainWindowHandle)
    Start-Sleep -Milliseconds 500
    $bitmap = New-Object System.Drawing.Bitmap($width, $height)
    try {
        $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
        try {
            $graphics.CopyFromScreen($rect.Left, $rect.Top, 0, 0, $bitmap.Size)
        } finally {
            $graphics.Dispose()
        }
        $bitmap.Save($screenshot, [System.Drawing.Imaging.ImageFormat]::Png)
    } finally {
        $bitmap.Dispose()
    }
    if (-not (Test-Path -LiteralPath $screenshot -PathType Leaf) -or
        (Get-Item -LiteralPath $screenshot).Length -lt 1000) {
        throw "Window screenshot was not written correctly"
    }

    if (-not $process.CloseMainWindow()) { throw "GUI did not accept a normal window-close request" }
    $closedNormally = $process.WaitForExit(10000)
    if (-not $closedNormally) { throw "GUI did not close normally within 10 seconds" }
} catch {
    $failure = $_.Exception.Message
} finally {
    if ($process -and -not $process.HasExited) {
        # Exact-process cleanup on a disposable CI runner only; never evidence of a pass.
        Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
        [void]$process.WaitForExit(5000)
    }
    $screenshotHash = $null
    if (Test-Path -LiteralPath $screenshot -PathType Leaf) {
        $screenshotHash = (Get-FileHash -LiteralPath $screenshot -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    $report = [ordered]@{
        schema = "folder_desktop_ci_gui_smoke_v1"
        status = if (-not $failure -and $closedNormally) { "PASS" } else { "FAIL" }
        source_commit = $sourceCommit
        executable = [IO.Path]::GetFileName($exe)
        executable_sha256 = $exeHash
        window_title = $title
        window_width = $width
        window_height = $height
        process_responding = $responding
        normal_window_close = $closedNormally
        screenshot_file = if ($screenshotHash) { [IO.Path]::GetFileName($screenshot) } else { $null }
        screenshot_sha256 = $screenshotHash
        automated_runner_only = $true
        human_interactive_qa = $false
        store_listing_eligible = $false
        release_approved = $false
        error = $failure
        generated_utc = (Get-Date).ToUniversalTime().ToString("o")
    }
    $report | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $reportPath -Encoding UTF8
}
if ($failure) { throw "Folder desktop CI GUI smoke failed: $failure" }
Write-Host ("FOLDER_CI_GUI_WINDOW_PASS sha256={0} screenshot={1} store_eligible=false" -f $exeHash,$screenshot)
