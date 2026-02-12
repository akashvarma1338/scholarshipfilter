"""
Main Flask Application for Scholarship Eligibility Filter
This file contains all the routes and API endpoints for the application.
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_from_directory
from models import db, Student, Scholarship, Rule, EligibilityResult, Admin, ScholarshipApplication, ApplicationDocument
from rules_engine import rules_engine
from werkzeug.utils import secure_filename
import config
import json
import requests
import hashlib
import os
import uuid
from datetime import datetime
from functools import wraps

# Initialize Flask application
app = Flask(__name__)

# Load configuration
app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = config.SQLALCHEMY_TRACK_MODIFICATIONS
app.config['SECRET_KEY'] = config.SECRET_KEY

# File upload configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Create uploads folder if not exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Initialize database with app
db.init_app(app)


# =====================================================
# GOOGLE OAUTH CONFIGURATION
# =====================================================

def get_google_provider_cfg():
    """Fetch Google's OAuth 2.0 configuration"""
    try:
        return requests.get(config.GOOGLE_DISCOVERY_URL).json()
    except:
        return None


def admin_required(f):
    """Decorator to require admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            if request.path.startswith('/api/'):
                return jsonify({'success': False, 'error': 'Unauthorized'}), 401
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function


def super_admin_required(f):
    """Decorator to require super admin privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in') or not session.get('is_super_admin'):
            if request.path.startswith('/api/'):
                return jsonify({'success': False, 'error': 'Super admin access required'}), 403
            return redirect(url_for('admin_panel'))
        return f(*args, **kwargs)
    return decorated_function


def student_required(f):
    """Decorator to require student authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('student_logged_in'):
            if request.path.startswith('/api/'):
                return jsonify({'success': False, 'error': 'Student login required'}), 401
            return redirect(url_for('student_login'))
        return f(*args, **kwargs)
    return decorated_function


# =====================================================
# HELPER FUNCTIONS
# =====================================================

def init_sample_data():
    """
    Initialize sample scholarships and rules for demonstration.
    This function creates default scholarships if none exist.
    """
    # Check if scholarships already exist
    if Scholarship.query.first() is not None:
        return
    
    # Create Merit-Based Scholarship
    merit_scholarship = Scholarship(
        name="Merit Excellence Scholarship",
        description="For students with outstanding academic performance",
        amount=50000.00,
        is_active=True
    )
    db.session.add(merit_scholarship)
    db.session.flush()  # Get the ID
    
    # Add rules for Merit Scholarship
    merit_rules = [
        Rule(
            scholarship_id=merit_scholarship.id,
            field='marks_percentage',
            operator='>=',
            value='85',
            weight=1.5,
            description='Minimum marks requirement',
            error_message='Marks below 85% - Merit scholarship requires 85% or above'
        ),
        Rule(
            scholarship_id=merit_scholarship.id,
            field='has_backlogs',
            operator='==',
            value='false',
            weight=1.0,
            description='No backlogs allowed',
            error_message='Active backlogs found - No backlogs allowed for this scholarship'
        ),
        Rule(
            scholarship_id=merit_scholarship.id,
            field='is_full_time',
            operator='==',
            value='true',
            weight=1.0,
            description='Must be full-time student',
            error_message='Not a full-time student - Only full-time students are eligible'
        )
    ]
    for rule in merit_rules:
        db.session.add(rule)
    
    # Create Need-Based Scholarship
    need_scholarship = Scholarship(
        name="Financial Assistance Scholarship",
        description="For students from economically weaker sections",
        amount=75000.00,
        is_active=True
    )
    db.session.add(need_scholarship)
    db.session.flush()
    
    # Add rules for Need-Based Scholarship
    need_rules = [
        Rule(
            scholarship_id=need_scholarship.id,
            field='marks_percentage',
            operator='>=',
            value='75',
            weight=1.0,
            description='Minimum marks requirement',
            error_message='Marks below 75% - Minimum 75% marks required'
        ),
        Rule(
            scholarship_id=need_scholarship.id,
            field='family_income',
            operator='<=',
            value='250000',
            weight=2.0,
            description='Family income limit',
            error_message='Family income exceeds ₹2,50,000 - Income must be ≤ ₹2,50,000'
        ),
        Rule(
            scholarship_id=need_scholarship.id,
            field='has_backlogs',
            operator='==',
            value='false',
            weight=1.0,
            description='No backlogs allowed',
            error_message='Active backlogs found - No backlogs allowed'
        ),
        Rule(
            scholarship_id=need_scholarship.id,
            field='is_full_time',
            operator='==',
            value='true',
            weight=1.0,
            description='Must be full-time student',
            error_message='Not a full-time student - Only full-time students are eligible'
        )
    ]
    for rule in need_rules:
        db.session.add(rule)
    
    # Create SC/ST Scholarship
    scst_scholarship = Scholarship(
        name="SC/ST Welfare Scholarship",
        description="Special scholarship for SC/ST category students",
        amount=60000.00,
        is_active=True
    )
    db.session.add(scst_scholarship)
    db.session.flush()
    
    # Add rules for SC/ST Scholarship
    scst_rules = [
        Rule(
            scholarship_id=scst_scholarship.id,
            field='marks_percentage',
            operator='>=',
            value='60',
            weight=1.0,
            description='Minimum marks requirement',
            error_message='Marks below 60% - Minimum 60% marks required'
        ),
        Rule(
            scholarship_id=scst_scholarship.id,
            field='category',
            operator='in',
            value='SC,ST',
            weight=1.0,
            description='Category requirement',
            error_message='Not in SC/ST category - This scholarship is only for SC/ST students'
        ),
        Rule(
            scholarship_id=scst_scholarship.id,
            field='family_income',
            operator='<=',
            value='300000',
            weight=1.5,
            description='Family income limit',
            error_message='Family income exceeds ₹3,00,000'
        ),
        Rule(
            scholarship_id=scst_scholarship.id,
            field='is_full_time',
            operator='==',
            value='true',
            weight=1.0,
            description='Must be full-time student',
            error_message='Not a full-time student'
        )
    ]
    for rule in scst_rules:
        db.session.add(rule)
    
    # Create General Scholarship (Basic eligibility)
    general_scholarship = Scholarship(
        name="General Academic Scholarship",
        description="Basic scholarship for all eligible students",
        amount=25000.00,
        is_active=True
    )
    db.session.add(general_scholarship)
    db.session.flush()
    
    # Add rules for General Scholarship
    general_rules = [
        Rule(
            scholarship_id=general_scholarship.id,
            field='marks_percentage',
            operator='>=',
            value='75',
            weight=1.0,
            description='Minimum marks requirement',
            error_message='Marks below 75% - Minimum 75% marks required'
        ),
        Rule(
            scholarship_id=general_scholarship.id,
            field='family_income',
            operator='<=',
            value='250000',
            weight=1.5,
            description='Family income limit',
            error_message='Family income exceeds ₹2,50,000 - Income must be ≤ ₹2,50,000'
        ),
        Rule(
            scholarship_id=general_scholarship.id,
            field='has_backlogs',
            operator='==',
            value='false',
            weight=1.0,
            description='No backlogs allowed',
            error_message='Active backlogs found - No backlogs allowed'
        ),
        Rule(
            scholarship_id=general_scholarship.id,
            field='is_full_time',
            operator='==',
            value='true',
            weight=1.0,
            description='Must be full-time student',
            error_message='Not a full-time student - Only full-time students are eligible'
        )
    ]
    for rule in general_rules:
        db.session.add(rule)
    
    db.session.commit()
    print("Sample scholarships and rules initialized successfully!")


# =====================================================
# MAIN ROUTES (Frontend Pages)
# =====================================================

@app.route('/')
def index():
    """Home page - Shows login option or student form if logged in"""
    if session.get('student_logged_in'):
        student = Student.query.get(session.get('student_id'))
        return render_template('index.html', student=student, logged_in=True)
    return render_template('index.html', logged_in=False)


@app.route('/student/login')
def student_login():
    """Student login page"""
    if session.get('student_logged_in'):
        return redirect(url_for('index'))
    return render_template('student_login.html')


@app.route('/student/google/login')
def student_google_login():
    """Initiate Google OAuth login flow for students"""
    session['oauth_type'] = 'student'
    
    # Check if using simulated auth for students (separate from admin)
    if getattr(config, 'USE_SIMULATED_AUTH_STUDENT', getattr(config, 'USE_SIMULATED_AUTH', False)):
        return redirect(url_for('student_simulated_auth'))
    
    # Build the Google OAuth URL
    google_provider_cfg = get_google_provider_cfg()
    if not google_provider_cfg:
        return render_template('student_login.html', error='Could not connect to Google. Please try again.')
    
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]
    redirect_uri = url_for('student_google_callback', _external=True)
    
    auth_url = (
        f"{authorization_endpoint}?"
        f"client_id={config.GOOGLE_CLIENT_ID}&"
        f"redirect_uri={redirect_uri}&"
        f"scope=openid%20email%20profile&"
        f"response_type=code&"
        f"access_type=offline&"
        f"prompt=consent"
    )
    
    return redirect(auth_url)


@app.route('/student/google/callback')
def student_google_callback():
    """Handle Google OAuth callback for students"""
    code = request.args.get('code')
    if not code:
        return redirect(url_for('student_login'))
    
    google_provider_cfg = get_google_provider_cfg()
    if not google_provider_cfg:
        return render_template('student_login.html', error='Could not connect to Google.')
    
    token_endpoint = google_provider_cfg["token_endpoint"]
    redirect_uri = url_for('student_google_callback', _external=True)
    
    token_response = requests.post(
        token_endpoint,
        data={
            'code': code,
            'client_id': config.GOOGLE_CLIENT_ID,
            'client_secret': config.GOOGLE_CLIENT_SECRET,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }
    )
    
    if token_response.status_code != 200:
        return render_template('student_login.html', error='Failed to authenticate with Google.')
    
    tokens = token_response.json()
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    userinfo_response = requests.get(
        userinfo_endpoint,
        headers={'Authorization': f'Bearer {tokens["access_token"]}'}
    )
    
    if userinfo_response.status_code != 200:
        return render_template('student_login.html', error='Failed to get user info from Google.')
    
    userinfo = userinfo_response.json()
    google_id = userinfo.get('sub')
    email = userinfo.get('email')
    name = userinfo.get('name', email.split('@')[0])
    picture = userinfo.get('picture', '')
    
    # Check if student already exists
    student = Student.query.filter_by(google_id=google_id).first()
    
    if not student:
        # Check if email exists
        student = Student.query.filter_by(email=email).first()
        if student:
            # Update existing student with Google ID
            student.google_id = google_id
            student.profile_picture = picture
        else:
            # Create new student
            student = Student(
                google_id=google_id,
                email=email,
                name=name,
                profile_picture=picture,
                is_registered=False
            )
            db.session.add(student)
    
    student.last_login = datetime.utcnow()
    db.session.commit()
    
    # Set session
    session['student_logged_in'] = True
    session['student_id'] = student.id
    session['student_email'] = email
    session['student_name'] = name
    session['student_picture'] = picture
    
    return redirect(url_for('index'))


@app.route('/student/simulated-auth')
def student_simulated_auth():
    """Simulated authentication for students (development mode)"""
    return render_template('student_simulated_auth.html')


@app.route('/student/simulated-auth/submit', methods=['POST'])
def student_simulated_auth_submit():
    """Handle simulated student authentication"""
    email = request.form.get('email', '').strip().lower()
    name = request.form.get('name', '').strip()
    
    if not email or '@' not in email:
        return render_template('student_simulated_auth.html', error='Please enter a valid email address')
    
    google_id = hashlib.md5(email.encode()).hexdigest()
    
    if not name:
        name = email.split('@')[0].title()
    
    # Check if student exists
    student = Student.query.filter_by(email=email).first()
    
    if not student:
        student = Student(
            google_id=google_id,
            email=email,
            name=name,
            profile_picture='',
            is_registered=False
        )
        db.session.add(student)
    
    student.last_login = datetime.utcnow()
    db.session.commit()
    
    session['student_logged_in'] = True
    session['student_id'] = student.id
    session['student_email'] = email
    session['student_name'] = name
    session['student_picture'] = student.profile_picture or ''
    
    return redirect(url_for('index'))


@app.route('/student/logout')
def student_logout():
    """Logout student"""
    session.pop('student_logged_in', None)
    session.pop('student_id', None)
    session.pop('student_email', None)
    session.pop('student_name', None)
    session.pop('student_picture', None)
    return redirect(url_for('index'))


@app.route('/student/my-applications')
@student_required
def my_applications():
    """Page showing student's scholarship applications"""
    return render_template('my_applications.html')


@app.route('/dashboard')
def dashboard():
    """Dashboard page - Statistics and overview"""
    return render_template('dashboard.html')


@app.route('/admin')
@admin_required
def admin_panel():
    """Admin panel for managing scholarships and rules"""
    # Get unread application count for notifications
    unread_count = ScholarshipApplication.query.filter_by(is_read=False).count()
    
    admin_info = {
        'name': session.get('admin_name', 'Admin'),
        'email': session.get('admin_email', ''),
        'picture': session.get('admin_picture', ''),
        'is_super_admin': session.get('is_super_admin', False),
        'unread_applications': unread_count
    }
    return render_template('admin.html', admin_info=admin_info)


@app.route('/admin/applications')
@admin_required
def admin_applications():
    """Admin page for managing scholarship applications"""
    return render_template('admin_applications.html')


@app.route('/admin/login')
def admin_login():
    """Admin login page - shows Google login option"""
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_panel'))
    return render_template('admin_login.html')


@app.route('/admin/register')
def admin_register():
    """Admin registration page"""
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_panel'))
    return render_template('admin_register.html')


@app.route('/admin/google/login')
def google_login():
    """Initiate Google OAuth login flow"""
    # Store the action type in session (login or register)
    session['oauth_action'] = request.args.get('action', 'login')
    
    # Check if using simulated auth for development
    if getattr(config, 'USE_SIMULATED_AUTH', False):
        return redirect(url_for('simulated_auth'))
    
    # Build the Google OAuth URL
    google_provider_cfg = get_google_provider_cfg()
    if not google_provider_cfg:
        return render_template('admin_login.html', error='Could not connect to Google. Please try again.')
    
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]
    
    # Build redirect URI
    redirect_uri = url_for('google_callback', _external=True)
    
    # Build authorization URL
    auth_url = (
        f"{authorization_endpoint}?"
        f"client_id={config.GOOGLE_CLIENT_ID}&"
        f"redirect_uri={redirect_uri}&"
        f"scope=openid%20email%20profile&"
        f"response_type=code&"
        f"access_type=offline&"
        f"prompt=consent"
    )
    
    return redirect(auth_url)


@app.route('/admin/simulated-auth')
def simulated_auth():
    """Simulated authentication page for development without Google OAuth setup"""
    action = session.get('oauth_action', 'login')
    return render_template('simulated_auth.html', action=action)


@app.route('/admin/simulated-auth/submit', methods=['POST'])
def simulated_auth_submit():
    """Handle simulated authentication form submission"""
    email = request.form.get('email', '').strip().lower()
    name = request.form.get('name', '').strip()
    
    # Get action from form (fallback to session, then default to login)
    action = request.form.get('action') or session.pop('oauth_action', 'login')
    
    # Validate email
    if not email or '@' not in email:
        return render_template('simulated_auth.html', 
            action=action,
            error='Please enter a valid email address')
    
    # Generate a simulated Google ID from email
    google_id = hashlib.md5(email.encode()).hexdigest()
    
    if not name:
        name = email.split('@')[0].title()
    
    # Check if admin already exists
    admin = Admin.query.filter_by(email=email).first()
    
    if action == 'register':
        # Registration flow
        if admin:
            return render_template('simulated_auth.html', 
                action='register',
                error='This email is already registered. Please login instead.')
        
        # Create new admin (first admin becomes super admin)
        is_first_admin = Admin.query.count() == 0
        
        new_admin = Admin(
            google_id=google_id,
            email=email,
            name=name,
            profile_picture='',
            is_approved=is_first_admin or config.DEMO_MODE,
            is_super_admin=is_first_admin
        )
        
        db.session.add(new_admin)
        db.session.commit()
        
        if is_first_admin or config.DEMO_MODE:
            session['admin_logged_in'] = True
            session['admin_id'] = new_admin.id
            session['admin_email'] = email
            session['admin_name'] = name
            session['admin_picture'] = ''
            session['is_super_admin'] = new_admin.is_super_admin
            
            new_admin.last_login = datetime.utcnow()
            db.session.commit()
            
            return redirect(url_for('admin_panel'))
        else:
            return render_template('admin_login.html', 
                success='Registration successful! Please wait for admin approval.')
    else:
        # Login flow
        if not admin:
            return render_template('simulated_auth.html', 
                action='login',
                error='No account found with this email. Please register first.')
        
        if not admin.is_approved and not config.DEMO_MODE:
            return render_template('admin_login.html', 
                error='Your account is pending approval by a super admin.')
        
        # Login successful
        session['admin_logged_in'] = True
        session['admin_id'] = admin.id
        session['admin_email'] = admin.email
        session['admin_name'] = admin.name
        session['admin_picture'] = admin.profile_picture or ''
        session['is_super_admin'] = admin.is_super_admin
        
        admin.last_login = datetime.utcnow()
        db.session.commit()
        
        return redirect(url_for('admin_panel'))


@app.route('/admin/google/callback')
def google_callback():
    """Handle Google OAuth callback"""
    # Get the authorization code from Google
    code = request.args.get('code')
    if not code:
        return redirect(url_for('admin_login'))
    
    # Get Google's token endpoint
    google_provider_cfg = get_google_provider_cfg()
    if not google_provider_cfg:
        return render_template('admin_login.html', error='Could not connect to Google.')
    
    token_endpoint = google_provider_cfg["token_endpoint"]
    
    # Exchange code for tokens
    redirect_uri = url_for('google_callback', _external=True)
    token_response = requests.post(
        token_endpoint,
        data={
            'code': code,
            'client_id': config.GOOGLE_CLIENT_ID,
            'client_secret': config.GOOGLE_CLIENT_SECRET,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }
    )
    
    if token_response.status_code != 200:
        return render_template('admin_login.html', error='Failed to authenticate with Google.')
    
    tokens = token_response.json()
    
    # Get user info from Google
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    userinfo_response = requests.get(
        userinfo_endpoint,
        headers={'Authorization': f'Bearer {tokens["access_token"]}'}
    )
    
    if userinfo_response.status_code != 200:
        return render_template('admin_login.html', error='Failed to get user info from Google.')
    
    userinfo = userinfo_response.json()
    
    # Extract user details
    google_id = userinfo.get('sub')
    email = userinfo.get('email')
    name = userinfo.get('name', email.split('@')[0])
    picture = userinfo.get('picture', '')
    
    # Check if this is a registration or login
    action = session.pop('oauth_action', 'login')
    
    # Check if admin already exists
    admin = Admin.query.filter_by(google_id=google_id).first()
    
    if action == 'register':
        # Registration flow
        if admin:
            return render_template('admin_register.html', 
                error='This Google account is already registered. Please login instead.')
        
        # Check if email is already registered with different Google account
        existing_email = Admin.query.filter_by(email=email).first()
        if existing_email:
            return render_template('admin_register.html', 
                error='This email is already registered.')
        
        # Create new admin (first admin becomes super admin)
        is_first_admin = Admin.query.count() == 0
        
        new_admin = Admin(
            google_id=google_id,
            email=email,
            name=name,
            profile_picture=picture,
            is_approved=is_first_admin or config.DEMO_MODE,  # First admin is auto-approved
            is_super_admin=is_first_admin  # First admin is super admin
        )
        
        db.session.add(new_admin)
        db.session.commit()
        
        if is_first_admin or config.DEMO_MODE:
            # Auto-login first admin or in demo mode
            session['admin_logged_in'] = True
            session['admin_id'] = new_admin.id
            session['admin_email'] = email
            session['admin_name'] = name
            session['admin_picture'] = picture
            session['is_super_admin'] = new_admin.is_super_admin
            
            new_admin.last_login = datetime.utcnow()
            db.session.commit()
            
            return redirect(url_for('admin_panel'))
        else:
            return render_template('admin_register.html', 
                success='Registration successful! Please wait for admin approval.')
    
    else:
        # Login flow
        if not admin:
            return render_template('admin_login.html', 
                error='No account found. Please register first.')
        
        # Check if approved (or in demo mode)
        if not admin.is_approved and not config.DEMO_MODE:
            return render_template('admin_login.html', 
                error='Your account is pending approval. Please contact the administrator.')
        
        # Login successful
        session['admin_logged_in'] = True
        session['admin_id'] = admin.id
        session['admin_email'] = admin.email
        session['admin_name'] = admin.name
        session['admin_picture'] = admin.profile_picture
        session['is_super_admin'] = admin.is_super_admin
        
        # Update last login
        admin.last_login = datetime.utcnow()
        admin.name = name  # Update name in case it changed
        admin.profile_picture = picture  # Update picture
        db.session.commit()
        
        return redirect(url_for('admin_panel'))


@app.route('/admin/logout')
def admin_logout():
    """Admin logout - clear all session data"""
    session.clear()
    return redirect(url_for('index'))


@app.route('/admin/users')
@admin_required
@super_admin_required
def admin_users():
    """Admin users management page (super admin only)"""
    return render_template('admin_users.html')


@app.route('/results/<int:student_id>')
def results_page(student_id):
    """Display eligibility results for a student"""
    student = Student.query.get_or_404(student_id)
    return render_template('results.html', student_id=student_id)


# =====================================================
# API ENDPOINTS - Admin Users Management
# =====================================================

@app.route('/api/admin/users', methods=['GET'])
@admin_required
@super_admin_required
def get_admin_users():
    """Get all admin users (super admin only)"""
    admins = Admin.query.all()
    return jsonify({
        'success': True,
        'admins': [a.to_dict() for a in admins]
    })


@app.route('/api/admin/users/<int:admin_id>/approve', methods=['POST'])
@admin_required
@super_admin_required
def approve_admin(admin_id):
    """Approve an admin user (super admin only)"""
    admin = Admin.query.get_or_404(admin_id)
    admin.is_approved = True
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'{admin.name} has been approved'
    })


@app.route('/api/admin/users/<int:admin_id>/revoke', methods=['POST'])
@admin_required
@super_admin_required
def revoke_admin(admin_id):
    """Revoke admin approval (super admin only)"""
    admin = Admin.query.get_or_404(admin_id)
    
    # Prevent revoking own access
    if admin.id == session.get('admin_id'):
        return jsonify({
            'success': False,
            'error': 'Cannot revoke your own access'
        }), 400
    
    admin.is_approved = False
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'{admin.name} access has been revoked'
    })


@app.route('/api/admin/users/<int:admin_id>', methods=['DELETE'])
@admin_required
@super_admin_required
def delete_admin(admin_id):
    """Delete an admin user (super admin only)"""
    admin = Admin.query.get_or_404(admin_id)
    
    # Prevent deleting own account
    if admin.id == session.get('admin_id'):
        return jsonify({
            'success': False,
            'error': 'Cannot delete your own account'
        }), 400
    
    db.session.delete(admin)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Admin deleted successfully'
    })


# =====================================================
# API ENDPOINTS - Students
# =====================================================

@app.route('/api/students', methods=['GET'])
def get_students():
    """Get all students"""
    students = Student.query.all()
    return jsonify({
        'success': True,
        'students': [s.to_dict() for s in students],
        'count': len(students)
    })


@app.route('/api/students/<int:student_id>', methods=['GET'])
def get_student(student_id):
    """Get a specific student by ID"""
    student = Student.query.get_or_404(student_id)
    return jsonify({
        'success': True,
        'student': student.to_dict()
    })


@app.route('/api/students', methods=['POST'])
def create_student():
    """
    Create or update a student application.
    If student is logged in, updates their profile.
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'email', 'course', 'year_of_study', 
                          'marks_percentage', 'family_income', 'category']
        
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Check if student is logged in
        if session.get('student_logged_in'):
            student = Student.query.get(session.get('student_id'))
            if student:
                # Update existing student profile
                student.name = data['name']
                student.course = data['course']
                student.year_of_study = int(data['year_of_study'])
                student.marks_percentage = float(data['marks_percentage'])
                student.family_income = float(data['family_income'])
                student.category = data['category']
                student.has_backlogs = data.get('has_backlogs', False)
                student.is_full_time = data.get('is_full_time', True)
                student.is_registered = True
                
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Profile updated successfully',
                    'student': student.to_dict()
                }), 200
        
        # Check if email already exists (for non-logged in users)
        existing = Student.query.filter_by(email=data['email']).first()
        if existing:
            return jsonify({
                'success': False,
                'error': 'A student with this email already exists. Please login first.'
            }), 400
        
        # Create new student (legacy support for non-OAuth flow)
        student = Student(
            name=data['name'],
            email=data['email'],
            course=data['course'],
            year_of_study=int(data['year_of_study']),
            marks_percentage=float(data['marks_percentage']),
            family_income=float(data['family_income']),
            category=data['category'],
            has_backlogs=data.get('has_backlogs', False),
            is_full_time=data.get('is_full_time', True),
            is_registered=True
        )
        
        db.session.add(student)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Student application submitted successfully',
            'student': student.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/students/<int:student_id>', methods=['DELETE'])
def delete_student(student_id):
    """Delete a student"""
    student = Student.query.get_or_404(student_id)
    
    # Delete related eligibility results first
    EligibilityResult.query.filter_by(student_id=student_id).delete()
    
    db.session.delete(student)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Student deleted successfully'
    })


# =====================================================
# API ENDPOINTS - Scholarships
# =====================================================

@app.route('/api/scholarships', methods=['GET'])
def get_scholarships():
    """Get all scholarships with their rules"""
    scholarships = Scholarship.query.all()
    return jsonify({
        'success': True,
        'scholarships': [s.to_dict() for s in scholarships],
        'count': len(scholarships)
    })


@app.route('/api/scholarships/<int:scholarship_id>', methods=['GET'])
def get_scholarship(scholarship_id):
    """Get a specific scholarship by ID"""
    scholarship = Scholarship.query.get_or_404(scholarship_id)
    return jsonify({
        'success': True,
        'scholarship': scholarship.to_dict()
    })


@app.route('/api/scholarships', methods=['POST'])
def create_scholarship():
    """Create a new scholarship (Admin only)"""
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        
        scholarship = Scholarship(
            name=data['name'],
            description=data.get('description', ''),
            amount=float(data['amount']),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(scholarship)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Scholarship created successfully',
            'scholarship': scholarship.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/scholarships/<int:scholarship_id>', methods=['PUT'])
def update_scholarship(scholarship_id):
    """Update a scholarship (Admin only)"""
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    scholarship = Scholarship.query.get_or_404(scholarship_id)
    data = request.get_json()
    
    scholarship.name = data.get('name', scholarship.name)
    scholarship.description = data.get('description', scholarship.description)
    scholarship.amount = float(data.get('amount', scholarship.amount))
    scholarship.is_active = data.get('is_active', scholarship.is_active)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Scholarship updated successfully',
        'scholarship': scholarship.to_dict()
    })


@app.route('/api/scholarships/<int:scholarship_id>', methods=['DELETE'])
def delete_scholarship(scholarship_id):
    """Delete a scholarship (Admin only)"""
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    scholarship = Scholarship.query.get_or_404(scholarship_id)
    
    # Delete related eligibility results
    EligibilityResult.query.filter_by(scholarship_id=scholarship_id).delete()
    
    db.session.delete(scholarship)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Scholarship deleted successfully'
    })


# =====================================================
# API ENDPOINTS - Rules (Dynamic Rule Management)
# =====================================================

@app.route('/api/rules', methods=['POST'])
def create_rule():
    """Create a new rule for a scholarship (Admin only)"""
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        
        rule = Rule(
            scholarship_id=int(data['scholarship_id']),
            field=data['field'],
            operator=data['operator'],
            value=data['value'],
            weight=float(data.get('weight', 1.0)),
            description=data.get('description', ''),
            error_message=data.get('error_message', '')
        )
        
        db.session.add(rule)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Rule created successfully',
            'rule': rule.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/rules/<int:rule_id>', methods=['PUT'])
def update_rule(rule_id):
    """Update a rule (Admin only)"""
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    rule = Rule.query.get_or_404(rule_id)
    data = request.get_json()
    
    rule.field = data.get('field', rule.field)
    rule.operator = data.get('operator', rule.operator)
    rule.value = data.get('value', rule.value)
    rule.weight = float(data.get('weight', rule.weight))
    rule.description = data.get('description', rule.description)
    rule.error_message = data.get('error_message', rule.error_message)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Rule updated successfully',
        'rule': rule.to_dict()
    })


@app.route('/api/rules/<int:rule_id>', methods=['DELETE'])
def delete_rule(rule_id):
    """Delete a rule (Admin only)"""
    if not session.get('admin_logged_in'):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    rule = Rule.query.get_or_404(rule_id)
    db.session.delete(rule)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Rule deleted successfully'
    })


# =====================================================
# API ENDPOINTS - Eligibility Checking
# =====================================================

@app.route('/api/check-eligibility/<int:student_id>', methods=['GET'])
def check_student_eligibility(student_id):
    """
    Check a student's eligibility for all active scholarships.
    Returns detailed results with reasons for rejection.
    Also automatically creates applications for eligible scholarships.
    """
    student = Student.query.get_or_404(student_id)
    scholarships = Scholarship.query.filter_by(is_active=True).all()
    
    # Use the rules engine to check eligibility
    results = rules_engine.check_all_scholarships(student, scholarships)
    
    # Store results in database for dashboard tracking
    for scholarship in scholarships:
        # Find the result for this scholarship
        eligible_result = next(
            (r for r in results['eligible_scholarships'] if r['scholarship_id'] == scholarship.id),
            None
        )
        ineligible_result = next(
            (r for r in results['ineligible_scholarships'] if r['scholarship_id'] == scholarship.id),
            None
        )
        
        result = eligible_result or ineligible_result
        if result:
            # Check if result already exists
            existing = EligibilityResult.query.filter_by(
                student_id=student_id,
                scholarship_id=scholarship.id
            ).first()
            
            if existing:
                # Update existing result
                existing.is_eligible = result['eligible']
                existing.priority_score = result['priority_score']
                existing.rejection_reasons = json.dumps(result['rejection_reasons'])
            else:
                # Create new result
                new_result = EligibilityResult(
                    student_id=student_id,
                    scholarship_id=scholarship.id,
                    is_eligible=result['eligible'],
                    priority_score=result['priority_score'],
                    rejection_reasons=json.dumps(result['rejection_reasons'])
                )
                db.session.add(new_result)
            
            # Auto-create application for eligible scholarships
            if result['eligible']:
                # Check if application already exists
                existing_app = ScholarshipApplication.query.filter_by(
                    student_id=student_id,
                    scholarship_id=scholarship.id
                ).first()
                
                if not existing_app:
                    # Create new application automatically
                    new_application = ScholarshipApplication(
                        student_id=student_id,
                        scholarship_id=scholarship.id,
                        status='pending',
                        is_read=False  # Mark as unread for admin notification
                    )
                    db.session.add(new_application)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'results': results
    })


@app.route('/api/rankings/<int:scholarship_id>', methods=['GET'])
def get_scholarship_rankings(scholarship_id):
    """
    Get ranked list of eligible students for a specific scholarship.
    Ranked by priority score (higher is better).
    """
    scholarship = Scholarship.query.get_or_404(scholarship_id)
    students = Student.query.all()
    
    # Use the rules engine to rank students
    rankings = rules_engine.rank_students(students, scholarship)
    
    return jsonify({
        'success': True,
        'scholarship': scholarship.to_dict(),
        'rankings': rankings,
        'total_eligible': len(rankings)
    })


# =====================================================
# API ENDPOINTS - Dashboard Statistics
# =====================================================

@app.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """
    Get statistics for the dashboard:
    - Total applicants
    - Eligible count
    - Non-eligible count
    - Top priority students
    """
    # Total applicants
    total_applicants = Student.query.count()
    
    # Get unique eligible students (eligible for at least one scholarship)
    eligible_results = EligibilityResult.query.filter_by(is_eligible=True).all()
    eligible_student_ids = set(r.student_id for r in eligible_results)
    eligible_count = len(eligible_student_ids)
    
    # Non-eligible count
    all_student_ids = set(s.id for s in Student.query.all())
    checked_student_ids = set(r.student_id for r in EligibilityResult.query.all())
    
    # Students who have been checked but are not eligible for any scholarship
    only_ineligible_ids = checked_student_ids - eligible_student_ids
    non_eligible_count = len(only_ineligible_ids)
    
    # Not yet checked
    not_checked_count = len(all_student_ids - checked_student_ids)
    
    # Top priority students (top 10 by priority score)
    top_results = EligibilityResult.query.filter_by(is_eligible=True)\
        .order_by(EligibilityResult.priority_score.desc())\
        .limit(10).all()
    
    top_priority_students = []
    for result in top_results:
        top_priority_students.append({
            'student_id': result.student_id,
            'student_name': result.student.name,
            'scholarship_name': result.scholarship.name,
            'priority_score': result.priority_score,
            'marks': result.student.marks_percentage,
            'income': result.student.family_income
        })
    
    # Scholarship-wise statistics
    scholarships = Scholarship.query.filter_by(is_active=True).all()
    scholarship_stats = []
    
    for scholarship in scholarships:
        eligible = EligibilityResult.query.filter_by(
            scholarship_id=scholarship.id,
            is_eligible=True
        ).count()
        
        total_checked = EligibilityResult.query.filter_by(
            scholarship_id=scholarship.id
        ).count()
        
        scholarship_stats.append({
            'id': scholarship.id,
            'name': scholarship.name,
            'amount': scholarship.amount,
            'eligible_count': eligible,
            'total_checked': total_checked
        })
    
    return jsonify({
        'success': True,
        'stats': {
            'total_applicants': total_applicants,
            'eligible_count': eligible_count,
            'non_eligible_count': non_eligible_count,
            'not_checked_count': not_checked_count,
            'top_priority_students': top_priority_students,
            'scholarship_stats': scholarship_stats
        }
    })


# =====================================================
# ERROR HANDLERS
# =====================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    if request.path.startswith('/api/'):
        return jsonify({'success': False, 'error': 'Resource not found'}), 404
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors"""
    if request.path.startswith('/api/'):
        return jsonify({'success': False, 'error': 'Internal server error'}), 500
    return render_template('500.html'), 500


# =====================================================
# SCHOLARSHIP APPLICATION API
# =====================================================

@app.route('/api/applications', methods=['POST'])
@student_required
def apply_for_scholarship():
    """Student applies for a specific scholarship"""
    try:
        data = request.get_json()
        scholarship_id = data.get('scholarship_id')
        
        if not scholarship_id:
            return jsonify({'success': False, 'error': 'Scholarship ID required'}), 400
        
        student_id = session.get('student_id')
        student = Student.query.get(student_id)
        
        if not student or not student.is_registered:
            return jsonify({'success': False, 'error': 'Please complete your profile first'}), 400
        
        # Check if scholarship exists
        scholarship = Scholarship.query.get(scholarship_id)
        if not scholarship:
            return jsonify({'success': False, 'error': 'Scholarship not found'}), 404
        
        # Check if already applied
        existing = ScholarshipApplication.query.filter_by(
            student_id=student_id, 
            scholarship_id=scholarship_id
        ).first()
        
        if existing:
            return jsonify({'success': False, 'error': 'You have already applied for this scholarship'}), 400
        
        # Check eligibility before applying
        eligibility = EligibilityResult.query.filter_by(
            student_id=student_id,
            scholarship_id=scholarship_id,
            is_eligible=True
        ).first()
        
        if not eligibility:
            return jsonify({'success': False, 'error': 'You are not eligible for this scholarship'}), 400
        
        # Create application
        application = ScholarshipApplication(
            student_id=student_id,
            scholarship_id=scholarship_id,
            status='pending'
        )
        
        db.session.add(application)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully applied for {scholarship.name}',
            'application': application.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/applications/my', methods=['GET'])
@student_required
def get_my_applications():
    """Get all applications for the logged-in student"""
    student_id = session.get('student_id')
    applications = ScholarshipApplication.query.filter_by(student_id=student_id).all()
    
    return jsonify({
        'success': True,
        'applications': [app.to_dict() for app in applications]
    })


@app.route('/api/admin/applications', methods=['GET'])
@admin_required
def get_all_applications():
    """Get all scholarship applications for admin"""
    status_filter = request.args.get('status')
    
    query = ScholarshipApplication.query.order_by(ScholarshipApplication.applied_at.desc())
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    applications = query.all()
    
    # Count unread notifications
    unread_count = ScholarshipApplication.query.filter_by(is_read=False).count()
    
    return jsonify({
        'success': True,
        'applications': [app.to_dict() for app in applications],
        'unread_count': unread_count
    })


@app.route('/api/admin/applications/<int:app_id>/read', methods=['POST'])
@admin_required
def mark_application_read(app_id):
    """Mark an application as read"""
    application = ScholarshipApplication.query.get_or_404(app_id)
    application.is_read = True
    db.session.commit()
    
    return jsonify({'success': True})


@app.route('/api/admin/applications/<int:app_id>/status', methods=['PUT'])
@admin_required
def update_application_status(app_id):
    """Update application status (approve/reject)"""
    try:
        data = request.get_json()
        new_status = data.get('status')
        notes = data.get('notes', '')
        
        if new_status not in ['pending', 'under_review', 'approved', 'rejected']:
            return jsonify({'success': False, 'error': 'Invalid status'}), 400
        
        application = ScholarshipApplication.query.get_or_404(app_id)
        application.status = new_status
        application.admin_notes = notes
        application.reviewed_at = datetime.utcnow()
        application.reviewed_by = session.get('admin_id')
        application.is_read = True
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Application status updated to {new_status}',
            'application': application.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/admin/notifications/count', methods=['GET'])
@admin_required
def get_notification_count():
    """Get count of unread applications"""
    unread_count = ScholarshipApplication.query.filter_by(is_read=False).count()
    return jsonify({'success': True, 'count': unread_count})


# =====================================================
# DOCUMENT UPLOAD & FEEDBACK ROUTES
# =====================================================

@app.route('/api/admin/applications/<int:app_id>/request-documents', methods=['POST'])
@admin_required
def request_documents(app_id):
    """Admin sends feedback requesting documents from student"""
    try:
        data = request.get_json()
        feedback = data.get('feedback', '')
        
        if not feedback:
            return jsonify({'success': False, 'error': 'Feedback message is required'}), 400
        
        application = ScholarshipApplication.query.get_or_404(app_id)
        application.admin_feedback = feedback
        application.documents_requested = True
        application.status = 'documents_requested'
        application.feedback_sent_at = datetime.utcnow()
        application.feedback_read = False
        application.reviewed_by = session.get('admin_id')
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Document request sent to student',
            'application': application.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/student/applications/<int:app_id>/upload-document', methods=['POST'])
@student_required
def upload_document(app_id):
    """Student uploads a document for their application"""
    try:
        # Verify the application belongs to the logged-in student
        student_id = session.get('student_id')
        application = ScholarshipApplication.query.get_or_404(app_id)
        
        if application.student_id != student_id:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        if 'document' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        
        file = request.files['document']
        document_type = request.form.get('document_type', 'Other')
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'File type not allowed. Allowed: PDF, PNG, JPG, DOC, DOCX'}), 400
        
        # Generate unique filename
        original_filename = secure_filename(file.filename)
        file_ext = original_filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}_{app_id}.{file_ext}"
        
        # Save file
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Create document record
        doc = ApplicationDocument(
            application_id=app_id,
            filename=original_filename,
            stored_filename=unique_filename,
            file_type=file_ext,
            file_size=file_size,
            document_type=document_type
        )
        
        db.session.add(doc)
        
        # Update application - mark as documents uploaded for admin review
        application.is_read = False  # Notify admin about new documents
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Document uploaded successfully',
            'document': doc.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/applications/<int:app_id>/documents', methods=['GET'])
def get_application_documents(app_id):
    """Get all documents for an application"""
    # Check if admin or student owner
    is_admin = session.get('admin_logged_in')
    is_student = session.get('student_logged_in')
    student_id = session.get('student_id')
    
    application = ScholarshipApplication.query.get_or_404(app_id)
    
    if not is_admin and (not is_student or application.student_id != student_id):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    documents = ApplicationDocument.query.filter_by(application_id=app_id).all()
    
    return jsonify({
        'success': True,
        'documents': [doc.to_dict() for doc in documents]
    })


@app.route('/api/documents/<int:doc_id>/download', methods=['GET'])
def download_document(doc_id):
    """Download a specific document"""
    # Check if admin or student owner
    is_admin = session.get('admin_logged_in')
    is_student = session.get('student_logged_in')
    student_id = session.get('student_id')
    
    doc = ApplicationDocument.query.get_or_404(doc_id)
    application = doc.application
    
    if not is_admin and (not is_student or application.student_id != student_id):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    return send_from_directory(
        app.config['UPLOAD_FOLDER'],
        doc.stored_filename,
        as_attachment=True,
        download_name=doc.filename
    )


@app.route('/api/student/applications/<int:app_id>/mark-feedback-read', methods=['POST'])
@student_required
def mark_feedback_read(app_id):
    """Mark admin feedback as read by student"""
    student_id = session.get('student_id')
    application = ScholarshipApplication.query.get_or_404(app_id)
    
    if application.student_id != student_id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    application.feedback_read = True
    db.session.commit()
    
    return jsonify({'success': True})


@app.route('/api/student/notifications/count', methods=['GET'])
@student_required
def get_student_notification_count():
    """Get count of unread feedback for student"""
    student_id = session.get('student_id')
    unread_count = ScholarshipApplication.query.filter_by(
        student_id=student_id,
        documents_requested=True,
        feedback_read=False
    ).count()
    return jsonify({'success': True, 'count': unread_count})


# =====================================================
# APPLICATION STARTUP
# =====================================================

if __name__ == '__main__':
    # Create database tables and initialize sample data
    with app.app_context():
        db.create_all()
        init_sample_data()
    
    # Run the application in debug mode
    print("\n" + "="*50)
    print("Scholarship Eligibility Filter")
    print("="*50)
    print("Server starting at: http://localhost:5000")
    print("Admin Panel: http://localhost:5000/admin")
    print("Admin Credentials: admin / admin123")
    print("="*50 + "\n")
    
    app.run(debug=True, port=5000)
