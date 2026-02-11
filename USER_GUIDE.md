# Dataset Tracker - User Guide

A collaborative dataset management system with approval workflows and version control.

## Table of Contents
- [Overview](#overview)
- [Downloading Data](#downloading-data)
- [Uploading Data](#uploading-data)
- [Viewing Pending Changes](#viewing-pending-changes)
- [Approving Changes (Admin Only)](#approving-changes-admin-only)
- [Data Statistics](#data-statistics)
- [CSV Format](#csv-format)
- [Troubleshooting](#troubleshooting)

---

## Overview

The Dataset Tracker allows teams to collaboratively manage dataset metadata through a web interface. All changes go through a review process before being applied to the database.

**Key Features:**
- 📥 **Download** the current dataset as CSV
- 📤 **Upload** new data or modifications via CSV
- 👁️ **Review** pending changes before they go live
- ✅ **Approve/Reject** changes (admin only)
- 📊 **Data Statistics** - Interactive charts and visualizations
- 📜 **Audit log** of all changes

---

## Downloading Data

### How to Download

1. Open the Dataset Tracker web application
2. Click the **"Download CSV"** button
3. A CSV file will download with the current timestamp: `datasets_YYYYMMDD_HHMMSS.csv`

### What You Get

The downloaded CSV contains all current datasets with these columns:
- **Dataset ID** - Unique identifier (e.g., DS-000001)
- **Data Name Split** - Dataset name/split
- **Domain** - Dataset domain/category
- **Gemma3 Token Count** - Number of tokens
- **Epochs** - Training epochs
- **Desired Token Count** - Target token count
- **Training Stage** - Training phase/stage
- **Link** - URL to dataset
- **IBM Datapath** - Path to dataset location

---

## Uploading Data

### Step 1: Prepare Your CSV

You can either:
- **Modify the downloaded CSV** - Make changes to existing data
- **Create a new CSV** - Add new datasets (see [CSV Format](#csv-format))

### Step 2: Upload the File

1. Click the **"Upload CSV"** button
2. Select your CSV file
3. Choose upload mode:
   - **Click OK** → Add new data (keeps existing datasets)
   - **Click Cancel** → Replace all data (removes datasets not in your CSV)
4. Enter your name when prompted

### Step 3: Review the Preview

After uploading, you'll see a preview showing:
- ✅ **Additions** - New datasets being added (green)
- ⚠️ **Modifications** - Changes to existing datasets (yellow)
- ❌ **Deletions** - Datasets being removed (red, only in replace mode)

**Note:** Your changes are NOT yet applied! They are saved as "pending changes" awaiting approval.

---

## Viewing Pending Changes

### Check What's Waiting for Approval

1. Click **"View Pending Changes"**
2. Review all pending additions, modifications, and deletions
3. You can see:
   - Who submitted each change
   - When it was submitted
   - Exactly what will change

**Note:** Only approved changes appear in the main dataset view and downloads.

---

## Approving Changes (Admin Only)

### For Administrators

If you have approval permissions:

1. Click **"View Pending Changes"**
2. Review the proposed changes carefully
3. Click one of:
   - **"✓ Approve All Changes"** - Apply changes to the database
   - **"✗ Reject All Changes"** - Discard the pending changes
4. Enter your name when prompted
5. Confirm the action

### Authorization

Only designated administrators can approve or reject changes. If you try to approve without permission, you'll receive an "Unauthorized" error.

---

## Data Statistics

### Viewing Visualizations

The Data Statistics tab provides interactive charts and visualizations showing:
- Domain distribution across different training phases
- Token count distributions
- Dataset composition analysis

**How to Access:**

1. Click the **"Data Statistics"** button (purple button with chart icon) on the main page
2. Browse through charts organized by training phase:
   - BMoE-Phase1, BMoE-Phase2
   - SMoE-Phase1, SMoE-Phase2
   - SMoE-Midtrain, SMoE-SFT
   - And more...

### Understanding the Charts

**Pie Charts:**
- Show the distribution of datasets across different domains
- Larger slices indicate domains with more datasets or higher token counts
- "Other" category groups smaller domains for clarity

**Histograms:**
- Display token count distributions within each domain
- Help identify patterns and outliers in dataset sizes
- Include mean and median values for reference

### For Administrators: Uploading Charts

If you have access to the Jupyter notebook and want to update the visualizations:

**Step 1: Generate Charts**
```bash
jupyter notebook utils/load_sheets.ipynb
# Run all cells to generate PNG charts
```

**Step 2: Upload to Web App**
```bash
cd utils
python upload_charts.py
```

**Step 3: Verify**
- Refresh the Data Statistics page
- New charts will appear automatically
- Old charts with the same filename are updated

**Note:** Chart uploads require the web application to be running and accessible at `http://localhost:4000`.

---

## CSV Format

### Required Columns

Your CSV must include these columns (either format works):

#### Format 1: Display Names (with spaces)
```csv
Dataset ID,Data Name Split,Domain,Gemma3 Token Count,Epochs,Desired Token Count,Training Stage,Link,IBM Datapath
DS-000001,my-dataset,CRAWL-Gen,1000000000,1.0,1000000000,Phase1,https://example.com,/path/to/data
```

#### Format 2: Database Field Names (with underscores)
```csv
dataset_id,data_name_split,domain,gemma3_token_cnt,epochs,desired_token_cnt,training_stage,link,ibm_datapath
DS-000001,my-dataset,CRAWL-Gen,1000000000,1.0,1000000000,Phase1,https://example.com,/path/to/data
```

**Both formats work!** The system automatically detects which format you're using.

### Column Details

| Column | Required? | Description |
|--------|-----------|-------------|
| Dataset ID | Auto-generated if empty | Unique ID (DS-XXXXXX format) |
| Data Name Split | **Yes** | Dataset name/identifier |
| Domain | No | Dataset category or domain |
| Gemma3 Token Count | No | Number of tokens |
| Epochs | No | Training epochs |
| Desired Token Count | No | Target token count |
| Training Stage | **Yes** | Training phase (e.g., Phase1, Phase2) |
| Link | No | URL to dataset or documentation |
| IBM Datapath | No | File system path to dataset |

### Tips

- ✅ **Leave Dataset ID blank** for new rows - the system auto-generates them
- ✅ **Keep existing Dataset IDs** when modifying data
- ✅ **Use either column format** - display names OR database field names
- ⚠️ **Don't use both formats** in the same CSV

---

## Troubleshooting

### "No changes detected" after upload

**Cause:** Your CSV data is identical to what's already in the database.

**Solution:**
- Verify you actually changed values in the CSV
- Check that column names match the expected format
- Download the current data and compare with your upload

### Upload shows no pending changes

**Cause:** All your changes may have already been approved.

**Solution:** Click "View Pending Changes" - if it's empty, the data is already in the main dataset.

### Cannot approve changes

**Cause:** You don't have admin approval permissions.

**Solution:** Contact your administrator to approve your changes.

### CSV Upload Fails

**Possible causes:**
- Missing required columns (`Data Name Split` or `Training Stage`)
- Malformed CSV file
- Invalid data types (e.g., text in a number field)

**Solution:**
- Use the downloaded CSV as a template
- Ensure all required columns are present
- Verify data types match the expected format

### No Charts in Data Statistics

**Cause:** "No charts uploaded yet" appears in the Data Statistics tab.

**Solution:**
- Charts must be generated and uploaded separately
- Follow the chart upload process in [Data Statistics](#data-statistics)
- Contact your administrator to upload visualizations

### Chart Upload Script Fails

**Possible causes:**
- Web application is not running
- Wrong port or URL in upload_charts.py configuration
- No PNG files matching the pattern in utils directory

**Solution:**
- Verify the web app is running: `python app.py`
- Check WEBAPP_URL in upload_charts.py matches your app's URL
- Ensure you've generated charts with the Jupyter notebook first
- Check that PNG files exist in the utils directory

### Charts Not Appearing After Upload

**Cause:** Charts were uploaded but don't show in the Data Statistics tab.

**Solution:**
- Refresh the browser page
- Check the Flask console for error messages
- Verify the database connection is working
- Check that the `charts` table was created properly

---

## Best Practices

1. **Download Before Uploading** - Always start with the latest data
2. **Small Changes First** - Test with a few rows before bulk uploads
3. **Descriptive Names** - Use clear, consistent dataset names
4. **Review Before Approving** - Carefully check all changes in the preview
5. **Keep Backups** - Save copies of your CSV files before uploading

---

## Support

For issues, questions, or feature requests:
- Check the [Troubleshooting](#troubleshooting) section
- Contact your system administrator
- Report bugs on the GitHub repository

---

**Last Updated:** February 2026
**Version:** 1.0
