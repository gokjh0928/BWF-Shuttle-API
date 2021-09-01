# import scores
# import os
# from dotenv import load_dotenv
# from pyrebase import pyrebase
# from flask import json
# import smtplib

# basedir = os.path.dirname(__name__)
# load_dotenv(os.path.join(basedir, '.env'))

# categories = {
#         'MS': '472',
#         'WS': '473', 
#         'MD': '474', 
#         'WD': '475', 
#         'XD': '476'
#         }

# # configure firebase database
# firebaseConfig = {
#     'apiKey': os.getenv('FIREBASE_API_KEY'),
#     'authDomain': os.getenv('FIREBASE_AUTH_DOMAIN'),
#     'databaseURL': os.getenv('FIREBASE_DATABASE_URL'),
#     'projectId': os.getenv('FIREBASE_PROJECT_ID'),
#     'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET'),
#     'messagingSenderId': os.getenv('FIREBASE_MESSAGING_SENDER_ID'),
#     'appId': os.getenv('FIREBASE_APP_ID'),
#     'measurementId': os.getenv('FIREBASE_MEASUREMENT_ID')
# }

# firebase = pyrebase.initialize_app(firebaseConfig)
# db = firebase.database()

# def seed():
#     date_dict = scores.getValidDates()
#     valid_dates = sorted(list(scores.getValidDates().keys()), reverse=True)
#     seeded_dates = []
#     for date in valid_dates:
#         # Check if the database contains the data for this date
#         if not db.child('dates').child(date).shallow().get().val():
#             for category in ['MS', 'WS', 'MD', 'WD', 'XD']:
#                 print(f'Starting {category} {date}')
#                 result = scores.getTable(category, date_dict[date], categories[category]).to_json(orient='records')
#                 data = json.loads(result)
#                 db.child('dates').child(date).child(category).set(data)
#                 print(f'Done for {category} {date}')
#             seeded_dates.append(date)
#         # Since the dates are ordered, break once finding a date that is contained in database
#         else:
#             break
#     if seeded_dates:
#         message = ', '.join(seeded_dates)
#         try:
#             mailserver = smtplib.SMTP(os.getenv('MAIL_SERVER'), os.getenv('MAIL_PORT'))
#             mailserver.ehlo()
#             mailserver.starttls()
#             mailserver.login(os.getenv('MAIL_USERNAME'), os.getenv('MAIL_PASSWORD'))
#             #Adding a newline before the body text fixes the missing message body
#             mailserver.sendmail(os.getenv('MAIL_USERNAME'),os.getenv('MAIL_USERNAME'), 
#                     f'\nSeeded New Data:\nSeeded Date(s): {message}\n')
#             mailserver.quit()
#         except:
#             return
#     return

# seed()
    