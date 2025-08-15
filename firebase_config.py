import os
import firebase_admin
from firebase_admin import credentials, db

# Choose mode: Offline Emulator or Live Firebase Cloud
USE_EMULATOR = os.getenv('USE_FIREBASE_EMULATOR', 'false').lower() == 'true'

if USE_EMULATOR:
    print("🔥 Running Firebase Emulator (Offline Mode)")
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'http://localhost:8080'  # Offline Firebase Emulator
    })
else:
    print("☁️ Connecting to Live Firebase Cloud")
    cred = credentials.Certificate("config/attendance-system-44e2d-firebase-adminsdk-fbsvc-6abcc96cb1.json")  # Live Firebase key
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://your-firebase-project.firebaseio.com'
    })

# Reference Firebase database
attendance_ref = db.reference("attendance")
