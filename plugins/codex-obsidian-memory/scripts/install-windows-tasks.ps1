param(
    [switch]$Uninstall,
    [string]$TaskPrefix = 'Codex Obsidian Memory'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$codexRoot = if ($env:CODEX_HOME) {
    [System.IO.Path]::GetFullPath($env:CODEX_HOME)
} else {
    Join-Path ([Environment]::GetFolderPath('UserProfile')) '.codex'
}
$automationRoot = Join-Path $codexRoot 'obsidian-memory\automation'
$weeklyTask = "$TaskPrefix Weekly Brief"
$monthlyTask = "$TaskPrefix Monthly Audit"

if ($Uninstall) {
    foreach ($taskName in @($weeklyTask, $monthlyTask)) {
        $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
        if ($null -ne $task) {
            Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
        }
    }
    if (Test-Path -LiteralPath $automationRoot) {
        Remove-Item -LiteralPath $automationRoot -Recurse -Force
    }
    Write-Output 'automation_installed=false'
    exit 0
}

$python = Get-Command py.exe -ErrorAction SilentlyContinue
$pythonPrefix = '-3 '
if ($null -eq $python) {
    $python = Get-Command python3 -ErrorAction SilentlyContinue
    $pythonPrefix = ''
}
if ($null -eq $python) {
    throw 'Python 3.11 or newer was not found.'
}

New-Item -ItemType Directory -Path $automationRoot -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $automationRoot 'prompts') -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'memory_core.py') -Destination $automationRoot -Force
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'routine_runner.py') -Destination $automationRoot -Force
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'validate_vault.py') -Destination $automationRoot -Force
$pluginRoot = Split-Path -Parent $PSScriptRoot
Copy-Item -LiteralPath (Join-Path $pluginRoot 'assets\prompts\weekly.md') -Destination (Join-Path $automationRoot 'prompts\weekly.md') -Force
Copy-Item -LiteralPath (Join-Path $pluginRoot 'assets\prompts\monthly.md') -Destination (Join-Path $automationRoot 'prompts\monthly.md') -Force

$runner = Join-Path $automationRoot 'routine_runner.py'
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 2)
$weeklyAction = New-ScheduledTaskAction -Execute $python.Source -Argument ($pythonPrefix + '"' + $runner + '" weekly') -WorkingDirectory $automationRoot
$monthlyAction = New-ScheduledTaskAction -Execute $python.Source -Argument ($pythonPrefix + '"' + $runner + '" monthly') -WorkingDirectory $automationRoot
$weeklyTrigger = New-ScheduledTaskTrigger -Daily -At '09:00'
$monthlyTrigger = New-ScheduledTaskTrigger -Daily -At '09:15'

Register-ScheduledTask -TaskName $weeklyTask -Action $weeklyAction -Trigger $weeklyTrigger -Settings $settings -Description 'Create one evidence-backed Obsidian project brief per ISO week.' -Force | Out-Null
Register-ScheduledTask -TaskName $monthlyTask -Action $monthlyAction -Trigger $monthlyTrigger -Settings $settings -Description 'Run one non-destructive Obsidian memory audit per month.' -Force | Out-Null
Write-Output 'automation_installed=true'
Write-Output "weekly_task=$weeklyTask"
Write-Output "monthly_task=$monthlyTask"
