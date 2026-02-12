from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import config
import json
import os
import uuid
from datetime import datetime
from functools import wraps
import firebase_db as fdb

app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx'}
MAX_FILE_SIZE = 5 * 1024 * 1024

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

fdb.init_firebase()

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            if request.path.startswith('/api/'):
                return jsonify({'success': False, 'error': 'Unauthorized'}), 401
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def super_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in') or not session.get('is_super_admin'):
            if request.path.startswith('/api/'):
                return jsonify({'success': False, 'error': 'Super admin access required'}), 403
            return redirect(url_for('admin_panel'))
        return f(*args, **kwargs)
    return decorated_function

def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('student_logged_in'):
            if request.path.startswith('/api/'):
                return jsonify({'success': False, 'error': 'Student login required'}), 401
            return redirect(url_for('student_login'))
        return f(*args, **kwargs)
    return decorated_function

def init_sample_data():
    try:
        scholarships = fdb.ScholarshipDB.get_all()
        if scholarships:
            return
    except:
        pass
    
    merit_id, _ = fdb.ScholarshipDB.create(
        name="Merit Excellence Scholarship",
        description="For students with outstanding academic performance",
        amount=50000.00,
        is_active=True
    )
    
    fdb.RuleDB.create(merit_id, 'marks_percentage', '>=', '85', 1.5, 'Minimum marks requirement', 'Marks below 85%')
    fdb.RuleDB.create(merit_id, 'has_backlogs', '==', 'false', 1.0, 'No backlogs allowed', 'Active backlogs found')
    fdb.RuleDB.create(merit_id, 'is_full_time', '==', 'true', 1.0, 'Must be full-time student', 'Not a full-time student')
    
    need_id, _ = fdb.ScholarshipDB.create(
        name="Financial Assistance Scholarship",
        description="For students from economically weaker sections",
        amount=75000.00,
        is_active=True
    )
    
    fdb.RuleDB.create(need_id, 'marks_percentage', '>=', '75', 1.0, 'Minimum marks requirement', 'Marks below 75%')
    fdb.RuleDB.create(need_id, 'family_income', '<=', '250000', 2.0, 'Family income limit', 'Family income exceeds ₹2,50,000')
    fdb.RuleDB.create(need_id, 'has_backlogs', '==', 'false', 1.0, 'No backlogs allowed', 'Active backlogs found')
    fdb.RuleDB.create(need_id, 'is_full_time', '==', 'true', 1.0, 'Must be full-time student', 'Not a full-time student')
    
    print("Sample scholarships initialized!")

@app.route('/')
def index():
    if session.get('student_logged_in'):
        student = fdb.StudentDB.get_by_id(session.get('student_id'))
        return render_template('index.html', student=student, logged_in=True)
    return render_template('index.html', logged_in=False)

@app.route('/student/login', methods=['GET'])
def student_login():
    if session.get('student_logged_in'):
        return redirect(url_for('index'))
    return render_template('student_login.html')

@app.route('/student/login', methods=['POST'])
def student_login_submit():
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    
    if not email or not password:
        return render_template('student_login.html', error='Email and password are required')
    
    student = fdb.StudentDB.get_by_email(email)
    
    if not student or not check_password_hash(student['password'], password):
        return render_template('student_login.html', error='Invalid email or password')
    
    session['student_logged_in'] = True
    session['student_id'] = student['id']
    session['student_email'] = student['email']
    session['student_name'] = student['name']
    
    fdb.StudentDB.update(student['id'], {'last_login': fdb.to_timestamp()})
    
    return redirect(url_for('index'))

@app.route('/student/register', methods=['GET'])
def student_register():
    if session.get('student_logged_in'):
        return redirect(url_for('index'))
    return render_template('student_register.html')

@app.route('/student/register', methods=['POST'])
def student_register_submit():
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    
    if not name or not email or not password:
        return render_template('student_register.html', error='All fields are required')
    
    if fdb.StudentDB.get_by_email(email):
        return render_template('student_register.html', error='Email already registered as student')
    
    if fdb.AdminDB.get_by_email(email):
        return render_template('student_register.html', error='Email already registered as admin')
    
    student_id, student = fdb.StudentDB.create(
        email=email,
        password=generate_password_hash(password),
        name=name
    )
    
    session['student_logged_in'] = True
    session['student_id'] = student_id
    session['student_email'] = email
    session['student_name'] = name
    
    fdb.StudentDB.update(student_id, {'last_login': fdb.to_timestamp()})
    
    return redirect(url_for('index'))

@app.route('/student/logout')
def student_logout():
    session.pop('student_logged_in', None)
    session.pop('student_id', None)
    session.pop('student_email', None)
    session.pop('student_name', None)
    return redirect(url_for('index'))

@app.route('/student/my-applications')
@student_required
def my_applications():
    return render_template('my_applications.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/admin')
@admin_required
def admin_panel():
    unread_count = fdb.ApplicationDB.count_unread()
    
    admin_info = {
        'name': session.get('admin_name', 'Admin'),
        'email': session.get('admin_email', ''),
        'is_super_admin': session.get('is_super_admin', False),
        'unread_applications': unread_count
    }
    return render_template('admin.html', admin_info=admin_info)

@app.route('/admin/applications')
@admin_required
def admin_applications():
    return render_template('admin_applications.html')

@app.route('/admin/login', methods=['GET'])
def admin_login():
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_panel'))
    return render_template('admin_login.html')

@app.route('/admin/login', methods=['POST'])
def admin_login_submit():
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    
    if not email or not password:
        return render_template('admin_login.html', error='Email and password are required')
    
    admin = fdb.AdminDB.get_by_email(email)
    
    if not admin or not check_password_hash(admin['password'], password):
        return render_template('admin_login.html', error='Invalid email or password')
    
    if not admin['is_approved']:
        return render_template('admin_login.html', error='Your account is pending approval')
    
    session['admin_logged_in'] = True
    session['admin_id'] = admin['id']
    session['admin_email'] = admin['email']
    session['admin_name'] = admin['name']
    session['is_super_admin'] = admin['is_super_admin']
    
    fdb.AdminDB.update(admin['id'], {'last_login': fdb.to_timestamp()})
    
    return redirect(url_for('admin_panel'))

@app.route('/admin/register', methods=['GET'])
def admin_register():
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_panel'))
    return render_template('admin_register.html')

@app.route('/admin/register', methods=['POST'])
def admin_register_submit():
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    
    if not name or not email or not password:
        return render_template('admin_register.html', error='All fields are required')
    
    if fdb.AdminDB.get_by_email(email):
        return render_template('admin_register.html', error='Email already registered as admin')
    
    if fdb.StudentDB.get_by_email(email):
        return render_template('admin_register.html', error='Email already registered as student')
    
    is_first_admin = fdb.AdminDB.count() == 0
    
    admin_id, admin = fdb.AdminDB.create(
        email=email,
        password=generate_password_hash(password),
        name=name,
        is_super_admin=is_first_admin
    )
    
    if is_first_admin:
        session['admin_logged_in'] = True
        session['admin_id'] = admin_id
        session['admin_email'] = email
        session['admin_name'] = name
        session['is_super_admin'] = True
        fdb.AdminDB.update(admin_id, {'last_login': fdb.to_timestamp()})
        return redirect(url_for('admin_panel'))
    
    return render_template('admin_login.html', success='Registration successful! Please wait for admin approval')

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/admin/users')
@admin_required
@super_admin_required
def admin_users():
    return render_template('admin_users.html')

@app.route('/results/<student_id>')
def results_page(student_id):
    return render_template('results.html', student_id=student_id)

@app.route('/api/admin/users', methods=['GET'])
@admin_required
@super_admin_required
def get_admin_users():
    admins = fdb.AdminDB.get_all()
    return jsonify({'success': True, 'admins': admins})

@app.route('/api/admin/users/<admin_id>/approve', methods=['POST'])
@admin_required
@super_admin_required
def approve_admin(admin_id):
    admin = fdb.AdminDB.get_by_id(admin_id)
    if not admin:
        return jsonify({'success': False, 'error': 'Admin not found'}), 404
    
    fdb.AdminDB.update(admin_id, {'is_approved': True})
    return jsonify({'success': True, 'message': f'{admin["name"]} has been approved'})

@app.route('/api/admin/users/<admin_id>/revoke', methods=['POST'])
@admin_required
@super_admin_required
def revoke_admin(admin_id):
    if admin_id == session.get('admin_id'):
        return jsonify({'success': False, 'error': 'Cannot revoke your own access'}), 400
    
    admin = fdb.AdminDB.get_by_id(admin_id)
    if not admin:
        return jsonify({'success': False, 'error': 'Admin not found'}), 404
    
    fdb.AdminDB.update(admin_id, {'is_approved': False})
    return jsonify({'success': True, 'message': f'{admin["name"]} access has been revoked'})

@app.route('/api/admin/users/<admin_id>', methods=['DELETE'])
@admin_required
@super_admin_required
def delete_admin(admin_id):
    if admin_id == session.get('admin_id'):
        return jsonify({'success': False, 'error': 'Cannot delete your own account'}), 400
    
    fdb.AdminDB.delete(admin_id)
    return jsonify({'success': True, 'message': 'Admin deleted successfully'})

@app.route('/api/students', methods=['GET'])
def get_students():
    students = fdb.StudentDB.get_all()
    return jsonify({'success': True, 'students': students, 'count': len(students)})

@app.route('/api/students/<student_id>', methods=['GET'])
def get_student(student_id):
    student = fdb.StudentDB.get_by_id(student_id)
    if not student:
        return jsonify({'success': False, 'error': 'Student not found'}), 404
    return jsonify({'success': True, 'student': student})

@app.route('/api/students', methods=['POST'])
def create_student():
    try:
        data = request.get_json()
        required_fields = ['name', 'email', 'course', 'year_of_study', 'marks_percentage', 'family_income', 'category']
        
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        if session.get('student_logged_in'):
            student_id = session.get('student_id')
            fdb.StudentDB.update(student_id, {
                'name': data['name'],
                'course': data['course'],
                'year_of_study': int(data['year_of_study']),
                'marks_percentage': float(data['marks_percentage']),
                'family_income': float(data['family_income']),
                'category': data['category'],
                'has_backlogs': data.get('has_backlogs', False),
                'is_full_time': data.get('is_full_time', True),
                'is_registered': True
            })
            
            student = fdb.StudentDB.get_by_id(student_id)
            return jsonify({'success': True, 'message': 'Profile updated successfully', 'student': student}), 200
        
        if fdb.StudentDB.get_by_email(data['email']):
            return jsonify({'success': False, 'error': 'A student with this email already exists. Please login first.'}), 400
        
        student_id, student = fdb.StudentDB.create(
            email=data['email'],
            password=generate_password_hash('default123'),
            name=data['name']
        )
        
        fdb.StudentDB.update(student_id, {
            'course': data['course'],
            'year_of_study': int(data['year_of_study']),
            'marks_percentage': float(data['marks_percentage']),
            'family_income': float(data['family_income']),
            'category': data['category'],
            'has_backlogs': data.get('has_backlogs', False),
            'is_full_time': data.get('is_full_time', True),
            'is_registered': True
        })
        
        student = fdb.StudentDB.get_by_id(student_id)
        return jsonify({'success': True, 'message': 'Student application submitted successfully', 'student': student}), 201
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/students/<student_id>', methods=['DELETE'])
def delete_student(student_id):
    fdb.EligibilityResultDB.delete_by_student(student_id)
    fdb.StudentDB.delete(student_id)
    return jsonify({'success': True, 'message': 'Student deleted successfully'})

@app.route('/api/scholarships', methods=['GET'])
def get_scholarships():
    scholarships = fdb.ScholarshipDB.get_all()
    return jsonify({'success': True, 'scholarships': scholarships, 'count': len(scholarships)})

@app.route('/api/scholarships/<scholarship_id>', methods=['GET'])
def get_scholarship(scholarship_id):
    scholarship = fdb.ScholarshipDB.get_by_id(scholarship_id)
    if not scholarship:
        return jsonify({'success': False, 'error': 'Scholarship not found'}), 404
    return jsonify({'success': True, 'scholarship': scholarship})

@app.route('/api/scholarships', methods=['POST'])
@admin_required
def create_scholarship():
    try:
        data = request.get_json()
        scholarship_id, scholarship = fdb.ScholarshipDB.create(
            name=data['name'],
            description=data.get('description', ''),
            amount=float(data['amount']),
            is_active=data.get('is_active', True)
        )
        return jsonify({'success': True, 'message': 'Scholarship created successfully', 'scholarship': scholarship}), 201
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/scholarships/<scholarship_id>', methods=['PUT'])
@admin_required
def update_scholarship(scholarship_id):
    data = request.get_json()
    fdb.ScholarshipDB.update(scholarship_id, {
        'name': data.get('name'),
        'description': data.get('description'),
        'amount': float(data.get('amount')),
        'is_active': data.get('is_active')
    })
    scholarship = fdb.ScholarshipDB.get_by_id(scholarship_id)
    return jsonify({'success': True, 'message': 'Scholarship updated successfully', 'scholarship': scholarship})

@app.route('/api/scholarships/<scholarship_id>', methods=['DELETE'])
@admin_required
def delete_scholarship(scholarship_id):
    fdb.ScholarshipDB.delete(scholarship_id)
    return jsonify({'success': True, 'message': 'Scholarship deleted successfully'})

@app.route('/api/rules', methods=['POST'])
@admin_required
def create_rule():
    try:
        data = request.get_json()
        rule_id, rule = fdb.RuleDB.create(
            scholarship_id=data['scholarship_id'],
            field=data['field'],
            operator=data['operator'],
            value=data['value'],
            weight=float(data.get('weight', 1.0)),
            description=data.get('description', ''),
            error_message=data.get('error_message', '')
        )
        return jsonify({'success': True, 'message': 'Rule created successfully', 'rule': rule}), 201
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/rules/<rule_id>', methods=['PUT'])
@admin_required
def update_rule(rule_id):
    data = request.get_json()
    fdb.RuleDB.update(rule_id, data)
    rule = fdb.RuleDB.get_by_id(rule_id)
    return jsonify({'success': True, 'message': 'Rule updated successfully', 'rule': rule})

@app.route('/api/rules/<rule_id>', methods=['DELETE'])
@admin_required
def delete_rule(rule_id):
    fdb.RuleDB.delete(rule_id)
    return jsonify({'success': True, 'message': 'Rule deleted successfully'})

@app.errorhandler(404)
def not_found(error):
    if request.path.startswith('/api/'):
        return jsonify({'success': False, 'error': 'Resource not found'}), 404
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(error):
    if request.path.startswith('/api/'):
        return jsonify({'success': False, 'error': 'Internal server error'}), 500
    return render_template('500.html'), 500

if __name__ == '__main__':
    init_sample_data()
    
    print("\n" + "="*50)
    print("Scholarship Eligibility Filter")
    print("="*50)
    print("Server starting at: http://localhost:5000")
    print("Admin Panel: http://localhost:5000/admin")
    print("="*50 + "\n")
    
    app.run(debug=True, port=5000)
