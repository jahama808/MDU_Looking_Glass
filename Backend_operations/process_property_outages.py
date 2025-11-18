#!/usr/bin/env python3
"""
Property Outage Analysis Script

This script processes WAN connectivity outage data and Eero discovery details
to generate per-property outage reports with hourly summaries.

Usage:
    python process_property_outages.py --connectivity-file <path> --discovery-file <path> [--output-dir <path>]

Example:
    python process_property_outages.py \\
        --connectivity-file wan_connectivity-2025-11-06.csv \\
        --discovery-file Eero_Discovery_Details_-_2025-11-04_081045.csv \\
        --output-dir ./property_outages
"""

import pandas as pd
import argparse
import os
import sys
from datetime import datetime
from pathlib import Path


def validate_file(filepath, file_type):
    """Validate that the file exists and is readable."""
    if not os.path.exists(filepath):
        print(f"Error: {file_type} file not found: {filepath}")
        sys.exit(1)
    
    if not os.path.isfile(filepath):
        print(f"Error: {file_type} path is not a file: {filepath}")
        sys.exit(1)
    
    try:
        with open(filepath, 'r') as f:
            pass
    except Exception as e:
        print(f"Error: Cannot read {file_type} file: {e}")
        sys.exit(1)


def process_outages(connectivity_file, discovery_file, output_dir):
    """Process the outage data and generate reports."""
    
    print(f"\n{'='*60}")
    print("PROPERTY OUTAGE ANALYSIS")
    print(f"{'='*60}\n")
    
    # Read the source files
    print(f"Reading connectivity file: {connectivity_file}")
    try:
        wan_connectivity = pd.read_csv(connectivity_file)
        print(f"  ✓ Loaded {len(wan_connectivity):,} WAN connectivity records")
    except Exception as e:
        print(f"  ✗ Error reading connectivity file: {e}")
        sys.exit(1)
    
    print(f"\nReading discovery file: {discovery_file}")
    try:
        eero_details = pd.read_csv(discovery_file)
        print(f"  ✓ Loaded {len(eero_details):,} Eero discovery records")
    except Exception as e:
        print(f"  ✗ Error reading discovery file: {e}")
        sys.exit(1)
    
    # Validate required columns
    required_wan_cols = ['network_id', 'wan_down_start', 'wan_down_end', 'duration', 'reason']
    required_eero_cols = ['MDU Name', 'Eero Network ID', 'Street Address', 'Subloc', 'Customer Name']
    
    missing_wan_cols = [col for col in required_wan_cols if col not in wan_connectivity.columns]
    missing_eero_cols = [col for col in required_eero_cols if col not in eero_details.columns]
    
    if missing_wan_cols:
        print(f"\n✗ Error: Connectivity file missing required columns: {missing_wan_cols}")
        sys.exit(1)
    
    if missing_eero_cols:
        print(f"\n✗ Error: Discovery file missing required columns: {missing_eero_cols}")
        sys.exit(1)
    
    # Convert timestamps to datetime
    print("\nProcessing timestamps...")
    try:
        wan_connectivity['wan_down_start'] = pd.to_datetime(wan_connectivity['wan_down_start'])
        wan_connectivity['wan_down_end'] = pd.to_datetime(wan_connectivity['wan_down_end'])
        print("  ✓ Timestamps converted")
    except Exception as e:
        print(f"  ✗ Error converting timestamps: {e}")
        sys.exit(1)
    
    # Extract hour from start time for grouping
    wan_connectivity['outage_hour'] = wan_connectivity['wan_down_start'].dt.floor('h')
    
    # Get unique properties
    properties = eero_details['MDU Name'].dropna().unique()
    print(f"\n✓ Found {len(properties)} unique properties")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    print(f"✓ Output directory: {output_dir}")
    
    # Process each property
    print(f"\n{'='*60}")
    print("PROCESSING PROPERTIES")
    print(f"{'='*60}\n")
    
    properties_with_outages = 0
    properties_without_outages = 0
    total_outages_processed = 0
    
    for idx, property_name in enumerate(sorted(properties), 1):
        print(f"[{idx}/{len(properties)}] {property_name}")
        
        # Get all networks for this property
        property_networks = eero_details[eero_details['MDU Name'] == property_name]
        network_ids = property_networks['Eero Network ID'].dropna().unique()
        
        print(f"  Networks: {len(network_ids)}")
        
        # Get all outages for these networks
        property_outages = wan_connectivity[wan_connectivity['network_id'].isin(network_ids)]
        
        print(f"  Outages: {len(property_outages)}")
        
        if len(property_outages) == 0:
            print(f"  Status: Skipped (no outages)\n")
            properties_without_outages += 1
            continue
        
        properties_with_outages += 1
        total_outages_processed += len(property_outages)
        
        # Count outages per network per hour
        hourly_outages = property_outages.groupby(['network_id', 'outage_hour']).size().reset_index(name='outage_count')
        
        # Create aggregated outage counts (sum across all networks per hour)
        aggregated_outages = property_outages.groupby('outage_hour').size().reset_index(name='total_outage_count')
        aggregated_outages = aggregated_outages.sort_values('outage_hour')
        
        # Merge with network details
        network_info = property_networks[['Eero Network ID', 'Street Address', 'Subloc', 'Customer Name']].drop_duplicates()
        hourly_outages = hourly_outages.merge(
            network_info, 
            left_on='network_id', 
            right_on='Eero Network ID', 
            how='left'
        )
        
        # Sort by hour and network
        hourly_outages = hourly_outages.sort_values(['outage_hour', 'network_id'])
        
        # Create summary with total outages per network
        network_summary = property_outages.groupby('network_id').size().reset_index(name='total_outages')
        network_summary = network_summary.merge(
            network_info,
            left_on='network_id',
            right_on='Eero Network ID',
            how='left'
        )
        network_summary = network_summary.sort_values('total_outages', ascending=False)
        
        # Create filename (sanitize property name)
        safe_filename = "".join(c for c in property_name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_filename = safe_filename.replace(' ', '_')
        output_file = os.path.join(output_dir, f"{safe_filename}_outages.csv")
        
        # Combine summary and hourly data
        with open(output_file, 'w') as f:
            f.write(f"Property: {property_name}\n")
            f.write(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Networks: {len(network_ids)}\n")
            f.write(f"Total Outages: {len(property_outages)}\n")
            f.write("\n")
            
            f.write("=== NETWORK SUMMARY (Total Outages) ===\n")
            network_summary.to_csv(f, index=False)
            
            f.write("\n\n=== AGGREGATED OUTAGE COUNTS (All Networks Combined by Hour) ===\n")
            aggregated_outages.to_csv(f, index=False)
            
            f.write("\n\n=== HOURLY OUTAGE COUNTS (Per Network) ===\n")
            hourly_outages.to_csv(f, index=False)
        
        print(f"  Status: ✓ Created {safe_filename}_outages.csv\n")
    
    # Create an index file
    index_file = os.path.join(output_dir, "00_INDEX.txt")
    with open(index_file, 'w') as f:
        f.write("PROPERTY OUTAGE REPORTS\n")
        f.write("=" * 60 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Properties: {len(properties)}\n")
        f.write(f"Properties with Outages: {properties_with_outages}\n")
        f.write(f"Properties without Outages: {properties_without_outages}\n")
        f.write(f"Total Outages Processed: {total_outages_processed:,}\n")
        f.write("=" * 60 + "\n\n")
        
        for property_name in sorted(properties):
            safe_filename = "".join(c for c in property_name if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_filename = safe_filename.replace(' ', '_')
            f.write(f"{property_name}: {safe_filename}_outages.csv\n")
    
    # Print summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Total Properties: {len(properties)}")
    print(f"Properties with Outages: {properties_with_outages}")
    print(f"Properties without Outages: {properties_without_outages}")
    print(f"Total Outages Processed: {total_outages_processed:,}")
    print(f"Output Directory: {output_dir}")
    print(f"Index File: {index_file}")
    print(f"{'='*60}\n")
    
    return properties_with_outages


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Process property outages from WAN connectivity and Eero discovery data.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --connectivity-file wan_connectivity.csv --discovery-file eero_discovery.csv
  
  %(prog)s \\
    --connectivity-file /path/to/wan_connectivity-2025-11-06.csv \\
    --discovery-file /path/to/Eero_Discovery_Details.csv \\
    --output-dir ./my_reports
        """
    )
    
    parser.add_argument(
        '--connectivity-file',
        required=True,
        help='Path to the WAN connectivity CSV file (contains outage data)'
    )
    
    parser.add_argument(
        '--discovery-file',
        required=True,
        help='Path to the Eero discovery details CSV file (contains property and network data)'
    )
    
    parser.add_argument(
        '--output-dir',
        default='./output/property-files',
        help='Directory where output files will be saved (default: ./output/property-files)'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 1.0.0'
    )
    
    args = parser.parse_args()
    
    # Validate input files
    validate_file(args.connectivity_file, "Connectivity")
    validate_file(args.discovery_file, "Discovery")
    
    # Process the data
    try:
        num_reports = process_outages(
            args.connectivity_file,
            args.discovery_file,
            args.output_dir
        )
        
        print(f"✓ SUCCESS: Generated {num_reports} property outage reports")
        sys.exit(0)
        
    except KeyboardInterrupt:
        print("\n\n✗ Process interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
