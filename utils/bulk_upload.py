import pandas as pd
import requests

# Your Render URL
BASE_URL = "https://dataset-tracker.onrender.com"  # Change this to your actual URL

# Create sample data
data = {
    'Dataset Name': [
        'CommonCrawl-2024',
        'Wikipedia-EN',
        'Code-Dataset-v2',
        'ArXiv-Papers',
        'Books-Corpus',
        'StackOverflow-QA',
        'Reddit-Comments',
        'GitHub-Issues',
        'Medical-Papers',
        'Legal-Documents'
    ],
    'Phase': [
        'Pretraining',
        'Pretraining',
        'Fine-tuning',
        'Fine-tuning',
        'Pretraining',
        'Fine-tuning',
        'Pretraining',
        'Fine-tuning',
        'Fine-tuning',
        'Fine-tuning'
    ],
    'Tokens': [
        '500B',
        '20B',
        '50B',
        '15B',
        '10B',
        '30B',
        '100B',
        '5B',
        '8B',
        '12B'
    ],
    'Parent Dataset': [
        '',
        '',
        '',
        '',
        '',
        '',
        '',
        'Code-Dataset-v2',
        '',
        ''
    ],
    'Status': [
        'Active',
        'Active',
        'Active',
        'Active',
        'Active',
        'Processing',
        'Active',
        'Active',
        'Processing',
        'Active'
    ],
    'Description': [
        'Web crawl data from 2024',
        'English Wikipedia dump',
        'GitHub code repositories',
        'Academic papers from ArXiv',
        'Collection of books',
        'Q&A from StackOverflow',
        'Reddit comment threads',
        'GitHub issue discussions',
        'Medical research papers',
        'Legal case documents'
    ]
}

# Create DataFrame and save as CSV
df = pd.DataFrame(data)
csv_filename = 'datasets_to_upload.csv'
df.to_csv(csv_filename, index=False)

print(f"✓ Created {csv_filename} with {len(df)} datasets")
print(f"\nYou can now:")
print(f"1. Open {csv_filename} and edit as needed")
print(f"2. Go to {BASE_URL}")
print(f"3. Click 'Upload CSV' and select {csv_filename}")
print(f"4. Review and approve the changes")

# Optional: If you want to upload directly via API
# Uncomment the code below:

# with open(csv_filename, 'rb') as f:
#     files = {'file': (csv_filename, f, 'text/csv')}
#     data = {'submitted_by': 'Script Upload'}
#     response = requests.post(f'{BASE_URL}/api/upload', files=files, data=data)
#     
#     if response.ok:
#         result = response.json()
#         print(f"\n✓ Upload successful!")
#         print(f"  Added: {result['summary']['added']}")
#         print(f"  Modified: {result['summary']['modified']}")
#         print(f"  Deleted: {result['summary']['deleted']}")
#         print(f"\nNow go to {BASE_URL} to review and approve changes!")
#     else:
#         print(f"✗ Upload failed: {response.text}")
