from flask import render_template, request, redirect, url_for, flash, session, json, Markup
from .import bp as app
from flask import current_app as curr_app
from app.context_processor import auth
from werkzeug.exceptions import HTTPException
from requests.exceptions import HTTPError

@app.route('/register', methods = ['GET', 'POST'])
def register():
    # auth.create_user_with_email_and_password(email, password)
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('psw')
        password_repeat = request.form.get('psw-repeat')
        if password != password_repeat:
            flash('Password and repeated password are not the same.', 'danger')
            return redirect(url_for('authentication.register'))
        auth.create_user_with_email_and_password(email, password)
        user = auth.sign_in_with_email_and_password(email, password)
        user = auth.refresh(user['refreshToken'])
        session['user'] = user['idToken']
        flash('Successfully created account', 'success')
        return redirect(url_for('main.home'))
    return render_template('register.html')

@app.route('/login', methods = ['GET', 'POST'])
def login():
    # Check if session has a previously logged in user that's already existing
    if request.method == "POST":
            try:
                email = request.form.get('email')
                password = request.form.get('psw')
                user = auth.sign_in_with_email_and_password(email, password)
                # idTokens expire after an hour so logging back in would need to refresh it
                user = auth.refresh(user['refreshToken'])
                # userId and idToken
                session['user'] = user['idToken']
            except:
                flash('Incorrect email or password')
            flash('Logged in successsfully', 'success')
            return redirect(url_for('main.home'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    if 'user' in session:
        session.pop('user', None)
        flash('Logged out successully', 'success')
    return render_template('login.html')

@app.route('/reset_password', methods = ['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        try:
            email = request.form.get('email')
            auth.send_password_reset_email(email)
            flash('Successfully sent password reset email to provided email', 'success')
            return render_template('home.html')
        except:
            flash('Account does not exist for this email!', 'info')
            return redirect(url_for('main.home'))
    return render_template('reset-password.html')

@app.errorhandler(Exception)
def handle_exception(e):
    """Return JSON instead of HTML for HTTP errors."""
    # start with the correct headers and status code from the error
    if isinstance(e, HTTPError):
        print('This is HTTP Error!')
        if json.loads(e.args[1])['error']['message'] == "EMAIL_EXISTS":
            flash(Markup('An account already exists for this email! <a href="/authentication/forgot_password" class="alert-link">Forgot Password</a>?'))
            return redirect(url_for("authentication.login"))