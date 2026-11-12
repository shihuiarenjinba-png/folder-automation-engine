<#
Capture real JP/EN app-window images large enough for a Private-audience Store
listing candidate. This runs only on disposable GitHub-hosted Windows.
It is not human QA and it is not public-release approval.
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
    throw "Store screenshot capture is restricted to disposable GitHub-hosted Windows"
}
$exe=(Resolve-Path -LiteralPath $ExecutablePath -ErrorAction Stop).Path
if ([IO.Path]::GetFileName($exe) -cne "FolderAutomationEngine.exe") { throw "Unexpected executable" }
if (Test-Path -LiteralPath $EvidenceDirectory) { throw "Evidence directory already exists" }
New-Item -ItemType Directory -Path $EvidenceDirectory | Out-Null
$evidence=(Resolve-Path -LiteralPath $EvidenceDirectory).Path
$sourceCommit=(& git -C (Join-Path $PSScriptRoot "..") rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $sourceCommit -notmatch '^[0-9a-fA-F]{40}$') { throw "Unable to resolve source commit" }
$exeHash=(Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLowerInvariant()

Add-Type -AssemblyName System.Drawing
Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class FolderStoreCapture {
    [StructLayout(LayoutKind.Sequential)]
    public struct RECT { public int Left; public int Top; public int Right; public int Bottom; }
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT rect);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll", SetLastError=true)]
    public static extern bool SetWindowPos(IntPtr hWnd, IntPtr insertAfter, int X, int Y, int cx, int cy, uint flags);
}
'@

$oldLocal=$env:LOCALAPPDATA
$tempLocal=Join-Path $env:RUNNER_TEMP ("FolderStoreCapture-"+[guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path (Join-Path $tempLocal "FolderAutomationEngine") -Force | Out-Null
$env:LOCALAPPDATA=$tempLocal
$results=@()
try {
    foreach ($case in @(
        [ordered]@{ code="ja"; locale="日本語" },
        [ordered]@{ code="en"; locale="English" }
    )) {
        $pref=Join-Path $tempLocal "FolderAutomationEngine\preferences.json"
        $payload=[ordered]@{ schema_version=1; values=[ordered]@{ locale=$case.locale } } | ConvertTo-Json -Compress
        [IO.File]::WriteAllText($pref,$payload,[Text.UTF8Encoding]::new($false))
        $process=$null
        try {
            $process=Start-Process -FilePath $exe -PassThru -ErrorAction Stop
            $deadline=[DateTime]::UtcNow.AddSeconds(20)
            do {
                Start-Sleep -Milliseconds 250
                $process.Refresh()
            } while (-not $process.HasExited -and $process.MainWindowHandle -eq [IntPtr]::Zero -and [DateTime]::UtcNow -lt $deadline)
            if ($process.HasExited -or $process.MainWindowHandle -eq [IntPtr]::Zero) { throw "GUI window unavailable for $($case.code)" }
            if (-not $process.Responding) { throw "GUI not responding for $($case.code)" }
            if (-not [FolderStoreCapture]::SetWindowPos($process.MainWindowHandle,[IntPtr]::Zero,20,20,1366,768,0x0040)) {
                throw "SetWindowPos failed for $($case.code)"
            }
            Start-Sleep -Milliseconds 700
            $process.Refresh()
            [void][FolderStoreCapture]::SetForegroundWindow($process.MainWindowHandle)
            Start-Sleep -Milliseconds 300
            $rect=New-Object FolderStoreCapture+RECT
            if (-not [FolderStoreCapture]::GetWindowRect($process.MainWindowHandle,[ref]$rect)) { throw "GetWindowRect failed" }
            $width=$rect.Right-$rect.Left; $height=$rect.Bottom-$rect.Top
            if ($width -lt 1366 -or $height -lt 768) { throw "Store capture below 1366x768: ${width}x${height}" }
            $file=Join-Path $evidence ("folder-automation-engine-store-"+$case.code+".png")
            $bitmap=New-Object Drawing.Bitmap($width,$height)
            try {
                $graphics=[Drawing.Graphics]::FromImage($bitmap)
                try { $graphics.CopyFromScreen($rect.Left,$rect.Top,0,0,$bitmap.Size) }
                finally { $graphics.Dispose() }
                $bitmap.Save($file,[Drawing.Imaging.ImageFormat]::Png)
            } finally { $bitmap.Dispose() }
            $hash=(Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant()
            $results += [ordered]@{
                language=$case.locale
                file=[IO.Path]::GetFileName($file)
                sha256=$hash
                width=$width
                height=$height
                actual_application_window=$true
                private_audience_listing_candidate=$true
                human_approved=$false
                public_release_approved=$false
            }
            if (-not $process.CloseMainWindow() -or -not $process.WaitForExit(10000)) { throw "Normal close failed for $($case.code)" }
        } finally {
            if ($process -and -not $process.HasExited) {
                Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
                [void]$process.WaitForExit(5000)
            }
        }
    }
} finally {
    $env:LOCALAPPDATA=$oldLocal
    Remove-Item -LiteralPath $tempLocal -Recurse -Force -ErrorAction SilentlyContinue
}
[ordered]@{
    schema="folder_store_listing_capture_v1"
    source_commit=$sourceCommit
    executable_sha256=$exeHash
    automated_ci_capture=$true
    private_audience_use_requires_owner_visual_approval=$true
    public_release_requires_store_signed_install_capture=$true
    captures=$results
} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $evidence "store-capture-report.json") -Encoding UTF8
Write-Host "FOLDER_STORE_CAPTURE_PASS languages=ja,en min=1366x768"
