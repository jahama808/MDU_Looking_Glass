# Changelog

All notable changes to this project will be documented in this file.

## [1.0.1] - 2025-11-14

### Fixed
- **Critical Bug**: Fixed data retention issue in `process_property_outages_db.py` where networks without outages were incorrectly deleted during the `clear_old_data()` function
  - Previously, the `clear_old_data()` function (lines 347-351) was deleting ALL networks that didn't have any outages
  - This was treating networks without outages as "orphaned" and removing them
  - Networks without outages are critical for speedtest tracking and displaying "passing" networks
  - The bug caused the database to only retain ~2,000 networks with outages instead of all ~14,000 networks from the discovery file
  - Fixed by removing the erroneous deletion logic and adding explanatory comments

### Added
- Added `requests>=2.31.0` to `requirements.txt` for API download functionality
  - Required by `download_network_outages.py` and `download_eero_discovery.py` scripts
  - Missing dependency was causing download scripts to fail with `ModuleNotFoundError`

### Changed
- Updated all documentation files to use correct parameter names:
  - Changed `--connectivity-file` to `--outages-file` throughout documentation
  - Changed file naming from `wan_connectivity-*.csv` to `network_outages-*.csv`
  - Updated terminology from "WAN Connectivity" to "Network Outages"
- Updated documentation to reflect that database stores ALL networks from discovery file, not just those with outages
- Corrected default data retention period in documentation from 30 days to 7 days

### Documentation Updates
Files updated:
- `README.md` - Added version history, fixed parameter names, added `requests` to dependencies
- `QUICKSTART.md` - Updated parameter names and dependency list
- `PROCESSING_WORKFLOW.md` - Fixed rolling window default, added note about network retention
- `MASTER_README.md` - Updated parameter names and file references
- `DATABASE_README.md` - Updated parameter names and file references
- `UPDATE_DATA.md` - Updated parameter names and file references
- `PROJECT_SUMMARY.md` - Updated parameter names and file references
- `DEPLOYMENT_NOTES.md` - Updated parameter names and file references
- `WEB_APP_README.md` - Updated parameter names and file references
- `MIGRATION_SUMMARY.md` - Updated parameter names and file references
- `EMERGENCY_DEPLOYMENT.md` - Updated parameter names and file references
- `WINDOWS_AUTOMATION.md` - Updated parameter names and file references

### Database Impact
After applying this fix, the database will correctly contain:
- **All networks from the Eero Discovery file** (~14,000 networks)
- Networks WITH outages (with outage data)
- Networks WITHOUT outages (with speedtest data only)
- Accurate "passing" vs "failing" network counts for speedtest pages

### Upgrade Instructions
For existing installations:
1. Update the codebase to get the fixed `process_property_outages_db.py`
2. Update dependencies: `pip install -r requirements.txt`
3. Rebuild the database with the latest discovery file:
   ```bash
   source venv/bin/activate
   python process_property_outages_db.py \
     --outages-file <latest-outages-file> \
     --discovery-file <latest-discovery-file> \
     --mode rebuild
   ```

## [1.0.0] - 2025-01-07

### Initial Release
- Property and network outage tracking
- xPON shelf and 7x50 router monitoring
- Property-wide outage alerts
- Interactive dashboard with visualizations
- REST API for data access
- Automated data processing
- 7-day rolling window for outage data
