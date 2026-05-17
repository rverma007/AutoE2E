# run_tests.ps1
# Runs the full test suite in two stages:
#   Stage 1 - letter type dependency chain (sequential, must preserve order)
#   Stage 2 - all other modules (parallel, 4 workers)
#
# Usage:
#   .\run_tests.ps1              # full run
#   .\run_tests.ps1 -Stage 1    # chain only
#   .\run_tests.ps1 -Stage 2    # others only
#   .\run_tests.ps1 -Workers 2  # change parallel worker count

param(
    [ValidateSet("1","2","all")]
    [string]$Stage = "all",
    [int]$Workers = 4
)

$chain = @(
    "tests/test_letter_type_ingestion.py",
    "tests/test_download_letter.py",
    "tests/test_generate_letter.py",
    "tests/test_letter_type_detail_verify.py"
)

$chainIgnore = $chain | ForEach-Object { "--ignore=$_" }

$stage1Failed = $false
$stage2Failed = $false

if ($Stage -eq "1" -or $Stage -eq "all") {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  STAGE 1 - Letter Type Chain (sequential)" -ForegroundColor Cyan
    Write-Host "  Order: ingestion -> download -> generate -> detail_verify" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""

    pytest @chain -p no:xdist -v
    if ($LASTEXITCODE -ne 0) {
        $stage1Failed = $true
        Write-Host ""
        Write-Host "Stage 1 had failures - Stage 2 will still run." -ForegroundColor Yellow
    }
}

if ($Stage -eq "2" -or $Stage -eq "all") {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  STAGE 2 - All Other Modules (parallel, $Workers workers)" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""

    pytest tests/ @chainIgnore -n $Workers --dist loadfile -v
    if ($LASTEXITCODE -ne 0) {
        $stage2Failed = $true
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SUMMARY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
if ($Stage -eq "1" -or $Stage -eq "all") {
    if ($stage1Failed) {
        Write-Host "  Stage 1 (chain)  : FAILED" -ForegroundColor Red
    } else {
        Write-Host "  Stage 1 (chain)  : PASSED" -ForegroundColor Green
    }
}
if ($Stage -eq "2" -or $Stage -eq "all") {
    if ($stage2Failed) {
        Write-Host "  Stage 2 (others) : FAILED" -ForegroundColor Red
    } else {
        Write-Host "  Stage 2 (others) : PASSED" -ForegroundColor Green
    }
}
Write-Host ""
Write-Host "  HTML report  : reports/sanity_report.html"
Write-Host "  Allure       : allure serve reports/allure-results"
Write-Host ""

if ($stage1Failed -or $stage2Failed) { exit 1 } else { exit 0 }
