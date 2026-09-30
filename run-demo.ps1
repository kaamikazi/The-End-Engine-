param([string]$OutputDir = '', [switch]$VerboseTrace, [switch]$V02, [switch]$V03)
$ErrorActionPreference = 'Stop'
$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
$bundledPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
if ($pythonCommand) {
    $enginePython = $pythonCommand.Source
} elseif (Test-Path -LiteralPath $bundledPython) {
    $enginePython = $bundledPython
} else {
    throw 'Python 3.11+ is required. Install Python, then run python -m end_engine.demo.'
}
Push-Location $PSScriptRoot
try {
    if ($V02 -and $V03) { throw 'Choose only one demo version.' }
    $demoModule = if ($V03) { 'end_engine.demo_v03' } elseif ($V02) { 'end_engine.demo_v02' } else { 'end_engine.demo' }
    if (-not $OutputDir) { $OutputDir = if ($V03) { 'demo_v03_output' } elseif ($V02) { 'demo_v02_output' } else { 'demo_output' } }
    $demoArguments = @('-m', $demoModule, '--output-dir', $OutputDir)
    if ($VerboseTrace) { $demoArguments += '--verbose' }
    & $enginePython @demoArguments
    if ($LASTEXITCODE -ne 0) { throw "END demo exited with code $LASTEXITCODE" }
} finally {
    Pop-Location
}
