from flask import render_template, request, redirect, url_for, jsonify
from .import bp as app
from flask import current_app as curr_app
from app.context_processor import getDates, getWeeks
# Import smtplib for sending emails
import smtplib
from app import cache
from app import limiter


@app.route('/')
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
        # Replace the '/' with '_' to prevent errors in sending message
        message = message.replace('/', '_')
        #Adding a newline before the body text fixes the missing message body
        mailserver.sendmail(curr_app.config.get('MAIL_USERNAME'),curr_app.config.get('MAIL_USERNAME'), 
                f'\nFROM: {name}({email})\nSUBJECT: {subject}\n\n' + message)
        mailserver.quit()
        # print('Finish')  
        return render_template('success.html')
    except:
        return jsonify(["Something went wrong with sending the message. Please try again later!"])


@app.route('/faq', methods = ['GET', 'POST'])
def faq():
    return render_template('faq.html')