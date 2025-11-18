#!/usr/bin/env python3
"""Capture screenshot of the ongoing outages section."""

from playwright.sync_api import sync_playwright
import sys

def capture_page():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Navigate to the page
        page.goto('http://localhost:5173/property/29', wait_until='networkidle')
        page.wait_for_timeout(2000)

        # Take full page screenshot
        page.screenshot(path='/tmp/property_29_full.png', full_page=True)
        print("✓ Full page screenshot saved to /tmp/property_29_full.png")

        # Try to capture just the ongoing outages section
        try:
            section = page.locator('.ongoing-outages-section').first
            if section.is_visible():
                section.screenshot(path='/tmp/ongoing_outages_section.png')
                print("✓ Section screenshot saved to /tmp/ongoing_outages_section.png")

                # Get the HTML of the section
                html = section.inner_html()
                with open('/tmp/ongoing_section.html', 'w') as f:
                    f.write(html)
                print("✓ Section HTML saved to /tmp/ongoing_section.html")
        except Exception as e:
            print(f"Note: Could not capture section: {e}")

        browser.close()

if __name__ == '__main__':
    try:
        capture_page()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
