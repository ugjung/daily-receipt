# Daily receipt scheduler for Windows. ASCII only (Windows PowerShell 5.1 reads non-BOM files as ANSI).
#   -Time 18:00 [-EveryDay] [-NoOpen]   turn on / change time
#   -Off                                  turn off
#   -Status                               show current state
#   -Store "..." -Customer "..."          save names shown on the receipt
param(
    [string]$Time,
    [switch]$EveryDay,
    [switch]$NoOpen,
    [switch]$Off,
    [switch]$Status,
    [string]$Store,
    [string]$Customer
)
$ErrorActionPreference = 'Stop'
$TaskName = 'ClaudeDailyReceipt'
$Dir = Join-Path $HOME '.claude\daily-receipt'
$ConfigPath = Join-Path $Dir 'config.json'
$RunPath = Join-Path $Dir 'run.ps1'
New-Item -ItemType Directory -Force -Path (Join-Path $Dir 'logs') | Out-Null

function Read-Config {
    if (Test-Path $ConfigPath) { return Get-Content $ConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json }
    return New-Object psobject
}
function Write-Config($cfg) {
    $json = $cfg | ConvertTo-Json
    [IO.File]::WriteAllText($ConfigPath, $json, (New-Object Text.UTF8Encoding($false)))
}
function Set-Field($obj, $name, $value) {
    if ($obj.PSObject.Properties[$name]) { $obj.$name = $value } else { $obj | Add-Member -NotePropertyName $name -NotePropertyValue $value }
}

$cfg = Read-Config
if ($Store) { Set-Field $cfg 'store' $Store }
if ($Customer) { Set-Field $cfg 'customer' $Customer }

if ($Off) {
    if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    }
    Set-Field $cfg 'schedule' $null
    Write-Config $cfg
    Write-Output "OFF: task removed"
    exit 0
}

if ($Time) {
    if ($Time -notmatch '^\d{1,2}:\d{2}$') { throw "Time must be HH:mm, got '$Time'" }
    $claude = (Get-Command claude -ErrorAction SilentlyContinue).Source
    if (-not $claude) { throw "claude command not found in PATH" }
    if ($claude -like '*.ps1') { $alt = [IO.Path]::ChangeExtension($claude, '.cmd'); if (Test-Path $alt) { $claude = $alt } }
    $open = if ($NoOpen) { '$false' } else { '$true' }

    # run.ps1: what the scheduler executes. Permissions are limited to python scripts,
    # reading, and writing inside Documents\claude-receipts.
    $run = @"
`$ErrorActionPreference = 'Continue'
`$day = Get-Date -Format 'yyyy-MM-dd'
`$log = Join-Path '$Dir\logs' "`$day.log"
[Console]::OutputEncoding = [Text.Encoding]::UTF8
`$OutputEncoding = [Text.Encoding]::UTF8
Set-Location `$HOME
& '$claude' -p '/daily-receipt:receipt scheduled-run' --allowedTools 'Bash(python *)' 'Read' 'Glob' 'Edit(~/Documents/claude-receipts/**)' *> `$log
`$html = Join-Path `$HOME "Documents\claude-receipts\`$day.html"
if ($open -and (Test-Path `$html) -and ((Get-Item `$html).LastWriteTime -gt (Get-Date).AddHours(-1))) { Start-Process `$html }
Get-ChildItem '$Dir\logs' -Filter *.log | Where-Object LastWriteTime -lt (Get-Date).AddDays(-30) | Remove-Item -ErrorAction SilentlyContinue
"@
    [IO.File]::WriteAllText($RunPath, $run, (New-Object Text.UTF8Encoding($true)))

    $at = [datetime]::ParseExact($Time.PadLeft(5, '0'), 'HH:mm', $null)
    $trigger = if ($EveryDay) { New-ScheduledTaskTrigger -Daily -At $at }
               else { New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At $at }
    $action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$RunPath`""
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 30) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
    Register-ScheduledTask -TaskName $TaskName -Trigger $trigger -Action $action -Settings $settings -Description 'Claude Code daily receipt' -Force | Out-Null
    Set-Field $cfg 'schedule' ([ordered]@{ time = $Time; weekdays_only = (-not $EveryDay); open_after = (-not $NoOpen) })
    Write-Output "ON: $Time $(if ($EveryDay) {'every day'} else {'weekdays'})"
}

Write-Config $cfg

if ($Status -or -not ($Time -or $Store -or $Customer)) {
    $t = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($t) {
        $i = $t | Get-ScheduledTaskInfo
        Write-Output "task: ON, next run $($i.NextRunTime), last run $($i.LastRunTime) (result $($i.LastTaskResult))"
    } else { Write-Output "task: OFF" }
    Write-Output "config: $(Get-Content $ConfigPath -Raw -Encoding UTF8)"
}
