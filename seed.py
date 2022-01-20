from scrape_table import getTable
import os, shutil
from dotenv import load_dotenv
from pyrebase import pyrebase
from flask import json
import smtplib
import time
import requests
from bs4 import BeautifulSoup

load_dotenv('/home/jaybaekimchi/BWF-Shuttle-API/.env')

categories = {
        'MS': '472',
        'WS': '473',
        'MD': '474',
        'WD': '475',
        'XD': '476'
        }

# configure firebase database(change serviceAccount to correct one before pushing code)
firebaseConfig = {
    'apiKey': os.getenv('FIREBASE_API_KEY'),
    'authDomain': os.getenv('FIREBASE_AUTH_DOMAIN'),
    'databaseURL': os.getenv('FIREBASE_DATABASE_URL'),
    'projectId': os.getenv('FIREBASE_PROJECT_ID'),
    'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET'),
    "serviceAccount": "/home/jaybaekimchi/BWF-Shuttle-API/serviceAccountCredentials.json",
    # "serviceAccount": "./serviceAccountCredentials.json",
    'messagingSenderId': os.getenv('FIREBASE_MESSAGING_SENDER_ID'),
    'appId': os.getenv('FIREBASE_APP_ID'),
    'measurementId': os.getenv('FIREBASE_MEASUREMENT_ID')
}

firebase = pyrebase.initialize_app(firebaseConfig)
db = firebase.database()

def getValidDates():
    """Gets Year/Month/Day dates for each ranking table, and gets 
    unique value for each date. The values will be used in URL for later 
    scraping ranking table as 'date-value'.
    
    Return: dict with Year/Month/Day dates as keys and associated special values
    """
    page = requests.get("https://bwf.tournamentsoftware.com/ranking/ranking.aspx?id=1078")
    soup = BeautifulSoup(page.content, 'html.parser')

    # dictionary containing all possible dates along with the associated value to get the URL
    date_dict = {}
    for date in soup.find_all("option"):
        if '/' not in date.text:
            break
        year = date.text.split('/')[2]
        month = date.text.split('/')[0]
        day = date.text.split('/')[1]
        if len(month) == 1:
            month = '0' + month
        if len(day) == 1:
            day = '0' + day
        date_str = f'{year}/{month}/{day}'
        if date_str == '2010/01/21' and date_str in date_dict:
            date_str = '2009/10/01'
        date_dict[date_str] = date['value']
    return date_dict


def recentWeeks():
    """Uses Selenium headless driver to scrape Year-Week data from BWF Fansite
    
    Return: dict with key:value being Year/Month/Day:Year-Week
    """
    # headless webdriver to get the Prize Money, Titles/Finals after clicking links
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=chrome_options)
    valid_weeks = {}

    driver.get('https://bwfbadminton.com/rankings/')
    driver.find_elements_by_css_selector('div.v-input__icon.v-input__icon--append')[1].click()
    time.sleep(8)
    max_num_tries = 10
    weeks = driver.find_elements_by_css_selector('div.v-list-item__title')
    while max_num_tries > 0 and (weeks[0].text.strip() == '' or weeks[0].text.strip() == 'No data available'):
        time.sleep(1)
        weeks = driver.find_elements_by_css_selector('div.v-list-item__title')
        max_num_tries -= 1
    for week in weeks:
        # week number
        year = week.text.strip().split()[2][1:-1].split('-')[0]
        num_week = week.text.strip().split()[1]
        # list with year, month, day
        ymd_date = week.text.strip().split()[2][1:-1].replace('-', '/')

        valid_weeks[ymd_date] = f'{year}-{num_week}'
#         print([date.text.strip() for date in dates])
#     valid_weeks["2009-40"] = "2009/10/01"
    return valid_weeks


def seed():
    """Gets Year/Month/Day dates from BWF Tournament Software website, and
    connects to Year/Week dates from BWF Fansite as Key-Value pairs.
    Scrape ranking tables for each category(MS,WS,MD,WD,XD) until 
    reaching a previously scraped date.
    """
    number_of_seeded_dates = 0
    date_dict = getValidDates()
    recent_weeks = recentWeeks()
    valid_dates = sorted(list(getValidDates().keys()), reverse=True)
    invalid_dates = []
    seeded_dates = []
    for date in valid_dates:
        print('==================================================================')
        print('Date is', date)
        print('==================================================================')
        # Check if year/month/day date is a key in recent_weeks dict and has an associated valid year-week value
        if date in recent_weeks:
            print(f'{recent_weeks[date]} is a valid and recent week')
            # Now check if the associated week is in database, and add it if it's not yet in there
            if not db.child('weeks').child(recent_weeks[date]).shallow().get().val():
                print(f'Adding {recent_weeks[date]} to weeks for {date}')
                db.child('weeks').child(recent_weeks[date]).set({
                    'ymd_date': date
                })
            else:
                print(f'{recent_weeks[date]} is already in database')
            # Check if the database contains the data for this date
            if not db.child('dates').child(date).shallow().get().val():
                print(f'Scraping tables for {date}')
                for category in ['MS', 'WS', 'MD', 'WD', 'XD']:
                    print(f'Starting {category} {date}')
                    result = getTable(category, date_dict[date], categories[category]).to_json(orient='records')
                    data = json.loads(result)
                    db.child('dates').child(date).child(category).set(data)
                    print(f'Done for {category} {date}')
                seeded_dates.append(date)
                number_of_seeded_dates += 1
            # Since the dates are ordered, break once finding a date that is contained in database
            else:
                print(f'Date {date} is in database. Stopping seeding.')
                break
        else:
            print(f'Date {date} is in Tournament Software, but not in BWF Fansite.')
            invalid_dates.append(date)

    # If there are any dates that don't have associated weeks in BWF Fansite, then send email alert
    if invalid_dates:
        recent_weeks_str = json.dumps(recent_weeks, indent=4)
        try:
            mailserver = smtplib.SMTP(os.getenv('MAIL_SERVER'), os.getenv('MAIL_PORT'))
            mailserver.ehlo()
            mailserver.starttls()
            mailserver.login(os.getenv('MAIL_USERNAME'), os.getenv('MAIL_PASSWORD'))
            # Adding a newline before the body text fixes the missing message body
            mailserver.sendmail(os.getenv('MAIL_USERNAME'),os.getenv('ALT_MAIL'),
                    f'\nWarning! Dates {invalid_dates} not in recent weeks!\nRecent weeks are\n{recent_weeks_str}\n')
            mailserver.quit()
        except:
            pass

    if seeded_dates:
        print(f'Found additional seeded data. Seeded {number_of_seeded_dates} date(s)')
        message = ', '.join(seeded_dates)
        try:
            mailserver = smtplib.SMTP(os.getenv('MAIL_SERVER'), os.getenv('MAIL_PORT'))
            mailserver.ehlo()
            mailserver.starttls()
            mailserver.login(os.getenv('MAIL_USERNAME'), os.getenv('MAIL_PASSWORD'))
            #Adding a newline before the body text fixes the missing message body
            mailserver.sendmail(os.getenv('MAIL_USERNAME'),os.getenv('ALT_MAIL'),
                    f'\nSeeded New Data:\nSeeded Date(s): {message}\n')
            mailserver.quit()
        except:
            return
    else:
        print("Found no data to seed as of this moment.")
    # Clearing tmp folder in PythonAnywhere post-Selenium scraping 
    try:
        dir = '/tmp'
        for files in os.listdir(dir):
            path = os.path.join(dir, files)
            try:
                shutil.rmtree(path)
            except OSError:
                os.remove(path)
        print("Deleted tmp folder after running Selenium")
    except:
        print("Failed to clear the tmp folder")
    return

seed()
