# Optional local WACK pre-submission helper.
# This script NEVER changes Windows security/trust settings and is not run by CI.
param(
    [Parameter(Mandatory=$true)][string]$PackagePath,
    [Parameter(Mandatory=$true)][string]$OutputDirectory,
    [switch]$ApproveWackPackageTest
)
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

if (-not $ApproveWackPackageTest) {
    throw "WACK can deploy/open the package during testing. Re-run only after explicit action-time approval with -ApproveWackPackageTest."
}
$package = (Resolve-Path -LiteralPath $PackagePath -ErrorAction Stop).Path
if ([IO.Path]::GetExtension($package) -notin @(".msix", ".appx")) {
    throw "WACK preflight expects an MSIX/AppX package."
}
if (Test-Path -LiteralPath $OutputDirectory) {
    throw "Output directory already exists: $OutputDirectory"
}
New-Item -ItemType Directory -Path $OutputDirectory | Out-Null
$output = (Resolve-Path -LiteralPath $OutputDirectory).Path

$kit = Join-Path ${env:ProgramFiles(x86)} "Windows Kits\10\App Certification Kit\appcert.exe"
if (-not (Test-Path -LiteralPath $kit -PathType Leaf)) {
    throw "Windows App Certification Kit not found at the standard SDK location: $kit"
}
$packageSha = (Get-FileHash -LiteralPath $package -Algorithm SHA256).Hash.ToLowerInvariant()
$report = Join-Path $output "wack-report.xml"

& $kit reset
if ($LASTEXITCODE -ne 0) { throw "appcert reset failed: $LASTEXITCODE" }
& $kit test -appxpackagepath $package -reportoutputpath $report
$exitCode = $LASTEXITCODE

$result = [ordered]@{
    package = $package
    package_sha256 = $packageSha
    appcert = $kit
    appcert_exit_code = $exitCode
    report = $report
    passed = ($exitCode -eq 0)
    generated_utc = (Get-Date).ToUniversalTime().ToString("o")
    security_settings_changed = $false
    trust_store_changed = $false
    store_submission_performed = $false
}
$result | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $output "wack-preflight.json") -Encoding UTF8
if ($exitCode -ne 0) {
    throw "WACK preflight failed with exit code $exitCode. Preserve the report; do not bypass failures."
}
Write-Host "WACK PREFLIGHT PASS for SHA256 $packageSha"
