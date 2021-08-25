from flask import render_template, request, redirect, url_for, flash
from .import bp as app
from flask import current_app as curr_app
# Import smtplib for sending emails
import smtplib

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/contact', methods = ['GET', 'POST'])
def contact():
    if request.method == "POST":
        print("POSTING")
        name = request.form.get('input-name')
        email = request.form.get('input-email')
        subject = request.form.get('input-subject')
        message = request.form.get('input-message')
        
        try:
            # print('Start')
            mailserver = smtplib.SMTP(curr_app.config.get('MAIL_SERVER'), curr_app.config.get('MAIL_PORT'))
            mailserver.ehlo()
            mailserver.starttls()
            mailserver.login(curr_app.config.get('MAIL_USERNAME'), curr_app.config.get('MAIL_PASSWORD'))
            #Adding a newline before the body text fixes the missing message body
            mailserver.sendmail(curr_app.config.get('MAIL_USERNAME'),curr_app.config.get('MAIL_USERNAME'), 
                    f'\nFROM: {name}({email})\nSUBJECT: {subject}\n\n' + message)
            mailserver.quit()
            # print('Finish')  
            flash('Successfully sent email!', 'success')
            return redirect(url_for('main.contact'))
        except:
            flash('Something went wrong...', 'danger')
            return redirect(url_for('main.contact'))
    return render_template('contact.html')

@app.route('/contact/success')
def success():
    return render_template('success.html')