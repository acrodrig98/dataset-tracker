# Dataset Tracker Utils

Utilities for managing and uploading dataset visualizations.

## Files

- **load_sheets.ipynb** - Jupyter notebook for analyzing dataset metadata and generating visualizations
- **upload_charts.py** - Python script to upload chart images to the web app

## Usage

### Step 1: Generate Charts

Run the Jupyter notebook to generate visualizations:

```bash
jupyter notebook load_sheets.ipynb
```

Run all cells in the notebook. This will:
- Load dataset metadata from multiple CSV files
- Generate pie charts and histograms
- Save charts as PNG files in this directory

### Step 2: Upload Charts to Web App

After generating the charts, upload them to the dataset tracker web app:

```bash
cd /Users/antoniorodriguez/Documents/dataset-tracker/utils
python upload_charts.py
```

Or run it directly:
```bash
./upload_charts.py
```

The script will:
- Find all `*distribution*.png` files in the current directory
- Upload them to the web app at `http://localhost:4000`
- Display upload progress and summary

### Step 3: View Charts

1. Open the dataset tracker web app: http://localhost:4000
2. Click the **"Data Statistics"** button
3. View your uploaded visualizations grouped by training phase!

## Configuration

Edit `upload_charts.py` to change settings:

```python
WEBAPP_URL = 'http://localhost:4000'  # Change if app runs on different port
```

## Troubleshooting

### "No chart PNG files found"
- Make sure you've run the Jupyter notebook first to generate charts
- Check that PNG files exist in the utils directory

### "Connection refused" error
- Make sure the web app is running: `python app.py`
- Check that the webapp URL and port are correct

### Charts not appearing on website
- Check the Flask console for errors
- Verify the database has been initialized: `db.create_all()`
