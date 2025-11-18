# Install Windows Scheduled Task for Automated Data Processing
# Run this script as Administrator in PowerShell

# Check if running as Administrator
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
$isAdmin = $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "Error: This script must be run as Administrator" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

Write-Host "Property Outage Dashboard - Scheduled Task Installation" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

# Get the project directory
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ScriptPath = Join-Path $ProjectDir "auto-process-data.bat"

Write-Host "Project directory: $ProjectDir" -ForegroundColor Green
Write-Host "Script path: $ScriptPath" -ForegroundColor Green
Write-Host ""

# Check if script exists
if (-not (Test-Path $ScriptPath)) {
    Write-Host "Error: auto-process-data.bat not found at $ScriptPath" -ForegroundColor Red
    exit 1
}

# Task name and description
$TaskName = "OutageDashboardAutoProcess"
$TaskDescription = "Automatically processes new outage data files every 6 hours"

# Remove existing task if it exists
$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "Removing existing scheduled task..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Create the action (what to run)
$Action = New-ScheduledTaskAction -Execute $ScriptPath -WorkingDirectory $ProjectDir

# Create the trigger (when to run - every 6 hours)
$Trigger1 = New-ScheduledTaskTrigger -Daily -At "00:00"  # Midnight
$Trigger2 = New-ScheduledTaskTrigger -Daily -At "06:00"  # 6 AM
$Trigger3 = New-ScheduledTaskTrigger -Daily -At "12:00"  # Noon
$Trigger4 = New-ScheduledTaskTrigger -Daily -At "18:00"  # 6 PM

# Combine triggers
$Triggers = @($Trigger1, $Trigger2, $Trigger3, $Trigger4)

# Create the principal (run as current user)
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType S4U

# Create the settings
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable:$false `
    -MultipleInstances IgnoreNew

# Register the scheduled task
Write-Host "Creating scheduled task '$TaskName'..." -ForegroundColor Green
Register-ScheduledTask `
    -TaskName $TaskName `
    -Description $TaskDescription `
    -Action $Action `
    -Trigger $Triggers `
    -Principal $Principal `
    -Settings $Settings

Write-Host ""
Write-Host "Installation complete!" -ForegroundColor Green -BackgroundColor Black
Write-Host ""
Write-Host "The auto-processing script will now run every 6 hours at:" -ForegroundColor Cyan
Write-Host "  - 00:00 (midnight)" -ForegroundColor White
Write-Host "  - 06:00 (6 AM)" -ForegroundColor White
Write-Host "  - 12:00 (noon)" -ForegroundColor White
Write-Host "  - 18:00 (6 PM)" -ForegroundColor White
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor Cyan
Write-Host "  View task:        Get-ScheduledTask -TaskName '$TaskName'" -ForegroundColor White
Write-Host "  Run now:          Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor White
Write-Host "  Disable task:     Disable-ScheduledTask -TaskName '$TaskName'" -ForegroundColor White
Write-Host "  Enable task:      Enable-ScheduledTask -TaskName '$TaskName'" -ForegroundColor White
Write-Host "  Remove task:      Unregister-ScheduledTask -TaskName '$TaskName'" -ForegroundColor White
Write-Host "  View history:     Get-WinEvent -LogName 'Microsoft-Windows-TaskScheduler/Operational' | Where-Object {$_.Message -like '*$TaskName*'} | Select-Object -First 10" -ForegroundColor White
Write-Host ""
Write-Host "To view the processing log:" -ForegroundColor Cyan
Write-Host "  Get-Content logs\auto-process.log -Tail 50" -ForegroundColor White
Write-Host ""
