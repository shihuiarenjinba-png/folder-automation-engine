# Build the actual Folder Automation Engine GUI, not BackupRestoreVerifier.
# Technical validation only. No Store submission, signing or release.
param(
    [string]$OutputBase = "",
    [string]$BasePythonPath = ""
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$repo = $PSScriptRoot
$sourceCommit = (& git -C $repo rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $sourceCommit -notmatch '^[0-9a-fA-F]{40}$') {
    throw 'Unable to resolve exact source commit for validation build.'
}
$stamp = [guid]::NewGuid().ToString("N")
if (-not $OutputBase) {
    $OutputBase = Join-Path $repo ("dist-folder-validation\FolderAutomationEngine-" + $stamp)
}
if (Test-Path -LiteralPath $OutputBase) { throw "Output exists: $OutputBase" }
$venv = Join-Path $env:TEMP ("FolderDesktop-validation-" + $stamp)
$python = Join-Path $venv "Scripts\python.exe"
$work = Join-Path $venv "pyinstaller-work"
$spec = Join-Path $venv "pyinstaller-spec"
function Assert-Code {
    if ($LASTEXITCODE -ne 0) { throw "Command failed with exit code $LASTEXITCODE" }
}
function Invoke-VenvPython([string[]]$Arguments) {
    & $python @Arguments
    Assert-Code
}
try {
    if ($BasePythonPath) {
        if (-not (Test-Path -LiteralPath $BasePythonPath -PathType Leaf)) {
            throw "Base Python executable not found: $BasePythonPath"
        }
        & $BasePythonPath -m venv $venv
    } else {
        & py -3 -m venv $venv
    }
    Assert-Code
    Invoke-VenvPython @("-m", "pip", "install", "--upgrade", "pip")
    Invoke-VenvPython @("-m", "pip", "install", "pyinstaller>=6.10,<7")
    Invoke-VenvPython @("-m", "compileall", "-q", "folder_automation.py", "folder_desktop_app.py",
          "folder_desktop_flow.py", "tests")
    Invoke-VenvPython @("-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-v")
    Invoke-VenvPython @("-m", "PyInstaller", "--noconfirm", "--clean", "--onedir", "--windowed",
          "--name", "FolderAutomationEngine", "--distpath", $OutputBase,
          "--workpath", $work, "--specpath", $spec, "folder_desktop_app.py")
    $exe = Join-Path $OutputBase "FolderAutomationEngine\FolderAutomationEngine.exe"
    if (-not (Test-Path -LiteralPath $exe -PathType Leaf)) {
        throw "Wrong packaging entrypoint or EXE missing: $exe"
    }
    $proc = Start-Process -FilePath $exe -ArgumentList "--self-test" -PassThru -Wait
    if ($proc.ExitCode -ne 0) { throw "Packaged folder GUI self-test failed: $($proc.ExitCode)" }
    $hash = (Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLowerInvariant()
    $report = [ordered]@{
        expected_product = "Folder Automation Engine"
        packaged_entrypoint = "folder_desktop_app.py"
        source_commit = $sourceCommit
        exe_name = "FolderAutomationEngine.exe"
        exe_sha256 = $hash
        packaged_engine_selftest = "PASS"
        interactive_gui_acceptance = $false
        third_party_rights_approved = $false
        microsoft_store_submission = $false
        ready_for_sale = $false
        generated_utc = (Get-Date).ToUniversalTime().ToString("o")
    }
    $report | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (
        Join-Path $OutputBase "validation-manifest.json") -Encoding UTF8
    Write-Host "VALIDATION ONLY: $exe"
    Write-Host "SELFTEST PASS, SHA256 $hash"
    Write-Warning "EXE is unsigned; not certified, not approved for installation or sale."
} finally {
    if (Test-Path -LiteralPath $venv) {
        Remove-Item -LiteralPath $venv -Force -Recurse
    }
}
