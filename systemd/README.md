# Systemd Automated Processing Setup (Linux)

This directory contains systemd service and timer files for automating the data processing every 6 hours.

## Quick Installation

```bash
cd systemd
sudo ./install-systemd.sh
```

This will:
- Install the service and timer files to `/etc/systemd/system/`
- Enable the timer to run every 6 hours
- Start the timer immediately

## Schedule

The auto-processing runs at:
- **00:00** (midnight)
- **06:00** (6 AM)
- **12:00** (noon)
- **18:00** (6 PM)

## What It Does

The automated process:
1. Looks for new files in the `inputs/` directory:
   - WAN connectivity files matching: `wan_connectivity-*.csv`
   - Eero discovery files matching: `Eero Discovery Details*.csv`
2. Checks if files have already been processed (in `inputs_already_read/`)
3. Processes the files using `process_property_outages_db.py`
4. Updates the database at `./output/outages.db`
5. Moves processed files to `inputs_already_read/<timestamp>/`
6. Logs all activity to `logs/auto-process.log`
7. Optionally restarts the API service if running

## Manual Installation

If you prefer to install manually:

```bash
# Copy the service file (edit paths first!)
sudo cp outage-auto-process.service /etc/systemd/system/

# Copy the timer file
sudo cp outage-auto-process.timer /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable the timer
sudo systemctl enable outage-auto-process.timer

# Start the timer
sudo systemctl start outage-auto-process.timer
```

**Important:** Edit `outage-auto-process.service` to replace the paths with your actual project directory before copying.

## Managing the Timer

### Check Status
```bash
# Check if timer is running
systemctl status outage-auto-process.timer

# Check when next run is scheduled
systemctl list-timers outage-auto-process.timer
```

### View Logs
```bash
# View service logs
journalctl -u outage-auto-process.service

# Follow logs in real-time
journalctl -u outage-auto-process.service -f

# View last 50 lines
journalctl -u outage-auto-process.service -n 50
```

### Manual Trigger
```bash
# Run the processing now (without waiting for scheduled time)
sudo systemctl start outage-auto-process.service

# Check the result
systemctl status outage-auto-process.service
```

### Stop/Disable
```bash
# Stop the timer (won't run automatically)
sudo systemctl stop outage-auto-process.timer

# Disable the timer (won't start on boot)
sudo systemctl disable outage-auto-process.timer

# Re-enable later
sudo systemctl enable outage-auto-process.timer
sudo systemctl start outage-auto-process.timer
```

## Troubleshooting

### Timer not running?
```bash
# Check timer status
systemctl status outage-auto-process.timer

# If disabled, enable it
sudo systemctl enable outage-auto-process.timer
sudo systemctl start outage-auto-process.timer
```

### Service failing?
```bash
# Check service logs
journalctl -u outage-auto-process.service -n 50

# Common issues:
# 1. Script not executable - run: chmod +x /path/to/auto-process-data.sh
# 2. Virtual environment not found - run install.sh first
# 3. Wrong paths in service file - edit /etc/systemd/system/outage-auto-process.service
```

### Check what files are being processed
```bash
# View the auto-process log
tail -f logs/auto-process.log
```

## Uninstallation

```bash
# Stop and disable the timer
sudo systemctl stop outage-auto-process.timer
sudo systemctl disable outage-auto-process.timer

# Remove the files
sudo rm /etc/systemd/system/outage-auto-process.service
sudo rm /etc/systemd/system/outage-auto-process.timer

# Reload systemd
sudo systemctl daemon-reload
```

## File Descriptions

- **outage-auto-process.service** - Systemd service that runs the auto-process script
- **outage-auto-process.timer** - Timer that triggers the service every 6 hours
- **install-systemd.sh** - Installation script that sets up everything automatically
- **README.md** - This file

## Notes

- The timer uses `Persistent=true`, so if the system was off when a run should have occurred, it will run as soon as the system boots
- The service runs as your user account (not root) to ensure proper permissions
- All output is logged to systemd journal (`journalctl`) and to `logs/auto-process.log`
- The timer will not run if there are no new files to process (script exits gracefully)
