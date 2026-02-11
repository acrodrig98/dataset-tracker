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

Create a `.env` file (see `.env.example`):

```env
DATABASE_URL=postgresql://username:password@localhost/dataset_tracker
SECRET_KEY=your-secret-key-here
ADMIN_USER=your_username  # Only this user can approve/reject changes
```

### 4. Run

```bash
python app.py
```

Visit `http://localhost:8000` (or port 4000 if configured differently)

## Usage

📖 **For end users:** See the complete [User Guide](USER_GUIDE.md) for detailed instructions on:
- Downloading datasets as CSV
- Uploading and modifying data
- Reviewing pending changes
- Approving/rejecting changes (admins)
- CSV format requirements

### Quick Overview

1. **Download** - Click "Download CSV" to export current datasets
2. **Upload** - Click "Upload CSV" and select your modified file
3. **Review** - Preview shows additions, modifications, and deletions
4. **Approve** - Admin approves changes to apply them to the database

### Admin Configuration

Only the user specified in `ADMIN_USER` environment variable can approve or reject pending changes. This ensures controlled access to database modifications while allowing anyone to propose changes.

## Architecture

### Database Schema

The system uses three main tables:

- **`datasets`** - Main table storing approved dataset records
- **`pending_changes`** - Temporary storage for proposed changes (add/modify/delete)
- **`audit_log`** - Historical record of all approved changes

### Workflow

```
User uploads CSV → Creates pending_changes → Admin reviews → Approved changes written to datasets
```

All changes are atomic and logged for audit purposes.

## Deployment

### Production Checklist

1. Set strong `SECRET_KEY` in environment variables
2. Configure `DATABASE_URL` for production database
3. Set `ADMIN_USER` to the authorized approver's username
4. Ensure PostgreSQL is properly secured
5. Use a production WSGI server (e.g., Gunicorn)
6. Enable HTTPS

### Example Production Setup

```bash
# Install production dependencies
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

[Add your license here]
