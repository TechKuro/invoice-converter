#!/usr/bin/env python3
"""
PDF Invoice Converter - Web Application
======================================

Flask web application for processing PDF invoices with user authentication,
database storage, and a modern web interface.
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import uuid

# Add the parent directory to Python path to import our existing converter
sys.path.append(str(Path(__file__).parent.parent))
from pdf_to_excel_converter import PDFDataExtractor, ExcelExporter

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///pdf_converter.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = Path(__file__).parent / 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Create upload directory
app.config['UPLOAD_FOLDER'].mkdir(exist_ok=True)

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    upload_sessions = db.relationship('UploadSession', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

# Upload session model
class UploadSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    total_files = db.Column(db.Integer, default=0)
    processed_files = db.Column(db.Integer, default=0)
    output_file = db.Column(db.String(255))
    
    # Relationships
    processed_files_rel = db.relationship('ProcessedFile', backref='upload_session', lazy=True)

# Processed file model
class ProcessedFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    upload_session_id = db.Column(db.Integer, db.ForeignKey('upload_session.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed
    error_message = db.Column(db.Text)
    
    # Extracted data
    num_pages = db.Column(db.Integer)
    num_tables = db.Column(db.Integer)
    num_line_items = db.Column(db.Integer)
    processed_at = db.Column(db.DateTime)
    
    # Relationships
    line_items = db.relationship('LineItem', backref='processed_file', lazy=True)
    invoice_data = db.relationship('InvoiceData', backref='processed_file', lazy=True, uselist=False)

# Invoice data model
class InvoiceData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    processed_file_id = db.Column(db.Integer, db.ForeignKey('processed_file.id'), nullable=False)
    invoice_number = db.Column(db.String(100))
    invoice_date = db.Column(db.Date)
    vendor = db.Column(db.String(255))
    total_amount = db.Column(db.Numeric(10, 2))
    currency = db.Column(db.String(3), default='USD')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Line item model
class LineItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    processed_file_id = db.Column(db.Integer, db.ForeignKey('processed_file.id'), nullable=False)
    description = db.Column(db.Text)
    quantity = db.Column(db.Numeric(10, 3))
    unit_price = db.Column(db.Numeric(10, 2))
    amount = db.Column(db.Numeric(10, 2))
    vat_rate = db.Column(db.Numeric(5, 2))
    source = db.Column(db.String(50))  # table, text_parsing, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Forms
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

class UploadForm(FlaskForm):
    files = FileField('PDF Files', validators=[
        FileRequired(),
        FileAllowed(['pdf'], 'PDF files only!')
    ])
    submit = SubmitField('Upload and Process')

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        flash('Invalid username or password')
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful!')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get recent upload sessions
    recent_sessions = UploadSession.query.filter_by(user_id=current_user.id)\
        .order_by(UploadSession.created_at.desc()).limit(10).all()
    
    # Get statistics
    total_sessions = UploadSession.query.filter_by(user_id=current_user.id).count()
    total_files = ProcessedFile.query.join(UploadSession)\
        .filter(UploadSession.user_id == current_user.id).count()
    
    return render_template('dashboard.html', 
                         recent_sessions=recent_sessions,
                         total_sessions=total_sessions,
                         total_files=total_files)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    form = UploadForm()
    if form.validate_on_submit():
        # Handle file upload and processing
        files = request.files.getlist('files')
        if not files or files[0].filename == '':
            flash('No files selected')
            return redirect(request.url)
        
        # Create upload session
        upload_session = UploadSession(
            user_id=current_user.id,
            total_files=len(files)
        )
        db.session.add(upload_session)
        db.session.commit()
        
        # Save files and create processed file records
        session_dir = app.config['UPLOAD_FOLDER'] / upload_session.session_id
        session_dir.mkdir(exist_ok=True)
        
        for file in files:
            if file and file.filename.lower().endswith('.pdf'):
                filename = secure_filename(file.filename)
                file_path = session_dir / filename
                file.save(str(file_path))
                
                processed_file = ProcessedFile(
                    upload_session_id=upload_session.id,
                    filename=filename,
                    file_path=str(file_path)
                )
                db.session.add(processed_file)
        
        db.session.commit()
        flash(f'Successfully uploaded {len(files)} files. Processing will begin shortly.')
        return redirect(url_for('session_detail', session_id=upload_session.session_id))
    
    return render_template('upload.html', form=form)

@app.route('/session/<session_id>')
@login_required
def session_detail(session_id):
    upload_session = UploadSession.query.filter_by(
        session_id=session_id, 
        user_id=current_user.id
    ).first_or_404()
    
    return render_template('session_detail.html', session=upload_session)

@app.route('/api/process/<session_id>', methods=['POST'])
@login_required
def process_session(session_id):
    """API endpoint to trigger processing of an upload session"""
    upload_session = UploadSession.query.filter_by(
        session_id=session_id, 
        user_id=current_user.id
    ).first_or_404()
    
    if upload_session.status != 'pending':
        return jsonify({'error': 'Session already processed or in progress'}), 400
    
    # Update session status
    upload_session.status = 'processing'
    db.session.commit()
    
    try:
        # Process files using existing converter
        extractor = PDFDataExtractor(extract_tables=True, extract_text=True)
        exporter = ExcelExporter()
        all_data = []
        
        for processed_file in upload_session.processed_files_rel:
            processed_file.status = 'processing'
            db.session.commit()
            
            try:
                # Extract data from PDF
                pdf_path = Path(processed_file.file_path)
                extracted_data = extractor.extract_from_pdf(pdf_path)
                all_data.append(extracted_data)
                
                # Store in database
                processed_file.num_pages = extracted_data.get('metadata', {}).get('pages', 0)
                processed_file.num_tables = len(extracted_data.get('tables', []))
                processed_file.num_line_items = len(extracted_data.get('line_items', []))
                processed_file.processed_at = datetime.utcnow()
                processed_file.status = 'completed'
                
                # Store line items
                for item in extracted_data.get('line_items', []):
                    line_item = LineItem(
                        processed_file_id=processed_file.id,
                        description=item.get('description', ''),
                        quantity=item.get('quantity'),
                        unit_price=item.get('unit_price'),
                        amount=item.get('amount'),
                        vat_rate=item.get('vat_rate'),
                        source=item.get('source', 'unknown')
                    )
                    db.session.add(line_item)
                
                upload_session.processed_files += 1
                
            except Exception as e:
                processed_file.status = 'failed'
                processed_file.error_message = str(e)
            
            db.session.commit()
        
        # Generate Excel file
        if all_data:
            output_filename = f"results_{upload_session.session_id}.xlsx"
            output_path = app.config['UPLOAD_FOLDER'] / upload_session.session_id / output_filename
            exporter.export_to_excel(all_data, output_path)
            upload_session.output_file = str(output_path)
        
        # Update session status
        upload_session.status = 'completed'
        upload_session.completed_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': 'Processing completed successfully'})
        
    except Exception as e:
        upload_session.status = 'failed'
        db.session.commit()
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500

@app.route('/download/<session_id>')
@login_required
def download_results(session_id):
    """Download the Excel results file"""
    upload_session = UploadSession.query.filter_by(
        session_id=session_id, 
        user_id=current_user.id
    ).first_or_404()
    
    if not upload_session.output_file or not Path(upload_session.output_file).exists():
        flash('Results file not found or not yet generated')
        return redirect(url_for('session_detail', session_id=session_id))
    
    return send_file(upload_session.output_file, as_attachment=True)

# Create database tables
with app.app_context():
    db.create_all()
    
    # Create a default admin user if no users exist
    if User.query.count() == 0:
        admin = User(username='admin', email='admin@example.com')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Created default admin user: admin/admin123")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 