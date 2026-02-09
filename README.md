# Dataset Tracker

A company-wide dataset management system with version control, CSV import/export, and diff-based approval workflow.

## Features

- 📥 **CSV Download**: Export entire database to CSV for easy manipulation
- 📤 **CSV Upload**: Upload modified CSVs with automatic diff detection
- 🔍 **Diff Review**: Visual comparison of additions, modifications, and deletions
- ✅ **Approval Workflow**: Admin approval required before changes are committed
- 📝 **Audit Log**: Complete history of all changes with timestamps
- ⚙️ **Easy Schema Updates**: Simple JSON configuration for adding/modifying columns

## Quick Start

### 1. Prerequisites

- Python 3.8+
- PostgreSQL database

### 2. Installation

```bash
cd dataset-tracker

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Create a `.env` file:

```env
DATABASE_URL=postgresql://username:password@localhost/dataset_tracker
SECRET_KEY=your-secret-key-here
```

### 4. Run

```bash
python app.py
```

Visit `http://localhost:5000`

## Usage

See full documentation in the project files.
