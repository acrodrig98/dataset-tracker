# dataset-tracker/app.py
from flask import Flask, render_template, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pandas as pd
import io
import json
import os

app = Flask(__name__)

# Use PostgreSQL on Render, SQLite locally
database_url = os.getenv('DATABASE_URL', 'postgresql://antoniorodriguez@localhost:5432/dataset_tracking')
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url

db = SQLAlchemy(app)

# Load schema configuration
with open('schema_config.json', 'r') as f:
    SCHEMA_CONFIG = json.load(f)

# Models
class Dataset(db.Model):
    __tablename__ = 'datasets'
    id = db.Column(db.Integer, primary_key=True)
    data_name_split = db.Column(db.Text, nullable=False)
    domain = db.Column(db.Text)
    gemma3_token_cnt = db.Column(db.Float)
    epochs = db.Column(db.Float)
    desired_token_cnt = db.Column(db.Float)
    training_stage = db.Column(db.Text, nullable=False)  # Changed from phase
    link = db.Column(db.Text)
    ibm_datapath = db.Column(db.Text)

class PendingChange(db.Model):
    __tablename__ = 'pending_changes'
    id = db.Column(db.Integer, primary_key=True)
    change_type = db.Column(db.String(20))  # 'add', 'modify', 'delete'
    dataset_name = db.Column(db.String(255))
    old_data = db.Column(db.JSON)
    new_data = db.Column(db.JSON)
    submitted_by = db.Column(db.String(100))
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'approved', 'rejected'

class AuditLog(db.Model):
    __tablename__ = 'audit_log'
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(50))
    dataset_name = db.Column(db.String(255))
    changed_by = db.Column(db.String(100))
    changed_at = db.Column(db.DateTime, default=datetime.utcnow)
    changes = db.Column(db.JSON)

# Routes
@app.route('/')
def index():
    return render_template('index.html', schema=SCHEMA_CONFIG)

@app.route('/api/datasets')
def get_datasets():
    try:
        datasets = Dataset.query.all()
        result = []
        for d in datasets:
            result.append({
                'id': d.id,
                'data_name_split': d.data_name_split,
                'domain': d.domain,
                'gemma3_token_cnt': d.gemma3_token_cnt,
                'epochs': d.epochs,
                'desired_token_cnt': d.desired_token_cnt,
                'training_stage': d.training_stage,
                'link': d.link,
                'ibm_datapath': d.ibm_datapath
            })
        return jsonify(result)
    except Exception as e:
        print(f"ERROR in /api/datasets: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/download')
def download_csv():
    datasets = Dataset.query.all()
    
    # Create DataFrame with columns from schema config
    columns = [col['name'] for col in SCHEMA_CONFIG['columns']]
    data = []
    
    for d in datasets:
        row = []
        for col in SCHEMA_CONFIG['columns']:
            row.append(getattr(d, col['db_field'], ''))
        data.append(row)
    
    df = pd.DataFrame(data, columns=columns)
    
    # Convert to CSV
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
    
    try:
        # Read CSV
        df = pd.read_csv(file)
        
        # Get current datasets
        current_datasets = {d.dataset_name: d for d in Dataset.query.all()}
        
        # Calculate diff
        diff = {
            'added': [],
            'modified': [],
            'deleted': []
        }
        
        uploaded_names = set()
        
        # Check for additions and modifications
        for _, row in df.iterrows():
            dataset_name = row.get('Dataset Name', row.get('dataset_name'))
            if pd.isna(dataset_name):
                continue
                
            uploaded_names.add(dataset_name)
            
            # Create new_data dict from row
            new_data = {}
            for col in SCHEMA_CONFIG['columns']:
                csv_name = col['name']
                db_field = col['db_field']
                value = row.get(csv_name, '')
                new_data[db_field] = '' if pd.isna(value) else str(value)
            
            if dataset_name in current_datasets:
                # Check if modified
                old_dataset = current_datasets[dataset_name]
                old_data = {
                    col['db_field']: getattr(old_dataset, col['db_field'], '')
                    for col in SCHEMA_CONFIG['columns']
                }
                
                if old_data != new_data:
                    diff['modified'].append({
                        'dataset_name': dataset_name,
                        'old': old_data,
                        'new': new_data
                    })
            else:
                # New dataset
                diff['added'].append({
                    'dataset_name': dataset_name,
                    'data': new_data
                })
        
        # Check for deletions
        for name in current_datasets:
            if name not in uploaded_names:
                old_data = {
                    col['db_field']: getattr(current_datasets[name], col['db_field'], '')
                    for col in SCHEMA_CONFIG['columns']
                }
                diff['deleted'].append({
                    'dataset_name': name,
                    'data': old_data
                })
        
        # Store pending changes
        for item in diff['added']:
            change = PendingChange(
                change_type='add',
                dataset_name=item['dataset_name'],
                new_data=item['data'],
                submitted_by=submitted_by
            )
            db.session.add(change)
        
        for item in diff['modified']:
            change = PendingChange(
                change_type='modify',
                dataset_name=item['dataset_name'],
                old_data=item['old'],
                new_data=item['new'],
                submitted_by=submitted_by
            )
            db.session.add(change)
        
        for item in diff['deleted']:
            change = PendingChange(
                change_type='delete',
                dataset_name=item['dataset_name'],
                old_data=item['data'],
                submitted_by=submitted_by
            )
            db.session.add(change)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'diff': diff,
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
    
    try:
        for change_id in change_ids:
            change = PendingChange.query.get(change_id)
            if not change or change.status != 'pending':
                continue
            
            if change.change_type == 'add':
                # Add new dataset
                new_dataset = Dataset(dataset_name=change.dataset_name)
                for key, value in change.new_data.items():
                    setattr(new_dataset, key, value)
                db.session.add(new_dataset)
                
                # Log
                audit = AuditLog(
                    action='add',
                    dataset_name=change.dataset_name,
                    changed_by=approved_by,
                    changes={'new_data': change.new_data}
                )
                db.session.add(audit)
                
            elif change.change_type == 'modify':
                # Update existing dataset
                dataset = Dataset.query.filter_by(dataset_name=change.dataset_name).first()
                if dataset:
                    old_values = {}
                    for key, value in change.new_data.items():
                        old_values[key] = getattr(dataset, key, None)
                        setattr(dataset, key, value)
                    
                    # Log
                    audit = AuditLog(
                        action='modify',
                        dataset_name=change.dataset_name,
                        changed_by=approved_by,
                        changes={'old': old_values, 'new': change.new_data}
                    )
                    db.session.add(audit)
                    
            elif change.change_type == 'delete':
                # Delete dataset
                dataset = Dataset.query.filter_by(dataset_name=change.dataset_name).first()
                if dataset:
                    db.session.delete(dataset)
                    
                    # Log
                    audit = AuditLog(
                        action='delete',
                        dataset_name=change.dataset_name,
                        changed_by=approved_by,
                        changes={'deleted_data': change.old_data}
                    )
                    db.session.add(audit)
            
            # Mark as approved
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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=8000, host='0.0.0.0')