# Run commands quietly: print only failures and a one-line summary. The full output goes to .logs/<Name>.log (git-ignored).
# Used by `just test-quiet` and `just lint-quiet`. The normal recipes (`just test`, `just lint`) stay as they are.
# Rules: one native command per -Commands entry (a `;` chain keeps only the last exit code).
#        A command that cannot start counts as a failure. Test it with `just quiet-selftest`.
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Name,
    [Parameter(Mandatory)][string[]]$Commands
)
if ($Name -notmatch '^[A-Za-z0-9_-]+$') {
    Write-Host "quiet: -Name must match [A-Za-z0-9_-]+ (got: $Name)"
    exit 1
}
New-Item -ItemType Directory -Force .logs | Out-Null
$log = Join-Path .logs "$Name.log"
Set-Content -Path $log -Value "# $Name $(Get-Date -Format s)"
$bad = 0
$last = @()
foreach ($cmd in $Commands) {
    Add-Content -Path $log -Value "### $cmd"
    $global:LASTEXITCODE = 0
    $cannotStart = $false
    try {
        $items = @(& ([scriptblock]::Create($cmd)) 2>&1)
    }
    catch {
        $cannotStart = $true
        $items = @($_)
    }
    foreach ($item in $items) {
        if ($item -is [System.Management.Automation.ErrorRecord] -and
            $item.FullyQualifiedErrorId -match 'CommandNotFound|ProgramNotFound|ObjectNotFound') {
            $cannotStart = $true
        }
    }
    $code = $global:LASTEXITCODE
    if ($cannotStart -and $code -eq 0) { $code = 127 }
    $text = ($items | ForEach-Object { "$_" } | Out-String)
    Add-Content -Path $log -Value $text
    $lines = @($text -split "`r?`n" | Where-Object { $_.Trim() })
    if ($code -ne 0) {
        $bad++
        Write-Host "FAIL ($code): $cmd"
        $lines | Select-Object -Last 40 | ForEach-Object { Write-Host $_ }
    }
    elseif ($lines.Count -gt 0) {
        $last += $lines[-1].Trim()
    }
}
if ($bad -gt 0) {
    Write-Host "$Name FAILED: $bad of $($Commands.Count) commands. Full log: $log"
    exit 1
}
Write-Host "$Name OK: $($last -join ' | ')  (log: $log)"
exit 0
