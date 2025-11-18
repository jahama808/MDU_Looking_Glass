"""
Pushover notification module for network outage monitoring system.

This module provides functions to send Pushover notifications for:
- Eero data downloads
- Data processing completion
- Property-wide outages detected
"""

import os
import requests
from datetime import datetime
from pathlib import Path

# Try to load .env file if it exists
try:
    from dotenv import load_dotenv
    # Look for .env file in the script's directory
    script_dir = Path(__file__).parent.resolve()
    env_path = script_dir / '.env'

    # Also check current working directory
    cwd_env_path = Path.cwd() / '.env'

    if env_path.exists():
        load_dotenv(env_path)
    elif cwd_env_path.exists():
        load_dotenv(cwd_env_path)
except ImportError:
    # python-dotenv not installed, will fall back to environment variables
    pass


class PushoverNotifier:
    """Handle Pushover notifications for the outage monitoring system."""

    def __init__(self, user_key=None, api_token=None):
        """
        Initialize Pushover notifier.

        Args:
            user_key: Pushover user key (defaults to PUSHOVER_USER_KEY env var)
            api_token: Pushover API token (defaults to PUSHOVER_API_TOKEN env var)
        """
        self.user_key = user_key or os.getenv('PUSHOVER_USER_KEY')
        self.api_token = api_token or os.getenv('PUSHOVER_API_TOKEN')
        self.api_url = "https://api.pushover.net/1/messages.json"

        if not self.user_key or not self.api_token:
            print("Warning: Pushover credentials not configured. Notifications will be disabled.")
            print("Set PUSHOVER_USER_KEY and PUSHOVER_API_TOKEN environment variables.")
            self.enabled = False
        else:
            self.enabled = True

    def send_notification(self, message, title=None, priority=0, sound=None):
        """
        Send a Pushover notification.

        Args:
            message: The notification message
            title: Optional title for the notification
            priority: Priority level (-2 to 2, default 0)
            sound: Optional sound name

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            print(f"Pushover disabled. Would have sent: {title or 'Notification'}: {message}")
            return False

        try:
            payload = {
                "token": self.api_token,
                "user": self.user_key,
                "message": message,
            }

            if title:
                payload["title"] = title
            if priority != 0:
                payload["priority"] = priority
            if sound:
                payload["sound"] = sound

            response = requests.post(self.api_url, data=payload, timeout=10)

            if response.status_code != 200:
                error_msg = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                print(f"Pushover API error: {error_msg}")
                return False

            print(f"Pushover notification sent: {title or 'Notification'}")
            return True
        except Exception as e:
            print(f"Failed to send Pushover notification: {e}")
            return False

    def notify_eero_download_start(self, dataset_id=None):
        """
        Notify when eero data download starts.

        Args:
            dataset_id: Optional dataset identifier
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message = f"Starting download of network outage data from Eero API at {timestamp}"
        if dataset_id:
            message += f"\nDataset ID: {dataset_id}"

        return self.send_notification(
            message=message,
            title="Eero Data Download Started",
            priority=0,
            sound="climb"
        )

    def notify_eero_download_complete(self, filename, file_size=None):
        """
        Notify when eero data download completes.

        Args:
            filename: Name of the downloaded file
            file_size: Optional file size information
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message = f"Successfully downloaded: {filename}\nCompleted at: {timestamp}"
        if file_size:
            message += f"\nFile size: {file_size}"

        return self.send_notification(
            message=message,
            title="Eero Data Download Complete",
            priority=0,
            sound="climb"
        )

    def notify_eero_download_error(self, error_message):
        """
        Notify when eero data download fails.

        Args:
            error_message: Description of the error
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message = f"Failed to download data from Eero API\nTime: {timestamp}\nError: {error_message}"

        return self.send_notification(
            message=message,
            title="Eero Download Failed",
            priority=1,
            sound="siren"
        )

    def notify_processing_start(self, filename, mode="append"):
        """
        Notify when data processing starts.

        Args:
            filename: Name of file being processed
            mode: Processing mode (append or rebuild)
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message = f"Started processing network outage data\nFile: {filename}\nMode: {mode}\nTime: {timestamp}"

        return self.send_notification(
            message=message,
            title="Data Processing Started",
            priority=0,
            sound="climb"
        )

    def notify_processing_complete(self, filename, stats=None):
        """
        Notify when data processing completes.

        Args:
            filename: Name of processed file
            stats: Optional dictionary with processing statistics
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message = f"Successfully processed: {filename}\nCompleted at: {timestamp}"

        if stats:
            if 'properties' in stats:
                message += f"\n\nProperties: {stats['properties']}"
            if 'networks' in stats:
                message += f"\nNetworks: {stats['networks']}"
            if 'outages' in stats:
                message += f"\nTotal outages: {stats['outages']}"
            if 'processing_time' in stats:
                message += f"\nProcessing time: {stats['processing_time']}"

        return self.send_notification(
            message=message,
            title="Data Processing Complete",
            priority=0,
            sound="climb"
        )

    def notify_processing_error(self, filename, error_message):
        """
        Notify when data processing fails.

        Args:
            filename: Name of file that failed to process
            error_message: Description of the error
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message = f"Failed to process: {filename}\nTime: {timestamp}\nError: {error_message}"

        return self.send_notification(
            message=message,
            title="Data Processing Failed",
            priority=1,
            sound="siren"
        )

    def notify_property_wide_outages(self, properties):
        """
        Notify when property-wide outages are detected.

        Args:
            properties: List of property dictionaries with outage information
        """
        if not properties:
            return False

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        count = len(properties)

        message = f"Detected {count} property-wide outage{'s' if count != 1 else ''} at {timestamp}\n\n"

        # Add details for each property (limit to first 5 to keep message reasonable)
        for i, prop in enumerate(properties[:5]):
            property_name = prop.get('property_name', 'Unknown')
            networks_down = prop.get('networks_down', 0)
            total_networks = prop.get('total_networks', 0)
            percentage = prop.get('outage_percentage', 0)
            island = prop.get('island', '')

            message += f"{i+1}. {property_name}"
            if island:
                message += f" ({island})"
            message += f"\n   {networks_down}/{total_networks} networks down ({percentage:.1f}%)\n"

        if count > 5:
            message += f"\n... and {count - 5} more properties"

        return self.send_notification(
            message=message,
            title=f"Property-Wide Outage Alert",
            priority=1,  # High priority
            sound="siren"
        )

    def notify_property_wide_outage_resolved(self, property_name):
        """
        Notify when a property-wide outage is resolved.

        Args:
            property_name: Name of the property
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        message = f"Property-wide outage resolved for:\n{property_name}\n\nResolved at: {timestamp}"

        return self.send_notification(
            message=message,
            title="Outage Resolved",
            priority=0,
            sound="climb"
        )


# Convenience function for quick notifications
def send_quick_notification(message, title="Network Monitor", priority=0):
    """
    Send a quick notification without creating a PushoverNotifier instance.

    Args:
        message: The notification message
        title: Notification title
        priority: Priority level (-2 to 2)

    Returns:
        True if sent successfully, False otherwise
    """
    notifier = PushoverNotifier()
    return notifier.send_notification(message, title=title, priority=priority)


if __name__ == "__main__":
    # Test the notifier
    print("Testing Pushover Notifier...")
    notifier = PushoverNotifier()

    if notifier.enabled:
        print("Sending test notification...")
        notifier.send_notification(
            "This is a test notification from the Network Outage Monitoring System.",
            title="Test Notification"
        )
    else:
        print("Pushover not configured. Set PUSHOVER_USER_KEY and PUSHOVER_API_TOKEN environment variables.")
