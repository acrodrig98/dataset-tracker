# dataset-tracker/app.py
from flask import Flask, render_template, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pandas as pd
import io
import json
import os

app = Flask(__name__)

# Configuration - Connect to PostgreSQL
database_url = os.getenv('DATABASE_URL', 'postgresql://antoniorodriguez@localhost:5432/dataset_tracking')
# Render uses postgres:// but SQLAlchemy needs postgresql://
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Admin user who can approve/reject changes
ADMIN_USER = os.getenv('ADMIN_USER', 'antoniorodriguez')  # Set via environment variable or default

db = SQLAlchemy(app)

# Load schema configuration
with open('schema_config.json', 'r') as f:
    SCHEMA_CONFIG = json.load(f)

# Models
class Dataset(db.Model):
    __tablename__ = 'datasets'
    id = db.Column(db.Integer, primary_key=True)  # Keep as 'id' - it's the auto-increment PK
    dataset_id = db.Column(db.Text, unique=True, nullable=False)  # This is your custom ID like DS-000001
    data_name_split = db.Column(db.Text, nullable=False)
    domain = db.Column(db.Text)
    gemma3_token_cnt = db.Column(db.Float)
    epochs = db.Column(db.Float)
    desired_token_cnt = db.Column(db.Float)
    training_stage = db.Column(db.Text, nullable=False)
    link = db.Column(db.Text)
    ibm_datapath = db.Column(db.Text)

class PendingChange(db.Model):
    __tablename__ = 'pending_changes'
    id = db.Column(db.Integer, primary_key=True)  # Keep as 'id'
    change_type = db.Column(db.String(20))
    dataset_name = db.Column(db.String(255))
    old_data = db.Column(db.JSON)
    new_data = db.Column(db.JSON)
    submitted_by = db.Column(db.String(100))
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')

class AuditLog(db.Model):
    __tablename__ = 'audit_log'
    id = db.Column(db.Integer, primary_key=True)  # Keep as 'id'
    action = db.Column(db.String(50))
    dataset_name = db.Column(db.String(255))
    changed_by = db.Column(db.String(100))
    changed_at = db.Column(db.DateTime, default=datetime.utcnow)
    changes = db.Column(db.JSON)

class Chart(db.Model):
    __tablename__ = 'charts'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    chart_type = db.Column(db.String(100))  # e.g., 'pie', 'histogram'
    phase = db.Column(db.String(100))  # e.g., 'BMoE-Phase1'
    filename = db.Column(db.String(255), nullable=False, unique=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    uploaded_by = db.Column(db.String(100))

# Routes
@app.route('/')
def index():
    return render_template('index.html', schema=SCHEMA_CONFIG)

@app.route('/api/datasets')
def get_datasets():
    try:
        datasets = Dataset.query.all()
        return jsonify([{
            'id': d.id,
            'dataset_id': d.dataset_id,
            'data_name_split': d.data_name_split,
            'domain': d.domain,
            'gemma3_token_cnt': d.gemma3_token_cnt,
            'epochs': d.epochs,
            'desired_token_cnt': d.desired_token_cnt,
            'training_stage': d.training_stage,
            'link': d.link,
            'ibm_datapath': d.ibm_datapath
        } for d in datasets])
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/download')
def download_csv():
    datasets = Dataset.query.all()
    
    columns = [col['name'] for col in SCHEMA_CONFIG['columns']]
    data = []
    
    for d in datasets:
        row = []
        for col in SCHEMA_CONFIG['columns']:
            row.append(getattr(d, col['db_field'], ''))
        data.append(row)
    
    df = pd.DataFrame(data, columns=columns)
    
    output = io.StringIO()
    df.to_csv(output, index=False)
    output.seek(0)
    
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'datasets_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    )

@app.route('/api/upload', methods=['POST'])
def upload_csv():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    submitted_by = request.form.get('submitted_by', 'Unknown')
    upload_mode = request.form.get('upload_mode', 'add')
    
    try:
        df = pd.read_csv(file)

        # Debug: Log the columns found in the CSV
        print(f"CSV columns found: {list(df.columns)}")
        print(f"CSV has {len(df)} rows")

        # Get current datasets by dataset_id (the custom ID like DS-000001)
        current_datasets_by_id = {d.dataset_id: d for d in Dataset.query.all()}
        
        # Get max database id for generating new dataset_ids
        max_db_id = db.session.query(db.func.max(Dataset.id)).scalar() or 0
        next_id_counter = max_db_id + 1
        
        diff = {
            'added': [],
            'modified': [],
            'deleted': []
        }
        
        uploaded_ids = set()
        
        for _, row in df.iterrows():
            # Get or generate dataset_id - try both display name and db field name
            dataset_id = None
            for possible_name in ['Dataset ID', 'dataset_id']:
                if possible_name in row and not pd.isna(row[possible_name]):
                    dataset_id = row[possible_name]
                    break

            if not dataset_id:
                dataset_id = f'DS-{str(next_id_counter).zfill(6)}'
                next_id_counter += 1

            # Get dataset name - try both display name and db field name
            dataset_name = None
            for possible_name in ['Data Name Split', 'data_name_split']:
                if possible_name in row and not pd.isna(row[possible_name]):
                    dataset_name = row[possible_name]
                    break

            if not dataset_name:
                continue

            uploaded_ids.add(dataset_id)

            new_data = {}
            for col in SCHEMA_CONFIG['columns']:
                csv_name = col['name']
                db_field = col['db_field']

                if db_field == 'dataset_id':
                    new_data[db_field] = str(dataset_id)
                else:
                    # Try to get value using both display name and db field name
                    value = None
                    if csv_name in row:
                        value = row[csv_name]
                    elif db_field in row:
                        value = row[db_field]

                    new_data[db_field] = '' if pd.isna(value) else str(value)

            # Debug: Log first row to verify data is being read correctly
            if len(diff['added']) == 0 and len(diff['modified']) == 0:
                print(f"First row data: {new_data}")

            if dataset_id in current_datasets_by_id:
                old_dataset = current_datasets_by_id[dataset_id]
                old_data = {
                    col['db_field']: str(getattr(old_dataset, col['db_field'], ''))
                    for col in SCHEMA_CONFIG['columns']
                }
                
                if old_data != new_data:
                    diff['modified'].append({
                        'dataset_id': dataset_id,
                        'data_name_split': dataset_name,
                        'old': old_data,
                        'new': new_data
                    })
            else:
                diff['added'].append({
                    'dataset_id': dataset_id,
                    'data_name_split': dataset_name,
                    'data': new_data
                })
        
        if upload_mode == 'replace':
            for dataset_id in current_datasets_by_id:
                if dataset_id not in uploaded_ids:
                    old_dataset = current_datasets_by_id[dataset_id]
                    old_data = {
                        col['db_field']: str(getattr(old_dataset, col['db_field'], ''))
                        for col in SCHEMA_CONFIG['columns']
                    }
                    diff['deleted'].append({
                        'dataset_id': dataset_id,
                        'data_name_split': old_dataset.data_name_split,
                        'data': old_data
                    })
        
        for item in diff['added']:
            change = PendingChange(
                change_type='add',
                dataset_name=item['dataset_id'],
                new_data=item['data'],
                submitted_by=submitted_by
            )
            db.session.add(change)
        
        for item in diff['modified']:
            change = PendingChange(
                change_type='modify',
                dataset_name=item['dataset_id'],
                old_data=item['old'],
                new_data=item['new'],
                submitted_by=submitted_by
            )
            db.session.add(change)
        
        for item in diff['deleted']:
            change = PendingChange(
                change_type='delete',
                dataset_name=item['dataset_id'],
                old_data=item['data'],
                submitted_by=submitted_by
            )
            db.session.add(change)
        
        db.session.commit()

        # Debug: Log the summary
        print(f"Upload summary - Added: {len(diff['added'])}, Modified: {len(diff['modified'])}, Deleted: {len(diff['deleted'])}")

        return jsonify({
            'success': True,
            'diff': diff,
            'upload_mode': upload_mode,
            'summary': {
                'added': len(diff['added']),
                'modified': len(diff['modified']),
                'deleted': len(diff['deleted'])
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/pending')
def get_pending():
    pending = PendingChange.query.filter_by(status='pending').all()
    
    result = {
        'added': [],
        'modified': [],
        'deleted': []
    }
    
    for change in pending:
        if change.change_type == 'add':
            result['added'].append({
                'id': change.id,
                'dataset_name': change.dataset_name,
                'data': change.new_data,
                'submitted_by': change.submitted_by,
                'submitted_at': change.submitted_at.isoformat()
            })
        elif change.change_type == 'modify':
            result['modified'].append({
                'id': change.id,
                'dataset_name': change.dataset_name,
                'old': change.old_data,
                'new': change.new_data,
                'submitted_by': change.submitted_by,
                'submitted_at': change.submitted_at.isoformat()
            })
        elif change.change_type == 'delete':
            result['deleted'].append({
                'id': change.id,
                'dataset_name': change.dataset_name,
                'data': change.old_data,
                'submitted_by': change.submitted_by,
                'submitted_at': change.submitted_at.isoformat()
            })
    
    return jsonify(result)

@app.route('/api/approve', methods=['POST'])
def approve_changes():
    data = request.json
    change_ids = data.get('change_ids', [])
    approved_by = data.get('approved_by', 'Admin')

    # Authorization check - only the admin user can approve changes
    if approved_by != ADMIN_USER:
        return jsonify({
            'error': f'Unauthorized. Only {ADMIN_USER} can approve changes.',
            'unauthorized': True
        }), 403

    try:
        for change_id in change_ids:
            change = PendingChange.query.get(change_id)
            if not change or change.status != 'pending':
                continue
            
            if change.change_type == 'add':
                new_dataset = Dataset()
                for key, value in change.new_data.items():
                    setattr(new_dataset, key, value)
                db.session.add(new_dataset)
                
                audit = AuditLog(
                    action='add',
                    dataset_name=change.dataset_name,
                    changed_by=approved_by,
                    changes={'new_data': change.new_data}
                )
                db.session.add(audit)
                
            elif change.change_type == 'modify':
                dataset = Dataset.query.filter_by(dataset_id=change.dataset_name).first()
                if dataset:
                    old_values = {}
                    for key, value in change.new_data.items():
                        old_values[key] = getattr(dataset, key, None)
                        setattr(dataset, key, value)
                    
                    audit = AuditLog(
                        action='modify',
                        dataset_name=change.dataset_name,
                        changed_by=approved_by,
                        changes={'old': old_values, 'new': change.new_data}
                    )
                    db.session.add(audit)
                    
            elif change.change_type == 'delete':
                dataset = Dataset.query.filter_by(dataset_id=change.dataset_name).first()
                if dataset:
                    db.session.delete(dataset)
                    
                    audit = AuditLog(
                        action='delete',
                        dataset_name=change.dataset_name,
                        changed_by=approved_by,
                        changes={'deleted_data': change.old_data}
                    )
                    db.session.add(audit)
            
            change.status = 'approved'
        
        db.session.commit()
        return jsonify({'success': True})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/api/reject', methods=['POST'])
def reject_changes():
    data = request.json
    change_ids = data.get('change_ids', [])
    rejected_by = data.get('rejected_by', data.get('approved_by', 'Admin'))  # Get user who is rejecting

    # Authorization check - only the admin user can reject changes
    if rejected_by != ADMIN_USER:
        return jsonify({
            'error': f'Unauthorized. Only {ADMIN_USER} can reject changes.',
            'unauthorized': True
        }), 403

    try:
        for change_id in change_ids:
            change = PendingChange.query.get(change_id)
            if change and change.status == 'pending':
                change.status = 'rejected'
        
        db.session.commit()
        return jsonify({'success': True})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/api/audit-log')
def get_audit_log():
    logs = AuditLog.query.order_by(AuditLog.changed_at.desc()).limit(100).all()
    return jsonify([{
        'id': log.id,
        'action': log.action,
        'dataset_name': log.dataset_name,
        'changed_by': log.changed_by,
        'changed_at': log.changed_at.isoformat(),
        'changes': log.changes
    } for log in logs])

@app.route('/api/config')
def get_config():
    """Returns configuration info including who can approve changes"""
    return jsonify({
        'admin_user': ADMIN_USER,
        'message': f'Only {ADMIN_USER} can approve or reject pending changes'
    })

@app.route('/api/charts', methods=['GET'])
def get_charts():
    """Get all uploaded charts"""
    charts = Chart.query.order_by(Chart.uploaded_at.desc()).all()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'chart_type': c.chart_type,
        'phase': c.phase,
        'filename': c.filename,
        'uploaded_at': c.uploaded_at.isoformat(),
        'uploaded_by': c.uploaded_by
    } for c in charts])

@app.route('/api/charts/upload', methods=['POST'])
def upload_chart():
    """Upload a chart image"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    chart_name = request.form.get('name', '')
    chart_type = request.form.get('chart_type', 'unknown')
    phase = request.form.get('phase', '')
    uploaded_by = request.form.get('uploaded_by', 'Unknown')

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Create static/charts directory if it doesn't exist
    charts_dir = os.path.join(app.root_path, 'static', 'charts')
    os.makedirs(charts_dir, exist_ok=True)

    # Save the file
    filename = file.filename
    filepath = os.path.join(charts_dir, filename)
    file.save(filepath)

    # Check if chart already exists and update it
    existing_chart = Chart.query.filter_by(filename=filename).first()
    if existing_chart:
        existing_chart.name = chart_name
        existing_chart.chart_type = chart_type
        existing_chart.phase = phase
        existing_chart.uploaded_at = datetime.utcnow()
        existing_chart.uploaded_by = uploaded_by
    else:
        # Create new chart record
        chart = Chart(
            name=chart_name,
            chart_type=chart_type,
            phase=phase,
            filename=filename,
            uploaded_by=uploaded_by
        )
        db.session.add(chart)

    db.session.commit()

    return jsonify({
        'success': True,
        'filename': filename,
        'message': 'Chart uploaded successfully'
    })

@app.route('/api/charts/<int:chart_id>', methods=['DELETE'])
def delete_chart(chart_id):
    """Delete a chart"""
    chart = Chart.query.get(chart_id)
    if not chart:
        return jsonify({'error': 'Chart not found'}), 404

    # Delete the file
    filepath = os.path.join(app.root_path, 'static', 'charts', chart.filename)
    if os.path.exists(filepath):
        os.remove(filepath)

    # Delete the database record
    db.session.delete(chart)
    db.session.commit()

    return jsonify({'success': True})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.getenv('PORT', 4000))
    app.run(debug=True, port=port, host='0.0.0.0')