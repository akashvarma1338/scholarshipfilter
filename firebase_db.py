"""
Firebase Database Helper
Provides database operations using Firebase Realtime Database
"""

import firebase_admin
from firebase_admin import credentials, db
import json
from datetime import datetime
import os
import config

# Initialize Firebase
def init_firebase():
    try:
        firebase_admin.get_app()
    except ValueError:
        try:
            # Try environment variable first (for Render deployment)
            firebase_creds = os.environ.get('FIREBASE_CREDENTIALS')
            if firebase_creds:
                cred_dict = json.loads(firebase_creds)
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred, {
                    'databaseURL': config.FIREBASE_CONFIG['databaseURL']
                })
            elif os.path.exists(config.FIREBASE_CREDENTIALS_PATH):
                cred = credentials.Certificate(config.FIREBASE_CREDENTIALS_PATH)
                firebase_admin.initialize_app(cred, {
                    'databaseURL': config.FIREBASE_CONFIG['databaseURL']
                })
            else:
                firebase_admin.initialize_app(options={
                    'databaseURL': config.FIREBASE_CONFIG['databaseURL']
                })
        except:
            firebase_admin.initialize_app(options={
                'databaseURL': config.FIREBASE_CONFIG['databaseURL']
            })

# Database references
def get_ref(path):
    """Get database reference for a path"""
    return db.reference(path)

# Helper functions
def generate_id():
    """Generate unique ID"""
    import uuid
    return str(uuid.uuid4())

def to_timestamp(dt=None):
    """Convert datetime to timestamp"""
    if dt is None:
        dt = datetime.utcnow()
    return dt.isoformat()

def from_timestamp(ts):
    """Convert timestamp to datetime"""
    if ts:
        return datetime.fromisoformat(ts)
    return None

# Admin operations
class AdminDB:
    @staticmethod
    def create(email, password, name, is_super_admin=False):
        """Create new admin"""
        admin_id = generate_id()
        admin_data = {
            'id': admin_id,
            'email': email,
            'password': password,
            'name': name,
            'is_approved': is_super_admin,
            'is_super_admin': is_super_admin,
            'created_at': to_timestamp(),
            'last_login': None
        }
        get_ref(f'admins/{admin_id}').set(admin_data)
        return admin_id, admin_data
    
    @staticmethod
    def get_by_email(email):
        """Get admin by email"""
        admins = get_ref('admins').get() or {}
        for admin_id, admin in admins.items():
            if admin.get('email') == email:
                admin['id'] = admin_id
                return admin
        return None
    
    @staticmethod
    def get_by_id(admin_id):
        """Get admin by ID"""
        admin = get_ref(f'admins/{admin_id}').get()
        if admin:
            admin['id'] = admin_id
        return admin
    
    @staticmethod
    def update(admin_id, data):
        """Update admin"""
        get_ref(f'admins/{admin_id}').update(data)
    
    @staticmethod
    def get_all():
        """Get all admins"""
        admins = get_ref('admins').get() or {}
        result = []
        for admin_id, admin in admins.items():
            admin['id'] = admin_id
            result.append(admin)
        return result
    
    @staticmethod
    def delete(admin_id):
        """Delete admin"""
        get_ref(f'admins/{admin_id}').delete()
    
    @staticmethod
    def count():
        """Count admins"""
        admins = get_ref('admins').get() or {}
        return len(admins)

# Student operations
class StudentDB:
    @staticmethod
    def create(email, password, name):
        """Create new student"""
        student_id = generate_id()
        student_data = {
            'id': student_id,
            'email': email,
            'password': password,
            'name': name,
            'is_registered': False,
            'course': None,
            'year_of_study': None,
            'marks_percentage': None,
            'family_income': None,
            'category': None,
            'has_backlogs': False,
            'is_full_time': True,
            'created_at': to_timestamp(),
            'last_login': None
        }
        get_ref(f'students/{student_id}').set(student_data)
        return student_id, student_data
    
    @staticmethod
    def get_by_email(email):
        """Get student by email"""
        students = get_ref('students').get() or {}
        for student_id, student in students.items():
            if student.get('email') == email:
                student['id'] = student_id
                return student
        return None
    
    @staticmethod
    def get_by_id(student_id):
        """Get student by ID"""
        student = get_ref(f'students/{student_id}').get()
        if student:
            student['id'] = student_id
        return student
    
    @staticmethod
    def update(student_id, data):
        """Update student"""
        get_ref(f'students/{student_id}').update(data)
    
    @staticmethod
    def get_all():
        """Get all students"""
        students = get_ref('students').get() or {}
        result = []
        for student_id, student in students.items():
            student['id'] = student_id
            result.append(student)
        return result
    
    @staticmethod
    def delete(student_id):
        """Delete student"""
        get_ref(f'students/{student_id}').delete()

# Scholarship operations
class ScholarshipDB:
    @staticmethod
    def create(name, description, amount, is_active=True):
        """Create new scholarship"""
        scholarship_id = generate_id()
        scholarship_data = {
            'id': scholarship_id,
            'name': name,
            'description': description,
            'amount': amount,
            'is_active': is_active,
            'created_at': to_timestamp()
        }
        get_ref(f'scholarships/{scholarship_id}').set(scholarship_data)
        return scholarship_id, scholarship_data
    
    @staticmethod
    def get_by_id(scholarship_id):
        """Get scholarship by ID"""
        scholarship = get_ref(f'scholarships/{scholarship_id}').get()
        if scholarship:
            scholarship['id'] = scholarship_id
            # Get rules
            scholarship['rules'] = RuleDB.get_by_scholarship(scholarship_id)
        return scholarship
    
    @staticmethod
    def update(scholarship_id, data):
        """Update scholarship"""
        get_ref(f'scholarships/{scholarship_id}').update(data)
    
    @staticmethod
    def get_all(active_only=False):
        """Get all scholarships"""
        scholarships = get_ref('scholarships').get() or {}
        result = []
        for scholarship_id, scholarship in scholarships.items():
            if active_only and not scholarship.get('is_active', True):
                continue
            scholarship['id'] = scholarship_id
            scholarship['rules'] = RuleDB.get_by_scholarship(scholarship_id)
            result.append(scholarship)
        return result
    
    @staticmethod
    def delete(scholarship_id):
        """Delete scholarship"""
        get_ref(f'scholarships/{scholarship_id}').delete()
        # Delete associated rules
        rules = RuleDB.get_by_scholarship(scholarship_id)
        for rule in rules:
            RuleDB.delete(rule['id'])

# Rule operations
class RuleDB:
    @staticmethod
    def create(scholarship_id, field, operator, value, weight=1.0, description='', error_message=''):
        """Create new rule"""
        rule_id = generate_id()
        rule_data = {
            'id': rule_id,
            'scholarship_id': scholarship_id,
            'field': field,
            'operator': operator,
            'value': value,
            'weight': weight,
            'description': description,
            'error_message': error_message
        }
        get_ref(f'rules/{rule_id}').set(rule_data)
        return rule_id, rule_data
    
    @staticmethod
    def get_by_id(rule_id):
        """Get rule by ID"""
        rule = get_ref(f'rules/{rule_id}').get()
        if rule:
            rule['id'] = rule_id
        return rule
    
    @staticmethod
    def get_by_scholarship(scholarship_id):
        """Get all rules for a scholarship"""
        rules = get_ref('rules').get() or {}
        result = []
        for rule_id, rule in rules.items():
            if rule.get('scholarship_id') == scholarship_id:
                rule['id'] = rule_id
                result.append(rule)
        return result
    
    @staticmethod
    def update(rule_id, data):
        """Update rule"""
        get_ref(f'rules/{rule_id}').update(data)
    
    @staticmethod
    def delete(rule_id):
        """Delete rule"""
        get_ref(f'rules/{rule_id}').delete()

# Eligibility Result operations
class EligibilityResultDB:
    @staticmethod
    def create(student_id, scholarship_id, is_eligible, priority_score, rejection_reasons):
        """Create eligibility result"""
        result_id = generate_id()
        result_data = {
            'id': result_id,
            'student_id': student_id,
            'scholarship_id': scholarship_id,
            'is_eligible': is_eligible,
            'priority_score': priority_score,
            'rejection_reasons': json.dumps(rejection_reasons),
            'checked_at': to_timestamp()
        }
        get_ref(f'eligibility_results/{result_id}').set(result_data)
        return result_id, result_data
    
    @staticmethod
    def get_by_student_scholarship(student_id, scholarship_id):
        """Get result for student and scholarship"""
        results = get_ref('eligibility_results').get() or {}
        for result_id, result in results.items():
            if result.get('student_id') == student_id and result.get('scholarship_id') == scholarship_id:
                result['id'] = result_id
                return result
        return None
    
    @staticmethod
    def update_or_create(student_id, scholarship_id, is_eligible, priority_score, rejection_reasons):
        """Update existing or create new result"""
        existing = EligibilityResultDB.get_by_student_scholarship(student_id, scholarship_id)
        if existing:
            get_ref(f'eligibility_results/{existing["id"]}').update({
                'is_eligible': is_eligible,
                'priority_score': priority_score,
                'rejection_reasons': json.dumps(rejection_reasons),
                'checked_at': to_timestamp()
            })
            return existing['id']
        else:
            result_id, _ = EligibilityResultDB.create(student_id, scholarship_id, is_eligible, priority_score, rejection_reasons)
            return result_id
    
    @staticmethod
    def get_all():
        """Get all results"""
        results = get_ref('eligibility_results').get() or {}
        result_list = []
        for result_id, result in results.items():
            result['id'] = result_id
            result_list.append(result)
        return result_list
    
    @staticmethod
    def delete_by_student(student_id):
        """Delete all results for a student"""
        results = get_ref('eligibility_results').get() or {}
        for result_id, result in results.items():
            if result.get('student_id') == student_id:
                get_ref(f'eligibility_results/{result_id}').delete()

# Application operations
class ApplicationDB:
    @staticmethod
    def create(student_id, scholarship_id):
        """Create new application"""
        app_id = generate_id()
        app_data = {
            'id': app_id,
            'student_id': student_id,
            'scholarship_id': scholarship_id,
            'status': 'pending',
            'admin_notes': None,
            'admin_feedback': None,
            'documents_requested': False,
            'applied_at': to_timestamp(),
            'reviewed_at': None,
            'reviewed_by': None,
            'feedback_sent_at': None,
            'is_read': False,
            'feedback_read': False
        }
        get_ref(f'applications/{app_id}').set(app_data)
        return app_id, app_data
    
    @staticmethod
    def get_by_id(app_id):
        """Get application by ID"""
        app = get_ref(f'applications/{app_id}').get()
        if app:
            app['id'] = app_id
        return app
    
    @staticmethod
    def get_by_student_scholarship(student_id, scholarship_id):
        """Get application for student and scholarship"""
        apps = get_ref('applications').get() or {}
        for app_id, app in apps.items():
            if app.get('student_id') == student_id and app.get('scholarship_id') == scholarship_id:
                app['id'] = app_id
                return app
        return None
    
    @staticmethod
    def get_by_student(student_id):
        """Get all applications for a student"""
        apps = get_ref('applications').get() or {}
        result = []
        for app_id, app in apps.items():
            if app.get('student_id') == student_id:
                app['id'] = app_id
                result.append(app)
        return result
    
    @staticmethod
    def get_all(status=None):
        """Get all applications"""
        apps = get_ref('applications').get() or {}
        result = []
        for app_id, app in apps.items():
            if status and app.get('status') != status:
                continue
            app['id'] = app_id
            result.append(app)
        return result
    
    @staticmethod
    def update(app_id, data):
        """Update application"""
        get_ref(f'applications/{app_id}').update(data)
    
    @staticmethod
    def count_unread():
        """Count unread applications"""
        apps = get_ref('applications').get() or {}
        count = 0
        for app in apps.values():
            if not app.get('is_read', False):
                count += 1
        return count

# Document operations
class DocumentDB:
    @staticmethod
    def create(app_id, filename, stored_filename, file_type, file_size, document_type):
        """Create document record"""
        doc_id = generate_id()
        doc_data = {
            'id': doc_id,
            'application_id': app_id,
            'filename': filename,
            'stored_filename': stored_filename,
            'file_type': file_type,
            'file_size': file_size,
            'document_type': document_type,
            'uploaded_at': to_timestamp()
        }
        get_ref(f'documents/{doc_id}').set(doc_data)
        return doc_id, doc_data
    
    @staticmethod
    def get_by_application(app_id):
        """Get all documents for an application"""
        docs = get_ref('documents').get() or {}
        result = []
        for doc_id, doc in docs.items():
            if doc.get('application_id') == app_id:
                doc['id'] = doc_id
                result.append(doc)
        return result
    
    @staticmethod
    def get_by_id(doc_id):
        """Get document by ID"""
        doc = get_ref(f'documents/{doc_id}').get()
        if doc:
            doc['id'] = doc_id
        return doc
