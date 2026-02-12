"""
Configuration settings for Scholarship Eligibility Filter
"""

import os

# Base directory of the application
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Database configuration
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'scholarship.db')
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Secret key for session management
SECRET_KEY = 'scholarship-eligibility-secret-key-2024'

# Google OAuth Configuration
# To get these credentials:
# 1. Go to https://console.cloud.google.com/
# 2. Create a new project or select existing
# 3. Enable Google+ API
# 4. Go to Credentials > Create Credentials > OAuth Client ID
# 5. Set Authorized redirect URI to: http://localhost:5000/admin/google/callback
GOOGLE_CLIENT_ID = '614974869577-deg382b8fhal3ir3f12v9p150bb15j4h.apps.googleusercontent.com'
GOOGLE_CLIENT_SECRET = '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'
GOOGLE_DISCOVERY_URL = 'https://accounts.google.com/.well-known/openid-configuration'

# For development/demo mode - set to True to allow any Google account
# Set to False in production and use the registration system
DEMO_MODE = True

# Use simulated authentication (for development without Google OAuth setup)
# Set to False once you have real Google OAuth credentials configured properly
USE_SIMULATED_AUTH = False

# Separate control for student simulated auth (useful if admin needs simulated but students use real OAuth)
# Set to False to use real Google OAuth for students
USE_SIMULATED_AUTH_STUDENT = False
