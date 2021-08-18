from flask import current_app as curr_app
from pyrebase import pyrebase

# configure firebase database
firebaseConfig = {
    'apiKey': curr_app.config.get('FIREBASE_API_KEY'),
    'authDomain': curr_app.config.get('FIREBASE_AUTH_DOMAIN'),
    'databaseURL': curr_app.config.get('FIREBASE_DATABASE_URL'),
    'projectId': curr_app.config.get('FIREBASE_PROJECT_ID'),
    'storageBucket': curr_app.config.get('FIREBASE_STORAGE_BUCKET'),
    'messagingSenderId': curr_app.config.get('FIREBASE_MESSAGING_SENDER_ID'),
    'appId': curr_app.config.get('FIREBASE_APP_ID'),
    'measurementId': curr_app.config.get('FIREBASE_MEASUREMENT_ID')
}

firebase = pyrebase.initialize_app(firebaseConfig)

auth = firebase.auth()
db = firebase.database()
storage = firebase.storage()