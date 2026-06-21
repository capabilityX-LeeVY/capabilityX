################################################################################
# Build Core Controls Dataset - Automated Workflow (PowerShell)
################################################################################
# This script automates the core controls dataset building process.
# Usage:
#   .\build_core_controls.ps1 [-Mode auto|manual]
#
# Modes:
#   auto   - Run all steps automatically (assumes config is already set)
#   manual - Run steps 1-2, pause for manual editing, then run step 4
################################################################################

param(
    [ValidateSet("auto", "manual")]
    [string]$Mode = "manual"
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host " Build Core Controls Dataset Workflow" -ForegroundColor Cyan
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host " Mode: $Mode" -ForegroundColor Yellow
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Build filtered dataset
Write-Host "[Step 1/4] Building filtered dataset (1182 -> 211 controls)..." -ForegroundColor Green
Write-Host "Command: python build_core_controls_dataset.py --max-depth 9 --only-main-controls"
Write-Host ""
python build_core_controls_dataset.py --max-depth 9 --only-main-controls
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to build filtered dataset" -ForegroundColor Red
    exit 1
}
Write-Host ""
Write-Host "[SUCCESS] Filtered dataset created: data/go_to_core_controls_raw.json" -ForegroundColor Green
Write-Host ""

# Step 2: Generate configuration files
Write-Host "[Step 2/4] Generating configuration files..." -ForegroundColor Green
Write-Host "Command: python generate_core_controls_config.py"
Write-Host ""
python generate_core_controls_config.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to generate configuration" -ForegroundColor Red
    exit 1
}
Write-Host ""
Write-Host "[SUCCESS] Configuration files created:" -ForegroundColor Green
Write-Host "  - core_controls_config.json"
Write-Host "  - core_controls_selection.txt"
Write-Host ""

# Step 3: Manual editing or auto mode
if ($Mode -eq "auto") {
    Write-Host "[Step 3/4] Auto mode - Skipping manual editing..." -ForegroundColor Yellow
    Write-Host "Using existing selections in core_controls_config.json"
    Write-Host ""
} else {
    Write-Host "[Step 3/4] Manual editing required..." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "============================================================================" -ForegroundColor Cyan
    Write-Host " NEXT STEPS:" -ForegroundColor Yellow
    Write-Host " 1. Open: core_controls_config.json"
    Write-Host " 2. Set `"selected`": true for controls you want to include"
    Write-Host " 3. Save the file"
    Write-Host " 4. Press any key to continue..."
    Write-Host ""
    Write-Host " TIP: You can also review core_controls_selection.txt for reference"
    Write-Host "============================================================================" -ForegroundColor Cyan
    Write-Host ""
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

# Step 4: Extract final dataset
Write-Host "[Step 4/4] Extracting final core controls dataset..." -ForegroundColor Green
Write-Host "Command: python extract_core_controls_from_config.py"
Write-Host ""
python extract_core_controls_from_config.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to extract core controls" -ForegroundColor Red
    exit 1
}
Write-Host ""
Write-Host "[SUCCESS] Final dataset created: data/go_to_core_controls.json" -ForegroundColor Green
Write-Host ""

# Step 5: Apply Core Controls Overrides (control-level tuning)
Write-Host "[Step 5/6] Applying control overrides from configuration..." -ForegroundColor Yellow

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$applierScript = Join-Path $scriptDir "apply_self_calibration.py"
$configFile = Join-Path $scriptDir "config\self_calibration.json"

# Apply to raw dataset first (used by test runtime)
Write-Host "  [5a] Applying to go_to_core_controls_raw.json..." -ForegroundColor Gray
$rawDatasetFile = Join-Path $scriptDir "data\go_to_core_controls_raw.json"
python $applierScript --input $rawDatasetFile --output $rawDatasetFile --config $configFile
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to apply control overrides to raw dataset" -ForegroundColor Red
    exit 1
}

# Apply to final dataset (used by test generation)
Write-Host "  [5b] Applying to go_to_core_controls.json..." -ForegroundColor Gray
$datasetFile = Join-Path $scriptDir "data\go_to_core_controls.json"
python $applierScript --input $datasetFile --output $datasetFile --config $configFile
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to apply control overrides to final dataset" -ForegroundColor Red
    exit 1
}
Write-Host ""
Write-Host "[SUCCESS] Self-calibration applied to both datasets from config/self_calibration.json" -ForegroundColor Green
Write-Host ""

# ============================================================================
# Step 6: Generate Navigation Test Cases
# ============================================================================
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host "[Step 6/6] Generating navigation test cases..." -ForegroundColor Green
Write-Host "Command: python generate_navigation_test_cases.py --max-depth 10" -ForegroundColor Gray
Write-Host ""

$generatorScript = Join-Path $scriptDir "generate_navigation_test_cases.py"
& python $generatorScript --max-depth 10
$generatorExitCode = $LASTEXITCODE

if ($generatorExitCode -ne 0) {
    Write-Host "[ERROR] Failed to generate navigation test cases" -ForegroundColor Red
    exit 1
}
Write-Host ""
Write-Host "[SUCCESS] Navigation test cases generated successfully" -ForegroundColor Green
Write-Host ""

# Summary
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host " Workflow Complete!" -ForegroundColor Green
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host " Output Files:" -ForegroundColor Yellow
Write-Host "   - data/go_to_core_controls_raw.json     (Intermediate: 211 controls)"
Write-Host "   - config/core_controls_config.json       (Control selection configuration)"
Write-Host "   - data/go_to_core_controls.json          (Final dataset with calibrations)"
Write-Host "   - data/go_to_core_controls_backup_*.json (Backup before calibrations)"
Write-Host "   - ../../../test_space/test_cases/navigations/core/*.yaml (Generated test cases)"
Write-Host ""
Write-Host " Configuration Files:" -ForegroundColor Yellow
Write-Host "   - config/build_workflow_config.json      (Build workflow configuration)"
Write-Host "   - config/self_calibration.json           (Self-calibration configuration)"
Write-Host "   - config/test_case_generation_config.json (Test case generation settings)"
Write-Host ""
Write-Host " Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Review generated YAML files in: ../../../test_space/test_cases/navigations/core/"
Write-Host "   2. Edit config/self_calibration.json to fine-tune controls if needed"
Write-Host "   3. Re-run this script to regenerate with changes"
Write-Host "============================================================================" -ForegroundColor Cyan
Write-Host ""
