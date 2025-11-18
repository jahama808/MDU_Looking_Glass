#!/usr/bin/env python3
"""
Script for downloading network_outages files from Eero API.
Downloads files to ./inputs/ directory for later processing.
"""
import requests
import os
import sys
from datetime import datetime
from pushover_notifier import PushoverNotifier

# Configuration
EERO_API_TOKEN = '49925579|dofa12u9hkcopvr801gcqs7hge'
INPUTS_DIR = './inputs'
PROCESSED_DIR = './inputs_already_read'
DATABASE_PATH = './output/outages.db'

def get_network_outages_artifact():
    """Get the latest network_outages artifact_id from Eero API."""
    print("\n" + "="*80)
    print("STEP 1: Fetching available datasets from Eero API")
    print("="*80)

    # Get today's date for the start parameter
    today = datetime.now().strftime('%Y-%m-%d')
    url = f"https://api-user.e2ro.com/2.2/organizations/self/data_aggregation_jobs?start={today}T00:00:00Z"

    headers = {'X-User-Token': EERO_API_TOKEN}

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"✗ Error fetching datasets: {response.status_code}")
        print(response.text)
        return None

    data = response.json()
    jobs = data['data']['aggregation_jobs']

    print(f"✓ Found {len(jobs)} datasets")

    # Find network_outages
    for job in jobs:
        if job['dataset'] == 'network_outages' and job['status'] == 'completed':
            print(f"\n✓ Found network_outages dataset:")
            print(f"  Artifact ID: {job['artifact_id']}")
            print(f"  Scheduled: {job['scheduled_time']}")
            print(f"  Completed: {job['completed']}")
            return job['artifact_id']

    print("✗ network_outages dataset not found")
    return None


def get_download_url(artifact_id):
    """Get download URL for the artifact."""
    print("\n" + "="*80)
    print("STEP 2: Fetching download URL")
    print("="*80)

    url = f"https://api-user.e2ro.com/2.2/organizations/self/data_artifacts/{artifact_id}?download_link=true"
    headers = {'X-User-Token': EERO_API_TOKEN}

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"✗ Error fetching download URL: {response.status_code}")
        print(response.text)
        return None, None

    data = response.json()
    download_link = data['data']['download_link']
    expires = data['data']['download_link_expires']

    # Extract filename from the URL
    filename = download_link.split('/')[-1].split('?')[0]

    print(f"✓ Download URL obtained")
    print(f"  Filename: {filename}")
    print(f"  Link expires: {expires}")

    return download_link, filename


def download_file(download_url, filename):
    """Download the file to inputs directory."""
    print("\n" + "="*80)
    print("STEP 3: Downloading file")
    print("="*80)

    os.makedirs(INPUTS_DIR, exist_ok=True)
    filepath = os.path.join(INPUTS_DIR, filename)

    # Check if already downloaded
    if os.path.exists(filepath):
        print(f"⚠ File already exists in inputs: {filename}")
        return filepath

    print(f"  Downloading to: {filepath}")

    response = requests.get(download_url, stream=True)

    if response.status_code != 200:
        print(f"✗ Error downloading file: {response.status_code}")
        return None

    # Download with progress
    total_size = int(response.headers.get('content-length', 0))
    block_size = 8192
    downloaded = 0

    with open(filepath, 'wb') as f:
        for chunk in response.iter_content(chunk_size=block_size):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    print(f"\r  Progress: {percent:.1f}%", end='', flush=True)

    print(f"\n✓ File downloaded successfully")
    print(f"  Size: {os.path.getsize(filepath):,} bytes")

    return filepath


def check_already_downloaded(filename):
    """Check if file has already been downloaded."""
    print("\n" + "="*80)
    print("STEP 4: Checking if already downloaded")
    print("="*80)

    # Check in inputs_already_read directory and subdirectories
    if os.path.exists(PROCESSED_DIR):
        for root, dirs, files in os.walk(PROCESSED_DIR):
            if filename in files:
                processed_path = os.path.join(root, filename)
                print(f"⚠ File already downloaded and processed: {processed_path}")
                return True

    print(f"✓ File is new and ready for processing")
    return False


def main():
    print("\n" + "="*80)
    print("EERO API NETWORK OUTAGES DOWNLOAD")
    print("="*80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Initialize Pushover notifier
    notifier = PushoverNotifier()

    # Step 1: Get artifact_id
    artifact_id = get_network_outages_artifact()
    if not artifact_id:
        print("\n✗ Failed to get artifact_id")
        notifier.notify_eero_download_error("Failed to get artifact_id from Eero API")
        sys.exit(1)

    # Send notification that download is starting
    notifier.notify_eero_download_start(dataset_id=artifact_id)

    # Step 2: Get download URL
    download_url, filename = get_download_url(artifact_id)
    if not download_url:
        print("\n✗ Failed to get download URL")
        notifier.notify_eero_download_error("Failed to get download URL")
        sys.exit(1)

    # Step 3: Download file
    filepath = download_file(download_url, filename)
    if not filepath:
        print("\n✗ Failed to download file")
        notifier.notify_eero_download_error("Failed to download file from URL")
        sys.exit(1)

    # Step 4: Check if already downloaded
    if check_already_downloaded(filename):
        print("\n" + "="*80)
        print("FILE ALREADY DOWNLOADED - SKIPPING")
        print("="*80)
        print(f"\nDeleting duplicate download: {filepath}")
        os.remove(filepath)
        print("✓ Cleanup complete")
        sys.exit(0)

    # Send success notification with file details
    file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
    notifier.notify_eero_download_complete(filename, file_size=f"{file_size_mb:.2f} MB")

    print("\n" + "="*80)
    print("SUCCESS - DOWNLOAD COMPLETED")
    print("="*80)
    print(f"Downloaded file: {filename}")
    print(f"Location: {filepath}")
    print(f"Ready for processing by automated job")
    print(f"\nEnd time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✗ Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
