from flask import current_app as curr_app
from pyrebase import pyrebase
import scrape_table
from app import cache

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

# Memoize dates
@cache.memoize(timeout=600)
def getDates():
    # Dictionary with valid dates as keys and values being the ones used for getting the url
    valid_dates = sorted([week.val()['ymd_date'] for week in db.child('weeks').get().each()], reverse=True)
    return valid_dates

# Memoize weeks
@cache.memoize(timeout=600)
def getWeeks():
    # Dict with keys formated like '{year}-{week}' and value being corresponding year/month/day
    valid_weeks = sorted(db.child('weeks').shallow().get().val(), reverse=True)
    return valid_weeks
