import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
SECRET_KEY = 'scholarship-eligibility-secret-key-2024'

FIREBASE_CONFIG = {
    'apiKey': "AIzaSyA_T_-f1rft1LOE84QlZMsQ3-zuXInn-WU",
    'authDomain': "scholarship-a4d06.firebaseapp.com",
    'databaseURL': "https://scholarship-a4d06-default-rtdb.firebaseio.com",
    'projectId': "scholarship-a4d06",
    'storageBucket': "scholarship-a4d06.firebasestorage.app",
    'messagingSenderId': "874955088082",
    'appId': "1:874955088082:web:4dc2fcea6a10e1b3f8cd0b"
}

FIREBASE_CREDENTIALS_PATH = os.path.join(BASE_DIR, 'firebase-credentials.json')
DEMO_MODE = True
