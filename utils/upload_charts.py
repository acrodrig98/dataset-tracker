#!/usr/bin/env python3
"""
Upload Chart Images to Dataset Tracker Web App

This script uploads PNG chart files from the current directory to the
dataset tracker web application.

Usage:
    python upload_charts.py

Configuration:
    - Update WEBAPP_URL if your app runs on a different port
    - Charts are uploaded from the current directory (utils/)
"""

import requests
import os
import glob

# Configuration
WEBAPP_URL = 'http://localhost:4000'  # Update if your app runs on a different port
CHARTS_DIR = os.path.dirname(os.path.abspath(__file__))  # Current directory
UPLOADED_BY = 'Jupyter Notebook'

def upload_chart(filepath, name, chart_type, phase=''):
    """Upload a chart to the web app"""
    print(f'Uploading {os.path.basename(filepath)}...', end=' ')

    with open(filepath, 'rb') as f:
        files = {'file': (os.path.basename(filepath), f, 'image/png')}
        data = {
            'name': name,
            'chart_type': chart_type,
            'phase': phase,
            'uploaded_by': UPLOADED_BY
        }

        try:
            response = requests.post(f'{WEBAPP_URL}/api/charts/upload', files=files, data=data)
            if response.status_code == 200:
                print('✓ Success')
                return True
            else:
                print(f'✗ Failed: {response.text}')
                return False
        except Exception as e:
            print(f'✗ Error: {e}')
            return False

def parse_filename(filename):
    """Parse phase and chart type from filename"""
    # Example: BMoE-Phase1_domain_distribution_count.png
    base = filename.replace('.png', '')
    parts = base.split('_')

    # Extract phase (everything before first underscore)
    phase = parts[0] if parts else 'Unknown'

    # Determine chart type
    if 'distribution' in base and 'count' in base:
        chart_type = 'pie'
        name = f'{phase} - Domain Distribution (Count)'
    elif 'histogram' in base or 'distribution' in base:
        chart_type = 'histogram'
        name = f'{phase} - Token Distribution'
    else:
        chart_type = 'unknown'
        name = f'{phase} - Chart'

    return name, chart_type, phase

def main():
    """Main function to upload all chart PNG files"""
    print(f'Dataset Tracker - Chart Uploader')
    print(f'=' * 50)
    print(f'Web App URL: {WEBAPP_URL}')
    print(f'Charts Directory: {CHARTS_DIR}')
    print(f'=' * 50)
    print()

    # Find all PNG files
    pattern = os.path.join(CHARTS_DIR, '*distribution*.png')
    png_files = glob.glob(pattern)

    if not png_files:
        print('No chart PNG files found in the current directory.')
        print(f'Looking for files matching: {pattern}')
        return

    print(f'Found {len(png_files)} chart files to upload:\n')

    uploaded_count = 0
    failed_count = 0

    for filepath in sorted(png_files):
        filename = os.path.basename(filepath)
        name, chart_type, phase = parse_filename(filename)

        if upload_chart(filepath, name, chart_type, phase):
            uploaded_count += 1
        else:
            failed_count += 1

    print()
    print(f'=' * 50)
    print(f'Upload Summary:')
    print(f'  ✓ Successfully uploaded: {uploaded_count}')
    print(f'  ✗ Failed: {failed_count}')
    print(f'  📊 Total: {len(png_files)}')
    print(f'=' * 50)
    print()
    print(f'View charts at: {WEBAPP_URL}')
    print('Click the "Data Statistics" button!')

if __name__ == '__main__':
    main()
