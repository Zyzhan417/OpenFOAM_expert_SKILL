@echo off
REM ========================================================================
REM OpenFOAM Expert Skill v2.2 - Unified CLI Entry Point
REM ========================================================================
REM
REM Usage: ofa [command] [options]
REM
REM Commands:
REM   inheritance [class]  - Analyze class inheritance
REM   boundary [name]      - Analyze boundary condition
REM   model [type] [name]  - Analyze physics model
REM   modifier             - Code modification suggestions
REM   search [pattern]     - Search code in source
REM   version              - Show version info
REM   help                 - Show this help
REM   clear-cache          - Clear analysis cache
REM   test                 - Run skill tests
REM
REM Examples:
REM   ofa inheritance fvMesh --chain
REM   ofa model turbulence kEpsilon
REM   ofa boundary fixedValue --params
REM   ofa search "class.*fvMesh" --file-types .H
REM ========================================================================

setlocal EnableDelayedExpansion

REM ------------------------------------------------------------------------
REM Auto-detect SKILL_ROOT
REM Priority:
REM   1. OPENFOAM_SKILL_ROOT environment variable
REM   2. Script's parent directory
REM   3. Default user-level location
REM ------------------------------------------------------------------------
if defined OPENFOAM_SKILL_ROOT (
    set "SKILL_ROOT=%OPENFOAM_SKILL_ROOT%"
) else if exist "%~dp0scripts\router.py" (
    set "SKILL_ROOT=%~dp0"
) else if exist "%APPDATA%\CodeBuddy CN\User\globalStorage\tencent-cloud.coding-copilot\skills\openfoam-expert\scripts\router.py" (
    set "SKILL_ROOT=%APPDATA%\CodeBuddy CN\User\globalStorage\tencent-cloud.coding-copilot\skills\openfoam-expert"
) else (
    echo [ERROR] Cannot locate OpenFOAM Expert Skill root directory
    echo.
    echo Please set OPENFOAM_SKILL_ROOT environment variable or run from skill directory.
    exit /b 1
)

REM Validate Python availability
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python not found in PATH
    echo Please install Python 3.x and ensure it is accessible from command line.
    exit /b 1
)

REM Set paths
set "SCRIPTS_DIR=%SKILL_ROOT%\scripts"
set "SRC_DIR=%SKILL_ROOT%\attachments\OpenFOAM\src"

REM Check if router exists
if not exist "%SCRIPTS_DIR%\router.py" (
    echo [ERROR] Router script not found at: %SCRIPTS_DIR%\router.py
    echo The skill may be corrupted or incomplete.
    exit /b 1
)

REM ------------------------------------------------------------------------
REM Command dispatch
REM ------------------------------------------------------------------------
set "COMMAND=%~1"

if "%COMMAND%"=="" goto :show_help
if "%COMMAND%"=="help" goto :show_help
if "%COMMAND%"=="--help" goto :show_help
if "%COMMAND%"=="-h" goto :show_help
if "%COMMAND%"=="version" goto :show_version
if "%COMMAND%"=="-v" goto :show_version
if "%COMMAND%"=="--version" goto :show_version
if "%COMMAND%"=="clear-cache" goto :clear_cache
if "%COMMAND%"=="test" goto :run_test

REM Default: pass to router
shift
python "%SCRIPTS_DIR%\router.py" %COMMAND% --root "%SRC_DIR%" %*
exit /b %ERRORLEVEL%

REM ------------------------------------------------------------------------
REM Show version information
REM ------------------------------------------------------------------------
:show_version
python "%SCRIPTS_DIR%\router.py" version
exit /b %ERRORLEVEL%

REM ------------------------------------------------------------------------
REM Clear cache
REM ------------------------------------------------------------------------
:clear_cache
echo Clearing analysis cache...
python "%SCRIPTS_DIR%\router.py" clear-cache
echo Done.
exit /b %ERRORLEVEL%

REM ------------------------------------------------------------------------
REM Run tests
REM ------------------------------------------------------------------------
:run_test
echo Running OpenFOAM Expert Skill tests...
python "%SKILL_ROOT%\test_skill.py"
exit /b %ERRORLEVEL%

REM ------------------------------------------------------------------------
REM Show help
REM ------------------------------------------------------------------------
:show_help
echo.
echo OpenFOAM Expert Skill v2.2 - Unified CLI
echo ==========================================
echo.
echo Usage: ofa [command] [options]
echo.
echo Commands:
echo   inheritance    Analyze class inheritance
echo   boundary       Analyze boundary conditions
echo   model          Analyze physics models
echo   modifier       Generate code modification suggestions
echo   search         Search code in OpenFOAM source
echo   version        Show version information
echo   clear-cache    Clear analysis cache
echo   test           Run skill tests
echo   help           Show this help message
echo.
echo Inheritance Analysis:
echo   ofa inheritance --class fvMesh --chain
echo   ofa inheritance --class kEpsilon --tree --depth 3
echo   ofa inheritance --class turbulenceModel --suggest extend
echo.
echo Model Analysis:
echo   ofa model --type turbulence --name kEpsilon
echo   ofa model --type multiphase --name interFoam
echo   ofa model --type thermophysical --name heRhoThermo
echo.
echo Boundary Condition Analysis:
echo   ofa boundary --name fixedValue --params
echo   ofa boundary --name inletOutlet --examples
echo.
echo Code Search:
echo   ofa search "class.*fvMesh" --file-types .H
echo.
echo Output Formats:
echo   --format json     JSON output (default)
echo   --format text     Human-readable text
echo   --format compact  Compact JSON
echo.
echo Options:
echo   --root PATH       OpenFOAM src directory (auto-detected)
echo   --mode MODE       Access mode: auto, mcp, local
echo   --no-cache        Disable result caching
echo.
echo Skill Location: %SKILL_ROOT%
echo Source Location: %SRC_DIR%
echo.
exit /b 0
