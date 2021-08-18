import os
from dotenv import load_dotenv

basedir = os.path.dirname(__name__)
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    # The SECRET_KEY is in the .env file
    SECRET_KEY = os.getenv('SECRET_KEY')
    FLASK_APP = os.getenv('FLASK_APP')
    FLASK_ENV = os.getenv('FLASK_ENV')
    if os.getenv('SQLALCHEMY_DATABASE_URI').startswith('postgres'):
        SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI').replace('postgres', 'postgresql')
    SQLALCHEMY_TRACK_MODIFICATIONS = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS')

    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = os.getenv('MAIL_PORT')
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')

    FIREBASE_API_KEY=os.getenv('FIREBASE_API_KEY')
    FIREBASE_AUTH_DOMAIN=os.getenv('FIREBASE_AUTH_DOMAIN')
    FIREBASE_PROJECT_ID=os.getenv('FIREBASE_PROJECT_ID')
    FIREBASE_STORAGE_BUCKET=os.getenv('FIREBASE_STORAGE_BUCKET')
    FIREBASE_MESSAGING_SENDER_ID=os.getenv('FIREBASE_MESSAGING_SENDER_ID')
    FIREBASE_APP_ID=os.getenv('FIREBASE_APP_ID')
    FIREBASE_MEASUREMENT_ID=os.getenv('FIREBASE_MEASUREMENT_ID')
    FIREBASE_DATABASE_URL=os.getenv('FIREBASE_DATABASE_URL')
    


    