# Pushover Notifications - Quick Start

## Overview

Pushover notifications have been integrated into the network outage monitoring system. You'll receive real-time alerts on your phone for:

- **Eero Data Downloads** (start, complete, or error)
- **Data Processing** (start, complete, or error)
- **Property-Wide Outages** (when ≥75% of networks are down)

## Quick Setup (5 minutes)

1. **Sign up for Pushover**: Visit [pushover.net](https://pushover.net/)
   - Free 30-day trial, then $5 one-time per platform

2. **Get your credentials**:
   - **User Key**: Shown on your dashboard after login
   - **API Token**: Create an app at [pushover.net/apps/build](https://pushover.net/apps/build)

3. **Set environment variables**:
   ```bash
   export PUSHOVER_USER_KEY="your_user_key_here"
   export PUSHOVER_API_TOKEN="your_api_token_here"
   ```

4. **Test it**:
   ```bash
   python3 pushover_notifier.py
   ```

That's it! Your scripts will now send notifications.

## Files Modified

- `pushover_notifier.py` - New notification module
- `download_network_outages.py` - Added download notifications
- `process_property_outages_db.py` - Added processing & outage notifications
- `requirements.txt` - No new dependencies (uses existing `requests`)

## Running Without Pushover

**The system works fine without Pushover configured!**

If credentials aren't set, you'll see:
```
Warning: Pushover credentials not configured. Notifications will be disabled.
```

All scripts continue to work normally - they just won't send notifications.

## Full Documentation

See [PUSHOVER_SETUP.md](PUSHOVER_SETUP.md) for:
- Detailed setup instructions
- Customization options
- Troubleshooting guide
- API limits and best practices

## Example Notifications

**Download Complete:**
```
Eero Data Download Complete

Successfully downloaded: network_outages-2025-11-17.csv
Completed at: 2025-11-17 08:30:15
File size: 2.45 MB
```

**Processing Complete:**
```
Data Processing Complete

Successfully processed: network_outages-2025-11-17.csv
Completed at: 2025-11-17 08:35:22

Properties: 156
Networks: 1,234
Total outages: 342
Processing time: 4m 38s
```

**Property-Wide Outage Alert:**
```
Property-Wide Outage Alert

Detected 2 property-wide outages at 2025-11-17 14:30:15

1. Grand Wailea Resort (Maui)
   45/50 networks down (90.0%)

2. Hilton Hawaiian Village (Oahu)
   38/48 networks down (79.2%)
```

## Disable Notifications

To temporarily disable:
```bash
unset PUSHOVER_USER_KEY
unset PUSHOVER_API_TOKEN
```

---

**Questions?** See [PUSHOVER_SETUP.md](PUSHOVER_SETUP.md) for complete documentation.
