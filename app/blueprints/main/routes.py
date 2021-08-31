from flask import render_template, request, redirect, url_for, flash, jsonify
from .import bp as app
from flask import current_app as curr_app
import scores
# Import smtplib for sending emails
import smtplib
from app import cache
from app import limiter


@app.route('/')
@cache.cached(timeout=180)
def home():
    valid_dates = getDates()
    valid_weeks = getWeeks()
    context = {
            # all possible dates from which to get information from BWF Website
            'categories': ['MS', 'WS', 'MD', 'WD', 'XD'],
            'dates': valid_dates,
            'weeks': valid_weeks.keys()
        }
    return render_template('home.html', **context)

@app.route('/contact', methods = ['GET', 'POST'])
def contact():
    if request.method == "POST":
        name = request.form.get('input-name')
        email = request.form.get('input-email')
        subject = request.form.get('input-subject')
        message = request.form.get('input-message')
        return redirect(url_for('main.send_message', name=name, email=email, subject=subject, message=message))
    return render_template('contact.html')

@app.route('/contact/success')
def success():
    return render_template('success.html')

# Limit messages sent to BWF Shuttle API's email to 3 per day to prevent spam
@app.route('/contact/send_message/<name>_<email>_<subject>_<message>')
@limiter.limit(f"3/day", error_message=f'Please limit messages to 5/day')
def send_message(name, email, subject, message):
    try:
        mailserver = smtplib.SMTP(curr_app.config.get('MAIL_SERVER'), curr_app.config.get('MAIL_PORT'))
        mailserver.ehlo()
        mailserver.starttls()
        mailserver.login(curr_app.config.get('MAIL_USERNAME'), curr_app.config.get('MAIL_PASSWORD'))
        #Adding a newline before the body text fixes the missing message body
        mailserver.sendmail(curr_app.config.get('MAIL_USERNAME'),curr_app.config.get('MAIL_USERNAME'), 
                f'\nFROM: {name}({email})\nSUBJECT: {subject}\n\n' + message)
        mailserver.quit()
        # print('Finish')  
        return render_template('success.html')
    except:
        return jsonify(["Something went wrong with sending the message. Please try again later!"])



# Memoize dates
@cache.memoize(timeout=600)
def getDates():
    # Dictionary with valid dates as keys and values being the ones used for getting the url
    valid_dates = sorted(list(scores.getValidDates().keys()), reverse=True)
    return valid_dates

# Memoize weeks
@cache.memoize(timeout=600)
def getWeeks():
    # Dict with keys formated like '{year}-{week}' and value being corresponding year/month/day
    valid_weeks = scores.getWeeks()
    return valid_weeks