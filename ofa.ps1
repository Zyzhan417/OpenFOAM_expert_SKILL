# ========================================================================
# OpenFOAM Expert Skill v2.2 - Unified CLI Entry Point (PowerShell)
# ========================================================================
#
# Usage: .\ofa.ps1 [command] [options]
#
# Commands:
#   inheritance [class]  - Analyze class inheritance
#   boundary [name]      - Analyze boundary condition
#   model [type] [name]  - Analyze physics model
#   modifier             - Code modification suggestions
#   search [pattern]     - Search code in source
#   version              - Show version info
#   help                 - Show this help
#   clear-cache          - Clear analysis cache
#   test                 - Run skill tests
# ========================================================================

param(
    [Parameter(Position=0)]
    [string]$Command = "help",
    
    [Parameter(ValueFromRemainingArguments)]
    [string[]]$RemainingArgs
)

# ------------------------------------------------------------------------
# Auto-detect SKILL_ROOT
# Priority:
#   1. OPENFOAM_SKILL_ROOT environment variable
#   2. Script's parent directory
#   3. Default user-level location
# ------------------------------------------------------------------------
if ($env:OPENFOAM_SKILL_ROOT) {
    $SKILL_ROOT = $env:OPENFOAM_SKILL_ROOT
} elseif (Test-Path "$PSScriptRoot\scripts\router.py") {
    $SKILL_ROOT = $PSScriptRoot
} elseif (Test-Path "$env:APPDATA\CodeBuddy CN\User\globalStorage\tencent-cloud.coding-copilot\skills\openfoam-expert\scripts\router.py") {
    $SKILL_ROOT = "$env:APPDATA\CodeBuddy CN\User\globalStorage\tencent-cloud.coding-copilot\skills\openfoam-expert"
} else {
    Write-Host "[ERROR] Cannot locate OpenFOAM Expert Skill root directory" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please set OPENFOAM_SKILL_ROOT environment variable or run from skill directory."
    exit 1
}

# Validate Python availability
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "[ERROR] Python not found in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.x and ensure it is accessible from command line."
    exit 1
}

# Set paths
$SCRIPTS_DIR = "$SKILL_ROOT\scripts"
$SRC_DIR = "$SKILL_ROOT\attachments\OpenFOAM\src"

# Check if router exists
if (-not (Test-Path "$SCRIPTS_DIR\router.py")) {
    Write-Host "[ERROR] Router script not found at: $SCRIPTS_DIR\router.py" -ForegroundColor Red
    Write-Host "The skill may be corrupted or incomplete."
    exit 1
}

# ------------------------------------------------------------------------
# Command dispatch
# ------------------------------------------------------------------------
function Show-Help {
    Write-Host ""
    Write-Host "OpenFOAM Expert Skill v2.2 - Unified CLI" -ForegroundColor Cyan
    Write-Host "=========================================="
    Write-Host ""
    Write-Host "Usage: ofa [command] [options]"
    Write-Host ""
    Write-Host "Commands:"
    Write-Host "  inheritance    Analyze class inheritance"
    Write-Host "  boundary       Analyze boundary conditions"
    Write-Host "  model          Analyze physics models"
    Write-Host "  modifier       Generate code modification suggestions"
    Write-Host "  search         Search code in OpenFOAM source"
    Write-Host "  version        Show version information"
    Write-Host "  clear-cache    Clear analysis cache"
    Write-Host "  test           Run skill tests"
    Write-Host "  help           Show this help message"
    Write-Host ""
    Write-Host "Inheritance Analysis:"
    Write-Host "  ofa inheritance --class fvMesh --chain"
    Write-Host "  ofa inheritance --class kEpsilon --tree --depth 3"
    Write-Host "  ofa inheritance --class turbulenceModel --suggest extend"
    Write-Host ""
    Write-Host "Model Analysis:"
    Write-Host "  ofa model --type turbulence --name kEpsilon"
    Write-Host "  ofa model --type multiphase --name interFoam"
    Write-Host "  ofa model --type thermophysical --name heRhoThermo"
    Write-Host ""
    Write-Host "Boundary Condition Analysis:"
    Write-Host "  ofa boundary --name fixedValue --params"
    Write-Host "  ofa boundary --name inletOutlet --examples"
    Write-Host ""
    Write-Host "Code Search:"
    Write-Host "  ofa search `"class.*fvMesh`" --file-types .H"
    Write-Host ""
    Write-Host "Output Formats:"
    Write-Host "  --format json     JSON output (default)"
    Write-Host "  --format text     Human-readable text"
    Write-Host "  --format compact  Compact JSON"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  --root PATH       OpenFOAM src directory (auto-detected)"
    Write-Host "  --mode MODE       Access mode: auto, mcp, local"
    Write-Host "  --no-cache        Disable result caching"
    Write-Host ""
    Write-Host "Skill Location: $SKILL_ROOT"
    Write-Host "Source Location: $SRC_DIR"
    Write-Host ""
}

function Show-Version {
    & python "$SCRIPTS_DIR\router.py" version
}

function Clear-Cache {
    Write-Host "Clearing analysis cache..."
    & python "$SCRIPTS_DIR\router.py" clear-cache
    Write-Host "Done."
}

function Run-Test {
    Write-Host "Running OpenFOAM Expert Skill tests..."
    & python "$SKILL_ROOT\test_skill.py"
}

# Dispatch based on command
switch ($Command.ToLower()) {
    { $_ -in @("help", "--help", "-h", "") } { Show-Help }
    { $_ -in @("version", "-v", "--version") } { Show-Version }
    "clear-cache" { Clear-Cache }
    "test" { Run-Test }
    default {
        # Pass to router
        $allArgs = @($Command, "--root", $SRC_DIR) + $RemainingArgs
        & python "$SCRIPTS_DIR\router.py" @allArgs
    }
}
