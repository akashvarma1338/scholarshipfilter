"""
Database Models for Scholarship Eligibility Filter
Contains: Student, Scholarship, Rule, and Admin models
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initialize SQLAlchemy instance
db = SQLAlchemy()


class Admin(db.Model):
    """
    Admin model to store registered admin users
    Uses Google OAuth for authentication
    """
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(100), unique=True, nullable=False)  # Google's unique user ID
    email = db.Column(db.String(100), unique=True, nullable=False)      # Google email
    name = db.Column(db.String(100), nullable=False)                    # Display name
    profile_picture = db.Column(db.String(500))                         # Profile picture URL
    is_approved = db.Column(db.Boolean, default=False)                  # Admin approval status
    is_super_admin = db.Column(db.Boolean, default=False)               # Super admin can approve others
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<Admin {self.email}>'
    
    def to_dict(self):
        """Convert admin object to dictionary for JSON response"""
        return {
            'id': self.id,
            'google_id': self.google_id,
            'email': self.email,
            'name': self.name,
            'profile_picture': self.profile_picture,
            'is_approved': self.is_approved,
            'is_super_admin': self.is_super_admin,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'last_login': self.last_login.strftime('%Y-%m-%d %H:%M:%S') if self.last_login else None
        }


class Student(db.Model):
    """
    Student model to store applicant details
    Uses Google OAuth for authentication
    """
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    # Google OAuth fields
    google_id = db.Column(db.String(100), unique=True, nullable=True)   # Google's unique user ID
    profile_picture = db.Column(db.String(500))                          # Profile picture URL
    is_registered = db.Column(db.Boolean, default=False)                 # True if completed profile
    
    # Student details
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    course = db.Column(db.String(100), nullable=True)
    year_of_study = db.Column(db.Integer, nullable=True)
    marks_percentage = db.Column(db.Float, nullable=True)   # Marks in percentage
    family_income = db.Column(db.Float, nullable=True)      # Annual family income
    category = db.Column(db.String(50), nullable=True)      # General/OBC/SC/ST/EWS
    has_backlogs = db.Column(db.Boolean, default=False)     # True if has backlogs
    is_full_time = db.Column(db.Boolean, default=True)      # True if full-time student
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<Student {self.name}>'
    
    def to_dict(self):
        """Convert student object to dictionary for JSON response"""
        return {
            'id': self.id,
            'google_id': self.google_id,
            'name': self.name,
            'email': self.email,
            'profile_picture': self.profile_picture,
            'is_registered': self.is_registered,
            'course': self.course,
            'year_of_study': self.year_of_study,
            'marks_percentage': self.marks_percentage,
            'family_income': self.family_income,
            'category': self.category,
            'has_backlogs': self.has_backlogs,
            'is_full_time': self.is_full_time,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'last_login': self.last_login.strftime('%Y-%m-%d %H:%M:%S') if self.last_login else None
        }


class Scholarship(db.Model):
    """
    Scholarship model to store different scholarship programs
    Each scholarship can have its own set of eligibility rules
    """
    __tablename__ = 'scholarships'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    amount = db.Column(db.Float, nullable=False)            # Scholarship amount in INR
    is_active = db.Column(db.Boolean, default=True)         # Whether scholarship is active
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with rules
    rules = db.relationship('Rule', backref='scholarship', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Scholarship {self.name}>'
    
    def to_dict(self):
        """Convert scholarship object to dictionary for JSON response"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'amount': self.amount,
            'is_active': self.is_active,
            'rules': [rule.to_dict() for rule in self.rules],
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }


class Rule(db.Model):
    """
    Rule model to store eligibility criteria for each scholarship
    Rules are stored separately and can be modified by admin without changing code
    """
    __tablename__ = 'rules'
    
    id = db.Column(db.Integer, primary_key=True)
    scholarship_id = db.Column(db.Integer, db.ForeignKey('scholarships.id'), nullable=False)
    
    # Rule field - which student attribute to check
    # Options: marks_percentage, family_income, has_backlogs, is_full_time, category, year_of_study
    field = db.Column(db.String(50), nullable=False)
    
    # Operator for comparison
    # Options: >=, <=, ==, !=, >, <, in (for category lists)
    operator = db.Column(db.String(10), nullable=False)
    
    # Value to compare against (stored as string, converted during evaluation)
    value = db.Column(db.String(100), nullable=False)
    
    # Priority weight for scoring (higher = more important)
    weight = db.Column(db.Float, default=1.0)
    
    # Human-readable description of the rule
    description = db.Column(db.String(200))
    
    # Error message to display if rule fails
    error_message = db.Column(db.String(200))
    
    def __repr__(self):
        return f'<Rule {self.field} {self.operator} {self.value}>'
    
    def to_dict(self):
        """Convert rule object to dictionary for JSON response"""
        return {
            'id': self.id,
            'scholarship_id': self.scholarship_id,
            'field': self.field,
            'operator': self.operator,
            'value': self.value,
            'weight': self.weight,
            'description': self.description,
            'error_message': self.error_message
        }


class EligibilityResult(db.Model):
    """
    Store eligibility check results for tracking and dashboard
    """
    __tablename__ = 'eligibility_results'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    scholarship_id = db.Column(db.Integer, db.ForeignKey('scholarships.id'), nullable=False)
    is_eligible = db.Column(db.Boolean, nullable=False)
    priority_score = db.Column(db.Float, default=0.0)
    rejection_reasons = db.Column(db.Text)  # JSON string of rejection reasons
    checked_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    student = db.relationship('Student', backref='eligibility_results')
    scholarship = db.relationship('Scholarship', backref='eligibility_results')
    
    def __repr__(self):
        return f'<EligibilityResult Student:{self.student_id} Scholarship:{self.scholarship_id}>'
    
    def to_dict(self):
        """Convert result object to dictionary for JSON response"""
        import json
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.name if self.student else None,
            'scholarship_id': self.scholarship_id,
            'scholarship_name': self.scholarship.name if self.scholarship else None,
            'is_eligible': self.is_eligible,
            'priority_score': self.priority_score,
            'rejection_reasons': json.loads(self.rejection_reasons) if self.rejection_reasons else [],
            'checked_at': self.checked_at.strftime('%Y-%m-%d %H:%M:%S')
        }


class ScholarshipApplication(db.Model):
    """
    Model to track student applications for specific scholarships
    Students can apply to eligible scholarships one by one
    """
    __tablename__ = 'scholarship_applications'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    scholarship_id = db.Column(db.Integer, db.ForeignKey('scholarships.id'), nullable=False)
    
    # Application status: pending, approved, rejected, under_review, documents_requested
    status = db.Column(db.String(20), default='pending')
    
    # Admin notes for the application
    admin_notes = db.Column(db.Text)
    
    # Admin feedback requesting documents
    admin_feedback = db.Column(db.Text)
    documents_requested = db.Column(db.Boolean, default=False)
    
    # Timestamps
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=True)
    feedback_sent_at = db.Column(db.DateTime)
    
    # Is this notification read by admin?
    is_read = db.Column(db.Boolean, default=False)
    
    # Has student seen the feedback?
    feedback_read = db.Column(db.Boolean, default=False)
    
    # Relationships
    student = db.relationship('Student', backref='applications')
    scholarship = db.relationship('Scholarship', backref='applications')
    reviewer = db.relationship('Admin', backref='reviewed_applications')
    
    # Unique constraint - one application per student per scholarship
    __table_args__ = (db.UniqueConstraint('student_id', 'scholarship_id', name='unique_student_scholarship'),)
    
    def __repr__(self):
        return f'<Application Student:{self.student_id} Scholarship:{self.scholarship_id} Status:{self.status}>'
    
    def to_dict(self):
        """Convert application object to dictionary for JSON response"""
        # Include full student details for admin view
        student_details = None
        if self.student:
            student_details = {
                'id': self.student.id,
                'name': self.student.name,
                'email': self.student.email,
                'profile_picture': self.student.profile_picture,
                'course': self.student.course,
                'year_of_study': self.student.year_of_study,
                'marks_percentage': self.student.marks_percentage,
                'family_income': self.student.family_income,
                'category': self.student.category,
                'has_backlogs': self.student.has_backlogs,
                'is_full_time': self.student.is_full_time,
                'created_at': self.student.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.student.created_at else None
            }
        
        # Get document count
        doc_count = len(self.documents) if hasattr(self, 'documents') else 0
        
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.name if self.student else None,
            'student_email': self.student.email if self.student else None,
            'student_picture': self.student.profile_picture if self.student else None,
            'student_details': student_details,
            'scholarship_id': self.scholarship_id,
            'scholarship_name': self.scholarship.name if self.scholarship else None,
            'scholarship_amount': self.scholarship.amount if self.scholarship else None,
            'status': self.status,
            'admin_notes': self.admin_notes,
            'admin_feedback': self.admin_feedback,
            'documents_requested': self.documents_requested,
            'document_count': doc_count,
            'applied_at': self.applied_at.strftime('%Y-%m-%d %H:%M:%S') if self.applied_at else None,
            'reviewed_at': self.reviewed_at.strftime('%Y-%m-%d %H:%M:%S') if self.reviewed_at else None,
            'feedback_sent_at': self.feedback_sent_at.strftime('%Y-%m-%d %H:%M:%S') if self.feedback_sent_at else None,
            'is_read': self.is_read,
            'feedback_read': self.feedback_read
        }


class ApplicationDocument(db.Model):
    """
    Model to store documents uploaded by students for their applications
    """
    __tablename__ = 'application_documents'
    
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('scholarship_applications.id'), nullable=False)
    
    # Document details
    filename = db.Column(db.String(255), nullable=False)  # Original filename
    stored_filename = db.Column(db.String(255), nullable=False)  # Unique stored filename
    file_type = db.Column(db.String(50))  # pdf, jpg, png, etc.
    file_size = db.Column(db.Integer)  # Size in bytes
    document_type = db.Column(db.String(100))  # e.g., "Income Certificate", "Marksheet", etc.
    
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    application = db.relationship('ScholarshipApplication', backref='documents')
    
    def __repr__(self):
        return f'<Document {self.filename} for Application {self.application_id}>'
    
    def to_dict(self):
        """Convert document object to dictionary for JSON response"""
        return {
            'id': self.id,
            'application_id': self.application_id,
            'filename': self.filename,
            'stored_filename': self.stored_filename,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'document_type': self.document_type,
            'uploaded_at': self.uploaded_at.strftime('%Y-%m-%d %H:%M:%S') if self.uploaded_at else None
        }
