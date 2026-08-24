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
if ($null -eq $python) {
    $python = Get-Command python3 -ErrorAction SilentlyContinue
}
if ($null -eq $python) {
    throw 'Python 3.11 or newer was not found.'
}

New-Item -ItemType Directory -Path $automationRoot -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $automationRoot 'prompts') -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'memory_core.py') -Destination $automationRoot -Force
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'routine_runner.py') -Destination $automationRoot -Force
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'validate_vault.py') -Destination $automationRoot -Force
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'run-hidden.vbs') -Destination $automationRoot -Force
$pluginRoot = Split-Path -Parent $PSScriptRoot
Copy-Item -Path (Join-Path $pluginRoot 'assets\prompts\*') -Destination (Join-Path $automationRoot 'prompts') -Recurse -Force

$runner = Join-Path $automationRoot 'routine_runner.py'
$hiddenRunner = Join-Path $automationRoot 'run-hidden.vbs'
$wscript = Join-Path $env:SystemRoot 'System32\wscript.exe'
if (-not (Test-Path -LiteralPath $wscript)) {
    throw 'wscript.exe was not found.'
}
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 2) -Hidden
$weeklyArguments = '"{0}" "{1}" "{2}" weekly' -f $hiddenRunner, $python.Source, $runner
$monthlyArguments = '"{0}" "{1}" "{2}" monthly' -f $hiddenRunner, $python.Source, $runner
$weeklyAction = New-ScheduledTaskAction -Execute $wscript -Argument $weeklyArguments -WorkingDirectory $automationRoot
$monthlyAction = New-ScheduledTaskAction -Execute $wscript -Argument $monthlyArguments -WorkingDirectory $automationRoot
$weeklyTrigger = New-ScheduledTaskTrigger -Daily -At '09:00'
$monthlyTrigger = New-ScheduledTaskTrigger -Daily -At '09:15'

Register-ScheduledTask -TaskName $weeklyTask -Action $weeklyAction -Trigger $weeklyTrigger -Settings $settings -Description 'Create one evidence-backed Obsidian project brief per ISO week.' -Force | Out-Null
Register-ScheduledTask -TaskName $monthlyTask -Action $monthlyAction -Trigger $monthlyTrigger -Settings $settings -Description 'Run one non-destructive Obsidian memory audit per month.' -Force | Out-Null
Write-Output 'automation_installed=true'
Write-Output "weekly_task=$weeklyTask"
Write-Output "monthly_task=$monthlyTask"
