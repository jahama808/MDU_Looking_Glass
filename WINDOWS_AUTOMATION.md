# Windows Automated Processing Setup

This guide explains how to set up automated data processing on Windows using Task Scheduler.

## Quick Installation

1. **Open PowerShell as Administrator**
   - Right-click the Start button
   - Select "Windows PowerShell (Admin)" or "Terminal (Admin)"

2. **Navigate to the project directory**
   ```powershell
   cd "C:\path\to\theNewOutageLookingGlass"
   ```

3. **Run the installation script**
   ```powershell
   .\install-scheduled-task.ps1
   ```

This will create a scheduled task that runs every 6 hours at:
- **00:00** (midnight)
- **06:00** (6 AM)
- **12:00** (noon)
- **18:00** (6 PM)

## What It Does

The automated process:
1. Looks for new files in the `inputs\` directory:
   - network outages files matching: `network_outages-*.csv`
   - Eero discovery files matching: `Eero Discovery Details*.csv`
2. Checks if files have already been processed (in `inputs_already_read\`)
3. Processes the files using `process_property_outages_db.py`
4. Updates the database at `output\outages.db`
5. Moves processed files to `inputs_already_read\<timestamp>\`
6. Logs all activity to `logs\auto-process.log`

## Manual Setup (Alternative Method)

If you prefer to set up the scheduled task manually:

1. **Open Task Scheduler**
   - Press `Win + R`
   - Type `taskschd.msc`
   - Press Enter

2. **Create a New Task**
   - Click "Create Basic Task" in the right panel
   - Name: `OutageDashboardAutoProcess`
   - Description: `Automatically processes new outage data files every 6 hours`

3. **Set Trigger**
   - Select "Daily"
   - Set start time to `00:00` (midnight)
   - Recur every: `1` day

4. **Set Action**
   - Action: "Start a program"
   - Program/script: Browse to `auto-process-data.bat` in the project directory
   - Start in: Enter the full path to the project directory

5. **Create Additional Triggers**
   - After creating the task, right-click it and select "Properties"
   - Go to "Triggers" tab
   - Add three more triggers for 06:00, 12:00, and 18:00

6. **Configure Settings**
   - Under "Settings" tab:
     - ✓ Allow task to be run on demand
     - ✓ Run task as soon as possible after a scheduled start is missed
     - ✓ If the task fails, restart every: 1 hour
   - Under "Conditions" tab:
     - ✓ Start the task only if the computer is on AC power (optional)
     - ✓ Wake the computer to run this task (optional)

## Managing the Scheduled Task

### Using PowerShell

```powershell
# View task status
Get-ScheduledTask -TaskName "OutageDashboardAutoProcess"

# Run the task now
Start-ScheduledTask -TaskName "OutageDashboardAutoProcess"

# Disable the task
Disable-ScheduledTask -TaskName "OutageDashboardAutoProcess"

# Enable the task
Enable-ScheduledTask -TaskName "OutageDashboardAutoProcess"

# Remove the task
Unregister-ScheduledTask -TaskName "OutageDashboardAutoProcess" -Confirm:$false

# View recent task history
Get-WinEvent -LogName "Microsoft-Windows-TaskScheduler/Operational" |
    Where-Object {$_.Message -like "*OutageDashboardAutoProcess*"} |
    Select-Object -First 10
```

### Using Task Scheduler GUI

1. Open Task Scheduler (`taskschd.msc`)
2. Find "OutageDashboardAutoProcess" in the task list
3. Right-click for options:
   - **Run** - Execute now
   - **End** - Stop if running
   - **Disable** - Prevent from running
   - **Properties** - Modify settings
   - **Delete** - Remove the task

## Viewing Logs

### PowerShell
```powershell
# View last 50 lines of the log
Get-Content logs\auto-process.log -Tail 50

# Monitor log in real-time
Get-Content logs\auto-process.log -Wait

# View log with timestamps
Get-Content logs\auto-process.log | Select-String "2025-11-08"
```

### Command Prompt
```cmd
REM View the entire log
type logs\auto-process.log

REM View last 20 lines
powershell -Command "Get-Content logs\auto-process.log -Tail 20"
```

## Troubleshooting

### Task not running?

1. **Check task status**
   ```powershell
   Get-ScheduledTask -TaskName "OutageDashboardAutoProcess" | Select-Object State
   ```
   - If "Disabled", enable it:
     ```powershell
     Enable-ScheduledTask -TaskName "OutageDashboardAutoProcess"
     ```

2. **Check task history**
   - Open Task Scheduler
   - Select the task
   - Click "History" tab at the bottom
   - Look for errors or warnings

### Task failing?

1. **Check the log file**
   ```powershell
   Get-Content logs\auto-process.log -Tail 50
   ```

2. **Run the script manually** to see errors
   ```cmd
   auto-process-data.bat
   ```

3. **Common issues:**
   - Virtual environment not found → Run `install.bat` first
   - Files not found → Check that files exist in `inputs\` directory
   - Permission denied → Run Task Scheduler as Administrator

### No files being processed?

1. **Check the inputs directory**
   ```cmd
   dir inputs\
   ```

2. **Verify file names match patterns:**
   - `network_outages-YYYY-MM-DD.csv`
   - `Eero Discovery Details - YYYY-MM-DD HHMMSS.csv`

3. **Check if files are in archive**
   ```cmd
   dir inputs_already_read\ /s
   ```

## Testing the Automation

1. **Place test files in the inputs directory**
   ```cmd
   copy "network_outages-2025-11-08.csv" inputs\
   copy "Eero Discovery Details - 2025-11-08 120000.csv" inputs\
   ```

2. **Run the task manually**
   ```powershell
   Start-ScheduledTask -TaskName "OutageDashboardAutoProcess"
   ```

3. **Check the results**
   ```powershell
   # View log
   Get-Content logs\auto-process.log -Tail 20

   # Check if files were moved
   dir inputs_already_read\
   ```

## Uninstalling

### Using PowerShell
```powershell
Unregister-ScheduledTask -TaskName "OutageDashboardAutoProcess" -Confirm:$false
```

### Using Task Scheduler
1. Open Task Scheduler
2. Find "OutageDashboardAutoProcess"
3. Right-click → Delete

## Notes

- The task runs as your user account (not SYSTEM)
- The task will run even if you're not logged in (stored credentials)
- If the computer is off during a scheduled run, it will run as soon as possible after startup
- Multiple instances are prevented (if one run is still processing, the next scheduled run is skipped)
- All output is logged to `logs\auto-process.log`

## Support

For issues specific to Windows automation, check:
- Task Scheduler event logs
- `logs\auto-process.log`
- README.md for general documentation
