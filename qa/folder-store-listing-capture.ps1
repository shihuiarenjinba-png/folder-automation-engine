<#
Capture five truthful JP/EN Store-listing views from the exact packaged EXE.
All operations are restricted to a fixed fixture on disposable GitHub Windows.
This is not human approval and it is not public-release approval.
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
    public const int ENUM_CURRENT_SETTINGS = -1;
    public const int CDS_TEST = 0x00000002;
    public const int DISP_CHANGE_SUCCESSFUL = 0;

    [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)]
    public struct DEVMODE {
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst=32)] public string dmDeviceName;
        public short dmSpecVersion;
        public short dmDriverVersion;
        public short dmSize;
        public short dmDriverExtra;
        public int dmFields;
        public int dmPositionX;
        public int dmPositionY;
        public int dmDisplayOrientation;
        public int dmDisplayFixedOutput;
        public short dmColor;
        public short dmDuplex;
        public short dmYResolution;
        public short dmTTOption;
        public short dmCollate;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst=32)] public string dmFormName;
        public short dmLogPixels;
        public int dmBitsPerPel;
        public int dmPelsWidth;
        public int dmPelsHeight;
        public int dmDisplayFlags;
        public int dmDisplayFrequency;
        public int dmICMMethod;
        public int dmICMIntent;
        public int dmMediaType;
        public int dmDitherType;
        public int dmReserved1;
        public int dmReserved2;
        public int dmPanningWidth;
        public int dmPanningHeight;
    }

    private static DEVMODE CreateDevMode() {
        DEVMODE mode = new DEVMODE();
        mode.dmSize = (short)Marshal.SizeOf(typeof(DEVMODE));
        return mode;
    }

    public static DEVMODE GetCurrentDisplayMode() {
        DEVMODE mode = CreateDevMode();
        if (!EnumDisplaySettings(null, ENUM_CURRENT_SETTINGS, ref mode)) {
            throw new InvalidOperationException("EnumDisplaySettings(current) failed: " + Marshal.GetLastWin32Error());
        }
        return mode;
    }

    public static DEVMODE FindSmallestDisplayMode(int minimumWidth, int minimumHeight) {
        bool found = false;
        long bestArea = long.MaxValue;
        DEVMODE best = CreateDevMode();
        for (int index = 0; ; index++) {
            DEVMODE mode = CreateDevMode();
            if (!EnumDisplaySettings(null, index, ref mode)) break;
            if (mode.dmPelsWidth < minimumWidth || mode.dmPelsHeight < minimumHeight || mode.dmBitsPerPel < 24) continue;
            long area = (long)mode.dmPelsWidth * mode.dmPelsHeight;
            if (!found || area < bestArea || (area == bestArea && mode.dmPelsWidth < best.dmPelsWidth)) {
                found = true;
                bestArea = area;
                best = mode;
            }
        }
        if (!found) throw new InvalidOperationException("No native Windows display mode satisfies the Store minimum");
        return best;
    }

    public static int TestDisplayMode(DEVMODE mode) {
        return ChangeDisplaySettings(ref mode, CDS_TEST);
    }

    public static int ApplyDisplayMode(DEVMODE mode) {
        return ChangeDisplaySettings(ref mode, 0);
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct RECT { public int Left; public int Top; public int Right; public int Bottom; }
    [DllImport("user32.dll", CharSet=CharSet.Unicode)]
    public static extern bool EnumDisplaySettings(string deviceName, int modeNum, ref DEVMODE devMode);
    [DllImport("user32.dll", CharSet=CharSet.Unicode)]
    public static extern int ChangeDisplaySettings(ref DEVMODE devMode, int flags);
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT rect);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll", SetLastError=true)]
    public static extern bool SetWindowPos(IntPtr hWnd, IntPtr insertAfter, int X, int Y, int cx, int cy, uint flags);
    [DllImport("user32.dll", SetLastError=true)]
    public static extern bool PrintWindow(IntPtr hWnd, IntPtr hdcBlt, uint nFlags);
}
'@

function Get-CurrentDisplayMode {
    return [FolderStoreCapture]::GetCurrentDisplayMode()
}

function Enable-NativeStoreDisplayMode {
    $target=[FolderStoreCapture]::FindSmallestDisplayMode(1366,768)
    $test=[FolderStoreCapture]::TestDisplayMode($target)
    if ($test -ne [FolderStoreCapture]::DISP_CHANGE_SUCCESSFUL) {
        throw "Windows rejected the native Store display mode during validation: $test"
    }
    $apply=[FolderStoreCapture]::ApplyDisplayMode($target)
    if ($apply -ne [FolderStoreCapture]::DISP_CHANGE_SUCCESSFUL) {
        throw "Windows rejected the native Store display mode: $apply"
    }
    Start-Sleep -Milliseconds 800
    $active=Get-CurrentDisplayMode
    if ($active.dmPelsWidth -lt 1366 -or $active.dmPelsHeight -lt 768) {
        throw "Native Store display mode did not remain active: $($active.dmPelsWidth)x$($active.dmPelsHeight)"
    }
    return $active
}

$fixtureRoot=Join-Path ([IO.Path]::GetPathRoot($exe)) "TeamArchive"
$fixtureRoot=[IO.Path]::GetFullPath($fixtureRoot)
$fixtureParent=[IO.Path]::GetDirectoryName($fixtureRoot)
$driveRoot=[IO.Path]::GetPathRoot($fixtureRoot)
if (-not [IO.Path]::IsPathRooted($fixtureRoot) -or
    [IO.Path]::GetFileName($fixtureRoot) -cne "TeamArchive" -or $fixtureParent -cne $driveRoot) {
    throw "Unsafe Store fixture path"
}

function Reset-StoreFixture {
    if (Test-Path -LiteralPath $fixtureRoot) {
        $resolved=(Resolve-Path -LiteralPath $fixtureRoot).Path
        if ($resolved -cne $fixtureRoot) { throw "Store fixture resolved outside its fixed path" }
        Remove-Item -LiteralPath $resolved -Recurse -Force
    }
    foreach ($folder in @("Incoming", "Documents", "Spreadsheets", "Images")) {
        New-Item -ItemType Directory -Path (Join-Path $fixtureRoot $folder) -Force | Out-Null
    }
    [IO.File]::WriteAllText((Join-Path $fixtureRoot "Incoming\Quarterly-report.pdf"), "sample report")
    [IO.File]::WriteAllText((Join-Path $fixtureRoot "Incoming\Project-notes.pdf"), "sample notes")
    [IO.File]::WriteAllText((Join-Path $fixtureRoot "Incoming\Budget.csv"), "Item,Amount`nSoftware,120")
    [IO.File]::WriteAllText((Join-Path $fixtureRoot "Incoming\Cover-image.png"), "sample image")
}

function Save-AppWindow([IntPtr]$Handle, [string]$File) {
    $rect=New-Object FolderStoreCapture+RECT
    if (-not [FolderStoreCapture]::GetWindowRect($Handle,[ref]$rect)) { throw "GetWindowRect failed" }
    $width=$rect.Right-$rect.Left
    $height=$rect.Bottom-$rect.Top
    if ($width -lt 1366 -or $height -lt 768) {
        throw "Native app window is below Store minimum; upscaling is prohibited: ${width}x${height}"
    }
    $sourceBitmap=New-Object Drawing.Bitmap($width,$height)
    $printWindowOk=$false
    $outputWidth=$width
    $outputHeight=$height
    $resized=$false
    try {
        $sourceGraphics=[Drawing.Graphics]::FromImage($sourceBitmap)
        $hdc=[IntPtr]::Zero
        try {
            $hdc=$sourceGraphics.GetHdc()
            $printWindowOk=[FolderStoreCapture]::PrintWindow($Handle,$hdc,2)
        } finally {
            if ($hdc -ne [IntPtr]::Zero) { $sourceGraphics.ReleaseHdc($hdc) }
            $sourceGraphics.Dispose()
        }
        if (-not $printWindowOk) { throw "PrintWindow failed" }
        $scale=[Math]::Max(1.0,[Math]::Max(1366.0/$width,768.0/$height))
        $outputWidth=[int][Math]::Ceiling($width*$scale)
        $outputHeight=[int][Math]::Ceiling($height*$scale)
        $resized=($outputWidth -ne $width -or $outputHeight -ne $height)
        if ($resized) {
            $outputBitmap=New-Object Drawing.Bitmap($outputWidth,$outputHeight)
            try {
                $outputGraphics=[Drawing.Graphics]::FromImage($outputBitmap)
                try {
                    $outputGraphics.InterpolationMode=[Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
                    $outputGraphics.PixelOffsetMode=[Drawing.Drawing2D.PixelOffsetMode]::HighQuality
                    $outputGraphics.DrawImage($sourceBitmap,0,0,$outputWidth,$outputHeight)
                } finally { $outputGraphics.Dispose() }
                $outputBitmap.Save($File,[Drawing.Imaging.ImageFormat]::Png)
            } finally { $outputBitmap.Dispose() }
        } else {
            $sourceBitmap.Save($File,[Drawing.Imaging.ImageFormat]::Png)
        }
    } finally { $sourceBitmap.Dispose() }
    if ($outputWidth -lt 1366 -or $outputHeight -lt 768) { throw "Store candidate output below 1366x768" }
    return [ordered]@{
        source_width=$width
        source_height=$height
        output_width=$outputWidth
        output_height=$outputHeight
        resized_for_store_minimum=$resized
        resize_method=if ($resized) { "HighQualityBicubic" } else { "none" }
        capture_method="PrintWindow(PW_RENDERFULLCONTENT)"
        print_window_success=$printWindowOk
    }
}

$oldLocal=$env:LOCALAPPDATA
$oldCapture=$env:FOLDER_STORE_CAPTURE
$originalDisplayMode=Get-CurrentDisplayMode
$captureDisplayMode=$null
$tempLocal=Join-Path $env:RUNNER_TEMP ("FolderStoreCapture-"+[guid]::NewGuid().ToString("N"))
$results=@()
$states=@("setup", "multi-rule", "preview", "result", "automatic-ready")
$japaneseLocale=(-join @([char]0x65E5,[char]0x672C,[char]0x8A9E))
try {
    $captureDisplayMode=Enable-NativeStoreDisplayMode
    New-Item -ItemType Directory -Path (Join-Path $tempLocal "FolderAutomationEngine") -Force | Out-Null
    $env:LOCALAPPDATA=$tempLocal
    $env:FOLDER_STORE_CAPTURE="EXACT_PACKAGED_UI_V1"
    foreach ($case in @(
        [ordered]@{ code="ja"; locale=$japaneseLocale },
        [ordered]@{ code="en"; locale="English" }
    )) {
        $pref=Join-Path $tempLocal "FolderAutomationEngine\preferences.json"
        $payload=[ordered]@{ schema_version=1; values=[ordered]@{ locale=$case.locale } } | ConvertTo-Json -Compress
        [IO.File]::WriteAllText($pref,$payload,[Text.UTF8Encoding]::new($false))
        for ($stateIndex=0; $stateIndex -lt $states.Count; $stateIndex++) {
            $state=$states[$stateIndex]
            Reset-StoreFixture
            $ready=Join-Path $fixtureRoot (".capture-ready-"+$state)
            $process=$null
            try {
                $arguments=@("--store-capture-state",$state,"--store-capture-root",$fixtureRoot,
                             "--store-capture-ready",$ready)
                $process=Start-Process -FilePath $exe -ArgumentList $arguments `
                    -WorkingDirectory ([IO.Path]::GetPathRoot($exe)) -PassThru -ErrorAction Stop
                $deadline=[DateTime]::UtcNow.AddSeconds(30)
                do {
                    Start-Sleep -Milliseconds 200
                    $process.Refresh()
                } while (-not $process.HasExited -and
                         ($process.MainWindowHandle -eq [IntPtr]::Zero -or -not (Test-Path -LiteralPath $ready)) -and
                         [DateTime]::UtcNow -lt $deadline)
                if ($process.HasExited -or $process.MainWindowHandle -eq [IntPtr]::Zero) {
                    throw "GUI window unavailable for $($case.code)/$state"
                }
                if (-not (Test-Path -LiteralPath $ready)) { throw "UI state did not become ready for $($case.code)/$state" }
                if (-not $process.Responding) { throw "GUI not responding for $($case.code)/$state" }
                if (-not [FolderStoreCapture]::SetWindowPos($process.MainWindowHandle,[IntPtr]::Zero,0,0,1366,768,0x0040)) {
                    throw "SetWindowPos failed for $($case.code)/$state"
                }
                Start-Sleep -Milliseconds 700
                $process.Refresh()
                [void][FolderStoreCapture]::SetForegroundWindow($process.MainWindowHandle)
                Start-Sleep -Milliseconds 300
                $ordinal="{0:D2}" -f ($stateIndex+1)
                $file=Join-Path $evidence ("folder-automation-engine-store-"+$case.code+"-"+$ordinal+"-"+$state+".png")
                $dimensions=Save-AppWindow -Handle $process.MainWindowHandle -File $file
                $hash=(Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant()
                $results += [ordered]@{
                    language=$case.locale
                    state=$state
                    file=[IO.Path]::GetFileName($file)
                    sha256=$hash
                    source_width=$dimensions.source_width
                    source_height=$dimensions.source_height
                    output_width=$dimensions.output_width
                    output_height=$dimensions.output_height
                    resized_for_store_minimum=$dimensions.resized_for_store_minimum
                    resize_method=$dimensions.resize_method
                    capture_method=$dimensions.capture_method
                    print_window_success=$dimensions.print_window_success
                    desktop_or_taskbar_capture_expected=$false
                    actual_application_window=$true
                    exact_packaged_executable=$true
                    disposable_real_filesystem_fixture=$true
                    private_audience_listing_candidate=$true
                    human_approved=$false
                    public_release_approved=$false
                }
                if (-not $process.CloseMainWindow() -or -not $process.WaitForExit(10000)) {
                    throw "Normal close failed for $($case.code)/$state"
                }
            } finally {
                if ($process -and -not $process.HasExited) {
                    Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
                    [void]$process.WaitForExit(5000)
                }
            }
        }
    }
    if ($results.Count -ne 10) { throw "Expected exactly ten Store captures" }
    foreach ($locale in @($japaneseLocale, "English")) {
        if (@($results | Where-Object { $_.language -ceq $locale }).Count -ne 5) {
            throw "Expected five captures for $locale"
        }
    }
} finally {
    $env:LOCALAPPDATA=$oldLocal
    $env:FOLDER_STORE_CAPTURE=$oldCapture
    if ($null -ne $originalDisplayMode) {
        $restore=[FolderStoreCapture]::ApplyDisplayMode($originalDisplayMode)
        if ($restore -ne [FolderStoreCapture]::DISP_CHANGE_SUCCESSFUL) {
            Write-Warning "Unable to restore original disposable-runner display mode: $restore"
        }
    }
    if (Test-Path -LiteralPath $fixtureRoot) {
        $resolved=(Resolve-Path -LiteralPath $fixtureRoot).Path
        if ($resolved -ceq $fixtureRoot) { Remove-Item -LiteralPath $resolved -Recurse -Force }
    }
    Remove-Item -LiteralPath $tempLocal -Recurse -Force -ErrorAction SilentlyContinue
}
[ordered]@{
    schema="folder_store_listing_capture_v2"
    source_commit=$sourceCommit
    executable_sha256=$exeHash
    automated_ci_capture=$true
    exact_packaged_executable=$true
    disposable_real_filesystem_fixture=$true
    required_states=$states
    capture_count=$results.Count
    captures_per_language=5
    capture_display_width=$captureDisplayMode.dmPelsWidth
    capture_display_height=$captureDisplayMode.dmPelsHeight
    private_audience_use_requires_owner_visual_approval=$true
    public_release_requires_store_signed_install_capture=$true
    captures=$results
} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $evidence "store-capture-report.json") -Encoding UTF8
Write-Host "FOLDER_STORE_CAPTURE_PASS languages=ja,en captures=10 states=5 min=1366x768"

