# Regression test for scripts/quiet.ps1. Run it with `just quiet-selftest`. Exit code 1 if any case fails.
$shell = (Get-Process -Id $PID).Path
$quiet = Join-Path $PSScriptRoot 'quiet.ps1'
$fail = 0

function Quote([string]$Text) { "'" + ($Text -replace "'", "''") + "'" }

# Runs quiet.ps1 in a child shell, so its `exit` does not end this script.
function Test-Case([string]$Title, [bool]$ExpectFailure, [string]$Name, [string[]]$Commands) {
    $list = ($Commands | ForEach-Object { Quote $_ }) -join ','
    $tmp = [IO.Path]::ChangeExtension([IO.Path]::GetTempFileName(), '.ps1')
    Set-Content -Path $tmp -Value "& $(Quote $quiet) -Name $(Quote $Name) -Commands @($list); exit `$LASTEXITCODE"
    & $shell -NoProfile -File $tmp *> $null
    $code = $LASTEXITCODE
    Remove-Item -Path $tmp
    if (($code -ne 0) -eq $ExpectFailure) { Write-Host "ok   $Title" }
    else { Write-Host "FAIL $Title (exit $code)"; $script:fail++ }
}

$exit3 = "& $(Quote $shell) -NoProfile -Command 'exit 3'"
$exit0 = "& $(Quote $shell) -NoProfile -Command 'exit 0'"

Test-Case 'all commands pass: exit 0' $false 'selftest' @($exit0, $exit0)
Test-Case 'failing first, passing second: exit non-zero' $true 'selftest' @($exit3, $exit0)
Test-Case 'passing first, failing second: exit non-zero' $true 'selftest' @($exit0, $exit3)
Test-Case 'missing tool: exit non-zero' $true 'selftest' @('definitely-not-a-tool-xyz --version')
Test-Case 'syntax error in command: exit non-zero' $true 'selftest' @('if (')
Test-Case 'name with a path: rejected' $true '..\evil' @($exit0)

if ($fail -gt 0) { Write-Host "quiet-selftest FAILED: $fail case(s)"; exit 1 }
Write-Host 'quiet-selftest OK'
exit 0
