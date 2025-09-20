from flask import Flask, render_template, request, jsonify, send_file
from flask_mail import Mail, Message
import sqlite3
import os
from datetime import datetime, date, timedelta
import csv
import io
from functools import wraps
import random
import string
import hashlib

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'mahilnila2007@gmail.com'  # Your email
app.config['MAIL_PASSWORD'] = 'lysk oofx wibm laoc'     # Replace with Gmail App Password
app.config['MAIL_DEFAULT_SENDER'] = 'mahilnila2007@gmail.com'

# NOTE: To enable real email sending:
# 1. Go to your Google Account settings
# 2. Enable 2-Step Verification
# 3. Generate an App Password (not your regular Gmail password)
# 4. Replace 'your_app_password_here' above with the generated App Password
# 5. The system will automatically send real emails instead of console simulation

# Initialize Flask-Mail
mail = Mail()

# Database configuration - Use absolute paths to ensure DBs are in the Amma code folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATIENTS = os.path.join(BASE_DIR, 'patient.db')
DATABASE_DATA = os.path.join(BASE_DIR, 'data.db')

def init_databases():
    """Initialize both databases with required tables"""
    
    # Initialize patient database
    conn_patients = sqlite3.connect(DATABASE_PATIENTS)
    c = conn_patients.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            serial_number TEXT UNIQUE NOT NULL,
            patient_name TEXT NOT NULL,
            phone_number TEXT NOT NULL,
            age INTEGER NOT NULL,
            sex TEXT NOT NULL,
            marital_status TEXT NOT NULL,
            problem TEXT NOT NULL,
            times_of_visit INTEGER DEFAULT 1,
            date_added DATE DEFAULT CURRENT_DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create trigger to update updated_at timestamp
    c.execute('''
        CREATE TRIGGER IF NOT EXISTS update_patients_timestamp 
        AFTER UPDATE ON patients
        FOR EACH ROW
        BEGIN
            UPDATE patients SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
        END
    ''')
    
    conn_patients.commit()
    conn_patients.close()
    
    # Initialize data database for appointments
    conn_data = sqlite3.connect(DATABASE_DATA)
    c = conn_data.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            patient_name TEXT NOT NULL,
            patient_phone TEXT NOT NULL,
            date DATE NOT NULL,
            time TIME NOT NULL,
            duration INTEGER DEFAULT 30,
            notes TEXT,
            status TEXT DEFAULT 'scheduled',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS predefined_symptoms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symptom_name TEXT UNIQUE NOT NULL,
            category TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert default symptoms if not exist
    default_symptoms = [
        ('High Blood Pressure', 'Cardiovascular'),
        ('Diabetes', 'Endocrine'),
        ('Insomnia', 'Neurological')
    ]
    
    for symptom, category in default_symptoms:
        c.execute('''
            INSERT OR IGNORE INTO predefined_symptoms (symptom_name, category)
            VALUES (?, ?)
        ''', (symptom, category))
    
    # Create trigger to update updated_at timestamp for appointments
    c.execute('''
        CREATE TRIGGER IF NOT EXISTS update_appointments_timestamp 
        AFTER UPDATE ON appointments
        FOR EACH ROW
        BEGIN
            UPDATE appointments SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
        END
    ''')
    
    # Create users table for authentication
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            designation TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            email_verified BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create OTP table for email verification
    c.execute('''
        CREATE TABLE IF NOT EXISTS otp_verification (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            otp_code TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            is_used BOOLEAN DEFAULT 0
        )
    ''')
    
    # Create OTP table for password reset (separate from registration OTPs)
    c.execute('''
        CREATE TABLE IF NOT EXISTS otps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            otp TEXT NOT NULL,
            expiry_time TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_used BOOLEAN DEFAULT 0
        )
    ''')

    c.execute('''
        CREATE TRIGGER IF NOT EXISTS update_users_timestamp 
        AFTER UPDATE ON users
        FOR EACH ROW
        BEGIN
            UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
        END
    ''')
    
    conn_data.commit()
    conn_data.close()

def get_db_connection(db_name):
    """Get database connection"""
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row
    return conn

def require_auth(f):
    """Simple authentication decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # For simplicity, we'll just check if it's a POST request to login
        # In a real application, you'd use sessions or JWT tokens
        return f(*args, **kwargs)
    return decorated_function

# Authentication utility functions
def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, password_hash):
    """Verify password against hash"""
    return hash_password(password) == password_hash

def generate_otp():
    """Generate 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))

def send_otp_email(email, otp, name="User"):
    """Send OTP via email using Flask-Mail"""
    try:
        print(f"Email config check - Server: {app.config.get('MAIL_SERVER')}, Port: {app.config.get('MAIL_PORT')}")
        print(f"Email config check - Username: {app.config.get('MAIL_USERNAME')}")
        print(f"Email config check - TLS: {app.config.get('MAIL_USE_TLS')}")
        
        # Create HTML content
        html = f"""
        <html>
          <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f4f4f4;">
            <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
              <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #007bff; margin: 0;">KALPANA MEDCARE</h1>
                <p style="color: #666; margin: 5px 0;">Hospital Management System</p>
              </div>
              
              <div style="text-align: center; padding: 20px; background: #f8f9fa; border-radius: 8px; margin: 20px 0;">
                <h2 style="color: #333; margin: 0 0 10px 0;">Hello {name}!</h2>
                <p style="color: #666; margin: 0 0 20px 0;">Your OTP for registration verification is:</p>
                <div style="font-size: 32px; font-weight: bold; color: #007bff; letter-spacing: 8px; margin: 20px 0;">
                  {otp}
                </div>
                <p style="color: #666; font-size: 14px; margin: 20px 0 0 0;">
                  This OTP will expire in 10 minutes. Please do not share this code with anyone.
                </p>
              </div>
              
              <div style="text-align: center; margin-top: 30px; color: #666; font-size: 12px;">
                <p>If you didn't request this verification, please ignore this email.</p>
                <p>© 2025 KALPANA MEDCARE. All rights reserved.</p>
              </div>
            </div>
          </body>
        </html>
        """
        
        print(f"Creating email message for {email}")
        
        # Create message
        msg = Message(
            subject="KALPANA MEDCARE - OTP Verification",
            recipients=[email],
            html=html,
            sender=app.config['MAIL_DEFAULT_SENDER']
        )
        
        print(f"Attempting to send email...")
        # Send email
        mail.send(msg)
        print(f"Email sent successfully to {email}")
        return True
        
    except Exception as e:
        print(f"Email error: {e}")
        print(f"Email error type: {type(e).__name__}")
        # Fallback: print OTP to console for testing
        print(f"FALLBACK - OTP for {email}: {otp}")
        return False

def cleanup_expired_otps():
    """Clean up expired OTP records"""
    try:
        conn = get_db_connection(DATABASE_DATA)
        conn.execute("DELETE FROM otp_verification WHERE expires_at < datetime('now')")
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Cleanup error: {e}")

# Routes
@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

# Patient API endpoints
@app.route('/api/patients', methods=['GET'])
@require_auth
def get_patients():
    """Get all patients"""
    conn = get_db_connection(DATABASE_PATIENTS)
    patients = conn.execute('''
        SELECT * FROM patients 
        ORDER BY created_at DESC
    ''').fetchall()
    conn.close()
    
    patients_list = []
    for patient in patients:
        patients_list.append({
            'id': patient['id'],
            'serial_number': patient['serial_number'],
            'patient_name': patient['patient_name'],
            'phone_number': patient['phone_number'],
            'age': patient['age'],
            'sex': patient['sex'],
            'marital_status': patient['marital_status'],
            'problem': patient['problem'],
            'times_of_visit': patient['times_of_visit'],
            'date_added': patient['date_added'],
            'created_at': patient['created_at'],
            'updated_at': patient['updated_at']
        })
    
    return jsonify({'patients': patients_list})

@app.route('/api/patients', methods=['POST'])
@require_auth
def create_patient():
    """Create a new patient"""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['serial_number', 'patient_name', 'phone_number', 'age', 'sex', 'marital_status', 'problem']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    conn = get_db_connection(DATABASE_PATIENTS)
    
    try:
        # Check if serial number already exists
        existing = conn.execute(
            'SELECT id FROM patients WHERE serial_number = ?',
            (data['serial_number'],)
        ).fetchone()
        
        if existing:
            return jsonify({'error': 'Serial number already exists'}), 400
        
        # Insert new patient
        cursor = conn.execute('''
            INSERT INTO patients (serial_number, patient_name, phone_number, age, sex, 
                                marital_status, problem, times_of_visit)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['serial_number'],
            data['patient_name'],
            data['phone_number'],
            data['age'],
            data['sex'],
            data['marital_status'],
            data['problem'],
            data.get('times_of_visit', 1)
        ))
        
        patient_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'patient_id': patient_id, 'message': 'Patient created successfully'})
        
    except sqlite3.IntegrityError as e:
        conn.close()
        return jsonify({'error': 'Database integrity error: ' + str(e)}), 400

@app.route('/api/patients/<int:patient_id>', methods=['PUT'])
@require_auth
def update_patient(patient_id):
    """Update an existing patient"""
    data = request.get_json()
    
    conn = get_db_connection(DATABASE_PATIENTS)
    
    # Check if patient exists
    patient = conn.execute('SELECT * FROM patients WHERE id = ?', (patient_id,)).fetchone()
    if not patient:
        conn.close()
        return jsonify({'error': 'Patient not found'}), 404
    
    # Build update query dynamically based on provided fields
    update_fields = []
    update_values = []
    
    allowed_fields = ['serial_number', 'patient_name', 'phone_number', 'age', 'sex', 
                     'marital_status', 'problem', 'times_of_visit']
    
    for field in allowed_fields:
        if field in data:
            update_fields.append(f'{field} = ?')
            update_values.append(data[field])
    
    if not update_fields:
        conn.close()
        return jsonify({'error': 'No valid fields to update'}), 400
    
    update_values.append(patient_id)
    
    try:
        conn.execute(f'''
            UPDATE patients 
            SET {', '.join(update_fields)}
            WHERE id = ?
        ''', update_values)
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Patient updated successfully'})
        
    except sqlite3.IntegrityError as e:
        conn.close()
        return jsonify({'error': 'Database integrity error: ' + str(e)}), 400

@app.route('/api/patients/<int:patient_id>', methods=['DELETE'])
@require_auth
def delete_patient(patient_id):
    """Delete a patient"""
    conn_patients = get_db_connection(DATABASE_PATIENTS)
    conn_data = get_db_connection(DATABASE_DATA)
    
    # Check if patient exists
    patient = conn_patients.execute('SELECT * FROM patients WHERE id = ?', (patient_id,)).fetchone()
    if not patient:
        conn_patients.close()
        conn_data.close()
        return jsonify({'error': 'Patient not found'}), 404
    
    try:
        # Delete related appointments first
        conn_data.execute('DELETE FROM appointments WHERE patient_id = ?', (patient_id,))
        conn_data.commit()
        
        # Delete patient
        conn_patients.execute('DELETE FROM patients WHERE id = ?', (patient_id,))
        conn_patients.commit()
        
        conn_patients.close()
        conn_data.close()
        
        return jsonify({'success': True, 'message': 'Patient deleted successfully'})
        
    except sqlite3.Error as e:
        conn_patients.close()
        conn_data.close()
        return jsonify({'error': 'Database error: ' + str(e)}), 500

# Appointment API endpoints
@app.route('/api/appointments', methods=['GET'])
@require_auth
def get_appointments():
    """Get all appointments"""
    conn = get_db_connection(DATABASE_DATA)
    appointments = conn.execute('''
        SELECT * FROM appointments 
        ORDER BY date, time
    ''').fetchall()
    conn.close()
    
    appointments_list = []
    for appointment in appointments:
        appointments_list.append({
            'id': appointment['id'],
            'patient_id': appointment['patient_id'],
            'patient_name': appointment['patient_name'],
            'patient_phone': appointment['patient_phone'],
            'date': appointment['date'],
            'time': appointment['time'],
            'duration': appointment['duration'],
            'notes': appointment['notes'],
            'status': appointment['status'],
            'created_at': appointment['created_at'],
            'updated_at': appointment['updated_at']
        })
    
    return jsonify({'appointments': appointments_list})

@app.route('/api/appointments', methods=['POST'])
@require_auth
def create_appointment():
    """Create a new appointment"""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['patient_id', 'date', 'time']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # Get patient details
    conn_patients = get_db_connection(DATABASE_PATIENTS)
    patient = conn_patients.execute(
        'SELECT patient_name, phone_number FROM patients WHERE id = ?',
        (data['patient_id'],)
    ).fetchone()
    conn_patients.close()
    
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    conn_data = get_db_connection(DATABASE_DATA)
    
    try:
        # Insert new appointment
        cursor = conn_data.execute('''
            INSERT INTO appointments (patient_id, patient_name, patient_phone, date, time, 
                                    duration, notes, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['patient_id'],
            patient['patient_name'],
            patient['phone_number'],
            data['date'],
            data['time'],
            data.get('duration', 30),
            data.get('notes', ''),
            data.get('status', 'scheduled')
        ))
        
        appointment_id = cursor.lastrowid
        conn_data.commit()
        conn_data.close()
        
        return jsonify({'success': True, 'appointment_id': appointment_id, 'message': 'Appointment created successfully'})
        
    except sqlite3.Error as e:
        conn_data.close()
        return jsonify({'error': 'Database error: ' + str(e)}), 500

@app.route('/api/appointments/<int:appointment_id>', methods=['PUT'])
@require_auth
def update_appointment(appointment_id):
    """Update an existing appointment"""
    data = request.get_json()
    
    conn = get_db_connection(DATABASE_DATA)
    
    # Check if appointment exists
    appointment = conn.execute('SELECT * FROM appointments WHERE id = ?', (appointment_id,)).fetchone()
    if not appointment:
        conn.close()
        return jsonify({'error': 'Appointment not found'}), 404
    
    # Build update query dynamically based on provided fields
    update_fields = []
    update_values = []
    
    allowed_fields = ['date', 'time', 'duration', 'notes', 'status']
    
    for field in allowed_fields:
        if field in data:
            update_fields.append(f'{field} = ?')
            update_values.append(data[field])
    
    if not update_fields:
        conn.close()
        return jsonify({'error': 'No valid fields to update'}), 400
    
    update_values.append(appointment_id)
    try:
        conn.execute(f'''
            UPDATE appointments 
            SET {', '.join(update_fields)}
            WHERE id = ?
        ''', update_values)
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Appointment updated successfully'})
        
    except sqlite3.Error as e:
        conn.close()
        return jsonify({'error': 'Database error: ' + str(e)}), 500

@app.route('/api/appointments/<int:appointment_id>', methods=['DELETE'])
@require_auth
def delete_appointment(appointment_id):
    """Delete an appointment"""
    conn = get_db_connection(DATABASE_DATA)
    
    # Check if appointment exists
    appointment = conn.execute('SELECT * FROM appointments WHERE id = ?', (appointment_id,)).fetchone()
    if not appointment:
        conn.close()
        return jsonify({'error': 'Appointment not found'}), 404
    
    try:
        conn.execute('DELETE FROM appointments WHERE id = ?', (appointment_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Appointment deleted successfully'})
        
    except sqlite3.Error as e:
        conn.close()
        return jsonify({'error': 'Database error: ' + str(e)}), 500

# Export endpoints
@app.route('/api/export/patients')
@require_auth
def export_patients():
    """Export patients data as CSV"""
    conn = get_db_connection(DATABASE_PATIENTS)
    patients = conn.execute('''
        SELECT * FROM patients 
        ORDER BY created_at DESC
    ''').fetchall()
    conn.close()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Serial Number', 'Name', 'Phone', 'Age', 'Sex', 'Marital Status', 
                    'Problem', 'Times of Visit', 'Date Added', 'Created At', 'Updated At'])
    
    # Write data
    for patient in patients:
        writer.writerow([
            patient['serial_number'],
            patient['patient_name'],
            patient['phone_number'],
            patient['age'],
            patient['sex'],
            patient['marital_status'],
            patient['problem'],
            patient['times_of_visit'],
            patient['date_added'],
            patient['created_at'],
            patient['updated_at']
        ])
    
    # Create response
    output.seek(0)
    csv_data = output.getvalue()
    output.close()
    
    return app.response_class(
        csv_data,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=patients_data_{datetime.now().strftime("%Y%m%d")}.csv'}
    )

@app.route('/api/export/appointments')
@require_auth
def export_appointments():
    """Export appointments data as CSV"""
    conn = get_db_connection(DATABASE_DATA)
    appointments = conn.execute('''
        SELECT * FROM appointments 
        ORDER BY date, time
    ''').fetchall()
    conn.close()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Date', 'Time', 'Patient Name', 'Phone', 'Duration (min)', 
                    'Notes', 'Status', 'Created At', 'Updated At'])
    
    # Write data
    for appointment in appointments:
        writer.writerow([
            appointment['date'],
            appointment['time'],
            appointment['patient_name'],
            appointment['patient_phone'],
            appointment['duration'],
            appointment['notes'] or '',
            appointment['status'],
            appointment['created_at'],
            appointment['updated_at']
        ])
    
    # Create response
    output.seek(0)
    csv_data = output.getvalue()
    output.close()
    
    return app.response_class(
        csv_data,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=appointments_data_{datetime.now().strftime("%Y%m%d")}.csv'}
    )

# Symptoms API endpoint
@app.route('/api/symptoms', methods=['GET'])
@require_auth
def get_symptoms():
    """Get all predefined symptoms"""
    conn = get_db_connection(DATABASE_DATA)
    symptoms = conn.execute('''
        SELECT * FROM predefined_symptoms 
        WHERE is_active = 1
        ORDER BY category, symptom_name
    ''').fetchall()
    conn.close()
    
    symptoms_list = []
    for symptom in symptoms:
        symptoms_list.append({
            'id': symptom['id'],
            'symptom_name': symptom['symptom_name'],
            'category': symptom['category']
        })
    
    return jsonify({'symptoms': symptoms_list})

# ===============================
# Authentication API Endpoints
# ===============================

@app.route('/api/register', methods=['POST'])
def register_user():
    """Initialize user registration"""
    try:
        data = request.json
        print(f"Registration attempt with data: {data}")  # Debug log
        
        name = data.get('name', '').strip()
        email = data.get('email', '').strip().lower()
        phone = data.get('phone', '').strip()
        designation = data.get('designation', '').strip()
        
        print(f"Parsed data - Name: {name}, Email: {email}, Phone: {phone}, Designation: {designation}")  # Debug log
        
        if not all([name, email, phone, designation]):
            return jsonify({'success': False, 'message': 'All fields are required'})
        
        # Check if email already exists
        conn = get_db_connection(DATABASE_DATA)
        existing_user = conn.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
        
        if existing_user:
            conn.close()
            return jsonify({'success': False, 'message': 'Email already registered'})
        
        # Generate and send OTP
        otp = generate_otp()
        print(f"Generated OTP: {otp} for email: {email}")  # Debug log
        
        # Set OTP expiry to 10 minutes from now
        expires_at = (datetime.now() + timedelta(minutes=10)).strftime('%Y-%m-%d %H:%M:%S')
        
        # Clean up old OTPs and save new one
        cleanup_expired_otps()
        conn.execute('DELETE FROM otp_verification WHERE email = ?', (email,))
        conn.execute('''
            INSERT INTO otp_verification (email, otp_code, expires_at)
            VALUES (?, ?, ?)
        ''', (email, otp, expires_at))
        conn.commit()
        conn.close()
        
        # Send OTP email
        print(f"Attempting to send OTP email to: {email}")  # Debug log
        email_sent = send_otp_email(email, otp, name)
        print(f"Email send result: {email_sent}")  # Debug log
        
        if email_sent:
            return jsonify({'success': True, 'message': 'OTP sent to your email'})
        else:
            return jsonify({'success': False, 'message': 'Failed to send OTP. Please try again.'})
            
    except Exception as e:
        print(f"Registration error: {e}")
        return jsonify({'success': False, 'message': 'Registration failed'})

@app.route('/api/send-otp', methods=['POST'])
def resend_otp():
    """Resend OTP to email"""
    try:
        data = request.json
        email = data.get('email', '').strip().lower()
        
        if not email:
            return jsonify({'success': False, 'message': 'Email is required'})
        
        # Generate new OTP
        otp = generate_otp()
        # Set OTP expiry to 10 minutes from now
        expires_at = (datetime.now() + timedelta(minutes=10)).strftime('%Y-%m-%d %H:%M:%S')
        
        # Update OTP in database
        conn = get_db_connection(DATABASE_DATA)
        conn.execute('DELETE FROM otp_verification WHERE email = ?', (email,))
        conn.execute('''
            INSERT INTO otp_verification (email, otp_code, expires_at)
            VALUES (?, ?, ?)
        ''', (email, otp, expires_at))
        conn.commit()
        conn.close()
        
        # Send OTP email
        if send_otp_email(email, otp):
            return jsonify({'success': True, 'message': 'New OTP sent'})
        else:
            return jsonify({'success': False, 'message': 'Failed to send OTP'})
            
    except Exception as e:
        print(f"Resend OTP error: {e}")
        return jsonify({'success': False, 'message': 'Failed to resend OTP'})

@app.route('/api/verify-otp', methods=['POST'])
def verify_otp():
    """Verify OTP code"""
    try:
        data = request.json
        email = data.get('email', '').strip().lower()
        otp_code = data.get('otp', '').strip()
        
        if not email or not otp_code:
            return jsonify({'success': False, 'message': 'Email and OTP are required'})
        
        conn = get_db_connection(DATABASE_DATA)
        
        # Check if OTP exists and is valid
        otp_record = conn.execute('''
            SELECT * FROM otp_verification 
            WHERE email = ? AND otp_code = ? AND expires_at > datetime('now') AND is_used = 0
        ''', (email, otp_code)).fetchone()
        
        if otp_record:
            # Mark OTP as used
            conn.execute('UPDATE otp_verification SET is_used = 1 WHERE id = ?', (otp_record['id'],))
            conn.commit()
            conn.close()
            return jsonify({'success': True, 'message': 'OTP verified successfully'})
        else:
            conn.close()
            return jsonify({'success': False, 'message': 'Invalid or expired OTP'})
            
    except Exception as e:
        print(f"OTP verification error: {e}")
        return jsonify({'success': False, 'message': 'OTP verification failed'})

@app.route('/api/complete-registration', methods=['POST'])
def complete_registration():
    """Complete user registration with password"""
    try:
        data = request.json
        name = data.get('name', '').strip()
        email = data.get('email', '').strip().lower()
        phone = data.get('phone', '').strip()
        designation = data.get('designation', '').strip()
        password = data.get('password', '').strip()
        
        if not all([name, email, phone, designation, password]):
            return jsonify({'success': False, 'message': 'All fields are required'})
        
        if len(password) < 8:
            return jsonify({'success': False, 'message': 'Password must be at least 8 characters'})
        
        # Hash password
        password_hash = hash_password(password)
        
        # Create user account
        conn = get_db_connection(DATABASE_DATA)
        
        # Check if email already exists
        existing_user = conn.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
        if existing_user:
            conn.close()
            return jsonify({'success': False, 'message': 'Email already registered'})
        
        # Insert new user
        conn.execute('''
            INSERT INTO users (name, email, phone, designation, password_hash, email_verified)
            VALUES (?, ?, ?, ?, ?, 1)
        ''', (name, email, phone, designation, password_hash))
        
        # Clean up OTP records for this email
        conn.execute('DELETE FROM otp_verification WHERE email = ?', (email,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Registration completed successfully'})
        
    except Exception as e:
        print(f"Complete registration error: {e}")
        return jsonify({'success': False, 'message': 'Registration completion failed'})

@app.route('/api/login', methods=['POST'])
def login_user():
    """User login - supports email, phone, or username"""
    try:
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            return jsonify({'success': False, 'message': 'Username/Email/Phone and password are required'})
        
        # Check if it's the default admin login
        if username == 'admin' and password == 'password':
            return jsonify({
                'success': True, 
                'user': {
                    'id': 0,
                    'name': 'Administrator',
                    'email': 'admin@hospital.com',
                    'designation': 'Administrator'
                }
            })
        
        # Check registered users - allow login with email, phone, or name
        conn = get_db_connection(DATABASE_DATA)
        
        # Enhanced query to support multiple login methods
        user = conn.execute('''
            SELECT * FROM users 
            WHERE (
                LOWER(email) = LOWER(?) OR 
                phone = ? OR 
                LOWER(name) = LOWER(?)
            ) AND is_active = 1
        ''', (username, username, username)).fetchone()
        
        if user and verify_password(password, user['password_hash']):
            conn.close()
            return jsonify({
                'success': True,
                'user': {
                    'id': user['id'],
                    'name': user['name'],
                    'email': user['email'],
                    'designation': user['designation']
                },
                'message': f'Welcome back, {user["name"]}!'
            })
        else:
            conn.close()
            return jsonify({'success': False, 'message': 'Invalid credentials. Please check your email/phone/username and password.'})
            
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'success': False, 'message': 'Login failed'})

@app.route('/send_reset_otp', methods=['POST'])
def send_reset_otp():
    """Send OTP for password reset"""
    try:
        data = request.json
        email = data.get('email', '').strip().lower()
        
        print(f"=== RESET OTP REQUEST ===")
        print(f"Received email: {email}")
        
        if not email:
            print("Error: Email is empty")
            return jsonify({'success': False, 'message': 'Email is required'})
        
        # Check if user exists
        conn = get_db_connection(DATABASE_DATA)
        print(f"Database connection established: {DATABASE_DATA}")
        
        user = conn.execute('''
            SELECT * FROM users WHERE LOWER(email) = ? AND is_active = 1
        ''', (email,)).fetchone()
        
        print(f"User found: {user is not None}")
        if user:
            print(f"User details: {dict(user) if user else 'None'}")
        
        if not user:
            conn.close()
            print("Error: User not found or inactive")
            return jsonify({'success': False, 'message': 'Email not found. Please check your email address.'})
        
        # Generate OTP
        otp = generate_otp()
        expiry_time = datetime.now() + timedelta(minutes=10)
        
        print(f"Generated OTP: {otp}")
        print(f"OTP expiry time: {expiry_time}")
        
        # Store OTP in database (update or insert)
        conn.execute('''
            INSERT OR REPLACE INTO otps (email, otp, expiry_time, created_at)
            VALUES (?, ?, ?, ?)
        ''', (email, otp, expiry_time, datetime.now()))
        conn.commit()
        print("OTP stored in database")
        conn.close()
        
        # Send OTP email
        print("Attempting to send email...")
        send_reset_otp_email(email, otp, user['name'])
        print("Email sending completed")
        return jsonify({'success': True, 'message': 'Reset code sent to your email!'})
        
    except Exception as e:
        print(f"=== RESET OTP ERROR ===")
        print(f"Send reset OTP error: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'message': 'Failed to send reset code'})

@app.route('/verify_reset_otp', methods=['POST'])
def verify_reset_otp():
    """Verify OTP for password reset"""
    try:
        data = request.json
        email = data.get('email', '').strip().lower()
        otp = data.get('otp', '').strip()
        
        if not email or not otp:
            return jsonify({'success': False, 'message': 'Email and OTP are required'})
        
        # Check OTP validity
        conn = get_db_connection(DATABASE_DATA)
        otp_record = conn.execute('''
            SELECT * FROM otps 
            WHERE email = ? AND otp = ? AND expiry_time > ?
        ''', (email, otp, datetime.now())).fetchone()
        
        if otp_record:
            conn.close()
            return jsonify({'success': True, 'message': 'OTP verified successfully!'})
        else:
            conn.close()
            return jsonify({'success': False, 'message': 'Invalid or expired OTP. Please try again.'})
            
    except Exception as e:
        print(f"Verify reset OTP error: {e}")
        return jsonify({'success': False, 'message': 'OTP verification failed'})

@app.route('/reset_password', methods=['POST'])
def reset_password():
    """Reset user password"""
    try:
        data = request.json
        email = data.get('email', '').strip().lower()
        otp = data.get('otp', '').strip()
        new_password = data.get('new_password', '').strip()
        
        if not email or not otp or not new_password:
            return jsonify({'success': False, 'message': 'Email, OTP, and new password are required'})
        
        if len(new_password) < 6:
            return jsonify({'success': False, 'message': 'Password must be at least 6 characters long'})
        
        # Verify OTP one more time
        conn = get_db_connection(DATABASE_DATA)
        otp_record = conn.execute('''
            SELECT * FROM otps 
            WHERE email = ? AND otp = ? AND expiry_time > ?
        ''', (email, otp, datetime.now())).fetchone()
        
        if not otp_record:
            conn.close()
            return jsonify({'success': False, 'message': 'Invalid or expired OTP. Please start over.'})
        
        # Update user password
        hashed_password = hash_password(new_password)
        conn.execute('''
            UPDATE users SET password_hash = ? WHERE LOWER(email) = ?
        ''', (hashed_password, email))
        
        # Delete used OTP
        conn.execute('DELETE FROM otps WHERE email = ? AND otp = ?', (email, otp))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Password reset successfully!'})
        
    except Exception as e:
        print(f"Reset password error: {e}")
        return jsonify({'success': False, 'message': 'Password reset failed'})

def send_reset_otp_email(email, otp, name="User"):
    """Send password reset OTP via email"""
    try:
        # Create HTML content for password reset
        html = f"""
        <html>
          <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f4f4f4;">
            <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
              <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #2c3e50; margin: 0;">🔒 Password Reset</h1>
                <h2 style="color: #3498db; margin: 10px 0 0 0;">Kalpana Medcare</h2>
              </div>
              
              <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                <h3 style="color: white; margin: 0 0 10px 0; text-align: center;">Hello {name}!</h3>
                <p style="color: white; margin: 0; text-align: center; font-size: 16px;">
                  You requested to reset your password. Use the code below to proceed:
                </p>
              </div>
              
              <div style="text-align: center; margin: 30px 0;">
                <div style="background: #f8f9fa; border: 2px dashed #007bff; border-radius: 8px; padding: 20px; display: inline-block;">
                  <p style="margin: 0 0 10px 0; color: #666; font-size: 14px;">Your Reset Code:</p>
                  <h2 style="margin: 0; color: #007bff; font-size: 32px; letter-spacing: 5px; font-family: monospace;">
                    {otp}
                  </h2>
                </div>
              </div>
              
              <div style="background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px; padding: 15px; margin-bottom: 20px;">
                <p style="margin: 0; color: #856404; font-size: 14px;">
                  <strong>⚠️ Important:</strong> This code will expire in 10 minutes. If you didn't request this reset, please ignore this email.
                </p>
              </div>
              
              <div style="text-align: center; padding-top: 20px; border-top: 1px solid #eee;">
                <p style="margin: 0; color: #666; font-size: 12px;">
                  This is an automated message from Kalpana Medcare Healthcare Management System.
                </p>
              </div>
            </div>
          </body>
        </html>
        """
        
        # Create and send message
        msg = Message(
            subject=f'🔒 Password Reset Code - {otp}',
            recipients=[email],
            html=html
        )
        
        mail.send(msg)
        print(f"Password reset OTP sent to {email}: {otp}")
        
    except Exception as e:
        print(f"Failed to send password reset email to {email}: {e}")
        # Fallback to console output for development
        print(f"=== PASSWORD RESET EMAIL (Console Output) ===")
        print(f"To: {email}")
        print(f"Subject: Password Reset Code - {otp}")
        print(f"Reset Code: {otp}")
        print(f"Name: {name}")
        print(f"===================================")

@app.route('/test_forgot_password')
def test_forgot_password():
    """Test the forgot password functionality directly"""
    try:
        print("=== TESTING FORGOT PASSWORD ===")
        
        # Simulate the request
        from flask import g
        email = 'test@example.com'
        
        print(f"Testing with email: {email}")
        
        # Check if user exists
        conn = get_db_connection(DATABASE_DATA)
        print(f"Database connection established: {DATABASE_DATA}")
        
        user = conn.execute('''
            SELECT * FROM users WHERE LOWER(email) = ? AND is_active = 1
        ''', (email.lower(),)).fetchone()
        
        print(f"User found: {user is not None}")
        if user:
            print(f"User details: {dict(user)}")
        
        if not user:
            conn.close()
            return jsonify({'success': False, 'message': 'User not found'})
        
        # Generate OTP
        otp = generate_otp()
        expiry_time = datetime.now() + timedelta(minutes=10)
        
        print(f"Generated OTP: {otp}")
        print(f"OTP expiry time: {expiry_time}")
        
        # Store OTP in database
        conn.execute('''
            INSERT OR REPLACE INTO otps (email, otp, expiry_time, created_at)
            VALUES (?, ?, ?, ?)
        ''', (email, otp, expiry_time, datetime.now()))
        conn.commit()
        print("OTP stored in database")
        conn.close()
        
        # Test email sending
        print("Testing email sending...")
        send_reset_otp_email(email, otp, user['name'])
        print("Email sending completed")
        
        return jsonify({'success': True, 'message': f'Test completed! OTP: {otp}'})
        
    except Exception as e:
        print(f"=== TEST ERROR ===")
        print(f"Error: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'message': f'Test failed: {e}'})

@app.route('/create_test_user')
def create_test_user():
    """Create a test user for forgot password testing"""
    try:
        conn = get_db_connection(DATABASE_DATA)
        
        # Check if test user already exists
        existing_user = conn.execute('''
            SELECT * FROM users WHERE email = ?
        ''', ('test@example.com',)).fetchone()
        
        if existing_user:
            conn.close()
            return jsonify({'success': True, 'message': 'Test user already exists'})
        
        # Create test user
        hashed_password = hash_password('testpass123')
        conn.execute('''
            INSERT INTO users (name, email, phone, designation, password_hash, email_verified, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('Test User', 'test@example.com', '1234567890', 'Doctor', hashed_password, 1, 1))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Test user created successfully! Email: test@example.com, Password: testpass123'})
        
    except Exception as e:
        print(f"Error creating test user: {e}")
        return jsonify({'success': False, 'message': f'Error: {e}'})

if __name__ == '__main__':
    # Initialize Flask-Mail
    mail.init_app(app)
    
    # Initialize databases on startup
    init_databases()
    
    # Run the application
    app.run(debug=True, host='0.0.0.0', port=5000)
