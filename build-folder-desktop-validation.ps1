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
    Invoke-VenvPython @("-m", "pip", "install", "--upgrade", "pip==26.3")
    $buildRequirements = Join-Path $repo "store\build-requirements-win.txt"
    if (-not (Test-Path -LiteralPath $buildRequirements -PathType Leaf)) {
        throw "Pinned build requirements missing: $buildRequirements"
    }
    Invoke-VenvPython @("-m", "pip", "install", "-r", $buildRequirements)
    $pythonVersion = (& $python -c "import platform; print(platform.python_version())").Trim()
    Assert-Code
    $pyInstallerVersion = (& $python -c "import PyInstaller; print(PyInstaller.__version__)").Trim()
    Assert-Code
    if ($pythonVersion -cne "3.12.10" -or $pyInstallerVersion -cne "6.22.3") {
        throw "Unexpected packaging toolchain: Python=$pythonVersion PyInstaller=$pyInstallerVersion"
    }
    Invoke-VenvPython @("-m", "compileall", "-q", "folder_automation.py", "folder_desktop_app.py",
          "folder_desktop_flow.py", "tests")
    Invoke-VenvPython @("-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-v")
    Invoke-VenvPython @("-m", "PyInstaller", "--noconfirm", "--clean", "--onedir", "--windowed",
          "--name", "FolderAutomationEngine", "--distpath", $OutputBase,
          "--workpath", $work, "--specpath", $spec, "folder_desktop_app.py")
    $payloadDirectory = Join-Path $OutputBase "FolderAutomationEngine"
    $noticeDirectory = Join-Path $payloadDirectory "THIRD_PARTY_NOTICES"
    Invoke-VenvPython @(
        (Join-Path $repo "store\collect_runtime_notices.py"),
        $noticeDirectory,
        (Join-Path $repo "store\THIRD_PARTY_NOTICES.md")
    )
    $exe = Join-Path $payloadDirectory "FolderAutomationEngine.exe"
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
        python_version = $pythonVersion
        pyinstaller_version = $pyInstallerVersion
        build_requirements_sha256 = (Get-FileHash -LiteralPath $buildRequirements -Algorithm SHA256).Hash.ToLowerInvariant()
        third_party_notices_present = (Test-Path -LiteralPath $noticeDirectory -PathType Container)
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
