"""
Configuration settings for Scholarship Eligibility Filter
"""

import os

# Base directory of the application
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Secret key for session management
SECRET_KEY = 'scholarship-eligibility-secret-key-2024'

# Firebase Configuration
# Get these from Firebase Console > Project Settings > Service Accounts
FIREBASE_CONFIG = {
    'apiKey': "AIzaSyA_T_-f1rft1LOE84QlZMsQ3-zuXInn-WU",
    'authDomain': "scholarship-a4d06.firebaseapp.com",
    'databaseURL': "https://scholarship-a4d06-default-rtdb.firebaseio.com/",
    'projectId': "scholarship-a4d06",
    'storageBucket': "scholarship-a4d06.firebasestorage.app",
    'messagingSenderId': "874955088082",
    'appId': "1:874955088082:web:4dc2fcea6a10e1b3f8cd0b"
}

# Path to Firebase service account key JSON file
# Download from Firebase Console > Project Settings > Service Accounts > Generate New Private Key
FIREBASE_CREDENTIALS_PATH = os.path.join(BASE_DIR, 'firebase-credentials.json')

# Demo mode
DEMO_MODE = True
