# Pushover Notification Setup

This guide explains how to configure Pushover notifications for the Network Outage Monitoring System.

## What is Pushover?

Pushover is a service that makes it easy to send real-time notifications to your phone, tablet, or desktop. The monitoring system sends notifications for:

- **Eero Data Downloads**: When data is downloaded from the Eero API
- **Data Processing**: When outage data is processed and the database is updated
- **Property-Wide Outages**: When properties experience outages affecting ≥75% of their networks

## Prerequisites

1. **Pushover Account**: Sign up at [pushover.net](https://pushover.net/)
   - Free for 30 days, then $5 one-time per platform (iOS/Android)

2. **Pushover Mobile App**: Install the app on your device(s)
   - iOS: [App Store](https://apps.apple.com/us/app/pushover-notifications/id506088175)
   - Android: [Google Play](https://play.google.com/store/apps/details?id=net.superblock.pushover)

## Setup Instructions

### Step 1: Get Your User Key

1. Log in to [pushover.net](https://pushover.net/)
2. Your **User Key** is displayed on the dashboard
3. It looks like: `uQiRzpo4DXghDmr9QzzfQu27cmVRsG`

### Step 2: Create an Application

1. Go to [Create an Application/API Token](https://pushover.net/apps/build)
2. Fill in the application details:
   - **Name**: Network Outage Monitor (or any name you prefer)
   - **Type**: Application
   - **Description**: Monitors network outages and sends alerts
   - **URL**: (optional)
   - **Icon**: (optional - upload a custom icon)
3. Click **Create Application**
4. You'll receive an **API Token/Key**
5. It looks like: `azGDORePK8gMaC0QOYAMyEEuzJnyUi`

### Step 3: Configure Environment Variables

Set the following environment variables on your system:

#### On Linux/macOS:

Add to your `~/.bashrc`, `~/.zshrc`, or `~/.bash_profile`:

```bash
export PUSHOVER_USER_KEY="your_user_key_here"
export PUSHOVER_API_TOKEN="your_api_token_here"
```

Then reload your shell:
```bash
source ~/.bashrc  # or ~/.zshrc
```

#### On Windows (PowerShell):

```powershell
$env:PUSHOVER_USER_KEY = "your_user_key_here"
$env:PUSHOVER_API_TOKEN = "your_api_token_here"
```

For permanent setup on Windows:
```powershell
[System.Environment]::SetEnvironmentVariable('PUSHOVER_USER_KEY', 'your_user_key_here', 'User')
[System.Environment]::SetEnvironmentVariable('PUSHOVER_API_TOKEN', 'your_api_token_here', 'User')
```

#### Using a .env file (Alternative):

Create a `.env` file in the project root:

```bash
PUSHOVER_USER_KEY=your_user_key_here
PUSHOVER_API_TOKEN=your_api_token_here
```

**Note**: If using a `.env` file, you'll need to load it in your scripts using `python-dotenv`:
```bash
pip install python-dotenv
```

### Step 4: Install Python Dependencies

The Pushover notifier uses the `requests` library, which is already included in the requirements.

Install the required Python packages:

```bash
pip install -r requirements.txt
```

Or if you're using a virtual environment:

```bash
source venv/bin/activate  # Activate virtual environment
pip install -r requirements.txt
```

### Step 5: Test the Configuration

Run the test script to verify your setup:

```bash
python pushover_notifier.py
```

You should receive a test notification on your device!

## Notification Types

### 1. Eero Data Download Notifications

**When**: Data is being downloaded from Eero API
**Priority**: Normal (0)
**Sound**: pushover (default)

Examples:
- "Eero Data Download Started" - When download begins
- "Eero Data Download Complete" - When download finishes successfully
- "Eero Download Failed" - When download encounters an error (Priority: High)

### 2. Data Processing Notifications

**When**: Network outage data is being processed
**Priority**: Normal (0)
**Sound**: pushover (default) / cashregister (success)

Examples:
- "Data Processing Started" - When processing begins
- "Data Processing Complete" - When processing finishes with statistics
- "Data Processing Failed" - When processing encounters an error (Priority: High)

### 3. Property-Wide Outage Alerts

**When**: Properties have ≥75% of networks experiencing outages
**Priority**: High (1)
**Sound**: siren

Example:
```
Property-Wide Outage Alert

Detected 2 property-wide outages at 2025-11-17 14:30:15

1. Grand Wailea Resort (Maui)
   45/50 networks down (90.0%)

2. Hilton Hawaiian Village (Oahu)
   38/48 networks down (79.2%)
```

## Customizing Notifications

You can customize notifications by modifying the `pushover_notifier.py` file:

### Change Notification Sounds

Available sounds:
- pushover (default)
- bike, bugle, cashregister, classical, cosmic
- falling, gamelan, incoming, intermission
- magic, mechanical, pianobar, siren
- spacealarm, tugboat, alien, climb
- persistent, echo, updown, vibrate, none

Example:
```python
notifier.send_notification(
    message="Custom message",
    title="Custom Title",
    sound="cosmic"  # Change sound
)
```

### Change Priority Levels

Priority levels:
- `-2`: Lowest priority (no notification/alert)
- `-1`: Low priority (no sound/vibration)
- `0`: Normal priority (default)
- `1`: High priority (bypass quiet hours)
- `2`: Emergency priority (requires acknowledgment)

## Troubleshooting

### Notifications Not Received

1. **Check environment variables**:
   ```bash
   echo $PUSHOVER_USER_KEY
   echo $PUSHOVER_API_TOKEN
   ```

2. **Verify credentials** at [pushover.net](https://pushover.net/)

3. **Check app installation**: Make sure the Pushover app is installed on your device

4. **Test directly**:
   ```bash
   python -c "from pushover_notifier import PushoverNotifier; n = PushoverNotifier(); n.send_notification('Test', 'Test')"
   ```

### "Pushover credentials not configured" Warning

This means the environment variables are not set. The scripts will continue to run but won't send notifications.

### Network/Firewall Issues

Ensure your system can reach:
- `api.pushover.net` (HTTPS/443)

## Disable Notifications

To temporarily disable notifications without removing credentials:

1. **Comment out notification calls** in the scripts
2. **Unset environment variables**:
   ```bash
   unset PUSHOVER_USER_KEY
   unset PUSHOVER_API_TOKEN
   ```

The scripts will detect missing credentials and continue without sending notifications.

## Security Best Practices

1. **Never commit credentials** to version control
2. **Add `.env` to `.gitignore`**
3. **Use environment variables** instead of hardcoding keys
4. **Rotate API tokens** periodically
5. **Limit application access** on the Pushover dashboard

## API Limits

Pushover has rate limits:
- **Free tier**: 10,000 messages per month
- **Default limit**: 10,000 messages per month per application

This should be more than sufficient for typical monitoring operations.

## Support

- **Pushover Documentation**: [pushover.net/api](https://pushover.net/api)
- **Pushover API Reference**: [pushover.net/api](https://pushover.net/api)
- **Issue Tracker**: Report issues with the monitoring system integration

## Example Workflow

1. **Automated Download** (cron job runs every 6 hours):
   ```bash
   python download_network_outages.py
   ```
   → Sends notification when download starts and completes

2. **Automated Processing** (cron job runs after download):
   ```bash
   python process_property_outages_db.py --outages-file inputs/network_outages-2025-11-17.csv
   ```
   → Sends notification when processing completes and if property-wide outages detected

3. **You Receive Alerts**:
   - Download complete: Check phone
   - Processing complete: Review statistics
   - Property-wide outage: Immediate response required!

## Additional Configuration Options

### Quiet Hours

Configure quiet hours in the Pushover app to suppress non-emergency notifications during specific times.

### Delivery Groups

Create delivery groups on Pushover to send notifications to multiple devices or users.

### Custom Sounds per Device

Configure different notification sounds on each device through the Pushover app settings.

---

**Last Updated**: 2025-11-17
