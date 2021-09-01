from flask import render_template, request, redirect, url_for, flash, Markup, session, json, jsonify, Response
from app.context_processor import db, auth, getDates, getWeeks
import pandas as pd
import os
from .import bp as app
# from IPython.display import display
from app import cache
from app import limiter



# The path to the project's directory
path = os.getcwd()

# this is the altered dataframe from the dynamic table that will be available for download

# limits number of api_calls allowed to prevent DDOS style attacks
per_day = 3000
per_minute = 80


# Values used to get URL of chosen category
categories = {
        'MS': '472',
        'WS': '473', 
        'MD': '474', 
        'WD': '475', 
        'XD': '476'
        }

category_full_name = {
        'MS': 'Mens Singles',
        'WS': 'Womens Singles', 
        'MD': 'Mens Doubles', 
        'WD': 'Womens Doubles', 
        'XD': 'Mixed Doubles'
        }

@app.route('/')
def home():
    valid_dates = getDates()
    context = {
            # all possible dates from which to get information from BWF Website
            'dates': valid_dates
        }
    return render_template('ranking.html', **context)

@app.route('/tables', methods=['GET', 'POST'])
@limiter.limit(f"{per_day}/day;{per_minute}/minute", error_message=f'Please limit API calls to {per_day}/day, {per_minute}/minute')
def table():
    if request.method == 'POST':
        # Require user to be logged in to use the table functionality
        if 'user' not in session:
            flash("Please log in on the website before accessing data.", 'info')
            return redirect(url_for('rankings.home'))
        # See if the user's token has expired, and if so, refresh to get a new one
        try:
            auth.get_account_info(session['user'])
        except:
            session['user'] = auth.refresh(session['refreshToken'])['idToken']
        if not auth.get_account_info(session['user'])['users'][0]['emailVerified']:
            flash(Markup('Please verify your account before viewing table. <a href="/authentication/resend_verification" class="alert-link">Resend Verification</a>?'), 'info')
            return redirect(url_for('rankings.home'))
        category = request.form.get('category-select')
        num_rows = request.form.get('num-rows')
        num_rows = num_rows if num_rows else '25'
        date = request.form.get('date')

        # Check if entry for the date exists(not processed the latest ranking tables yet in database)
        if not db.child('dates').child(date).shallow().get().val():
            flash(f'Table for {date} does not exist', 'info')
            return redirect(url_for('rankings.home'))
        else:
            # if existing in database, generate ranking table
            df = generate_table(category, date, num_rows)
            valid_weeks = getWeeks()
            # Make sure to clear previous info that altered tables, since we're getting a new table
            for altering_term in ['search', 'ascending', 'descending']:
                if altering_term in session:
                    session.pop(altering_term)
            context = {
                'table': df.values,
                'category': category_full_name[request.form.get('category-select')],
                'category_abbr': request.form.get('category-select'),
                'date': date,
                'year': date[:4],
                'week': (list(valid_weeks.keys())[list(valid_weeks.values()).index(date)]).split('-')[1],
                'rows': num_rows
            }
            return render_template('ranking-table.html', **context)
    return render_template('empty-ranking-table.html')


@app.route('/players')
def players():
    return render_template('players.html')

@app.route('/download/<type>/<altered>/<category>/<year>/<week>/<rows>')
@limiter.limit(f"{per_day}/day;{per_minute}/minute", error_message=f'Please limit API calls to {per_day}/day, {per_minute}/minute')
def download(type, altered, category, year, week, rows):
    """
    type - type of file to download(csv, json, etc)
    category - chosen badminton category
    year, week - chosen date to download from
    rows - number of rows
    Return: downloaded csv file that use wants
    """
    if 'user' not in session:
        flash("Please log in on the website before downloading data.", 'info')
        return redirect(url_for('rankings.home'))
    # See if the user's token has expired, and if so, refresh to get a new one
    try:
        auth.get_account_info(session['user'])
    except:
        session['user'] = auth.refresh(session['refreshToken'])['idToken']
    if not auth.get_account_info(session['user'])['users'][0]['emailVerified']:
        flash(Markup('Please verify your account before downloading data. <a href="/authentication/resend_verification" class="alert-link">Resend Verification</a>?'), 'info')
        return redirect(url_for('rankings.home'))
    valid_weeks = getWeeks()
    df = generate_table(category, valid_weeks[f'{year}-{week}'], rows)
    # If we want to download the altered table
    if altered == "True":
        # Check if the user made any changes to the table and reflect those changes
        if ('search' in session) or ('ascending' in session) or ('descending' in session):
            if session['search']:
                if category in ['MS', 'WS']:
                    df = df[df.drop('profile_link', axis=1).apply(lambda row: row.astype(str).str.contains(session['search'], case=False).any(), axis=1)]
                elif category in ['MD', 'WD', 'XD']:
                    df = df[df.drop(['profile_link1', 'profile_link2'], axis=1).apply(lambda row: row.astype(str).str.contains(session['search'], case=False).any(), axis=1)]
            if 'ascending' in session:
                col_name = session['ascending']
                if col_name in ['player', 'player1', 'player2']:
                    df.sort_values(by=col_name, ascending=True, inplace=True, key=lambda col: col.str.lower())
                elif col_name != 'rank':
                    df.sort_values(by=[col_name, 'rank'], ascending=[True, True], inplace=True)
                else:
                    df.sort_values(by='rank', ascending=True, inplace=True)
            if 'descending' in session:
                col_name = session['descending']
                if col_name in ['player', 'player1', 'player2']:
                    df.sort_values(by=col_name, ascending=False, inplace=True, key=lambda col: col.str.lower())
                elif col_name != 'rank':
                    df.sort_values(by=[col_name, 'rank'], ascending=[False, True], inplace=True)
                else:
                    df.sort_values(by='rank', ascending=False, inplace=True)
    if type == 'csv':
        file = df.to_csv(index=False)
        return Response(
            file,
            mimetype="text/csv",
            headers={"Content-disposition":
                    f"attachment; filename={category}_{year}_{week}.csv"})        
    elif type == 'json':
        data = df.to_json(orient='records')
        file = jsonify(json.loads(data))
        file.headers['Content-Disposition'] = f'attachment;filename={category}_{year}_{week}.json'
        return file
    else:
        # Catching any other error by doing nothing
        return ('', 204)
    

    
@app.route('/table/<category>/<year>/<month>/<day>/<rows>', methods=['GET'])
@limiter.limit(f"{per_day}/day;{per_minute}/minute", error_message=f'Please limit API calls to {per_day}/day, {per_minute}/minute')
def flask_table(category, year, month, day, rows):
    date = f'{year}/{month}/{day}'
    df = generate_table(category, date, rows)
    # This allows for the altered dataframe to be initialized as the original dataframe
    if isinstance(df, pd.DataFrame): 
        search = request.args.get('search[value]')
        # Save search in session to reflect changes when downloading altered table
        session['search'] = search
        total_records = len(df)
        if search:
            if category in ['MS', 'WS']:
                df = df[df.drop('profile_link', axis=1).apply(lambda row: row.astype(str).str.contains(search, case=False).any(), axis=1)]
            elif category in ['MD', 'WD', 'XD']:
                df = df[df.drop(['profile_link1', 'profile_link2'], axis=1).apply(lambda row: row.astype(str).str.contains(search, case=False).any(), axis=1)]
        total_filtered = len(df)
        order = []
        i = 0
        while True:
            col_index = request.args.get(f'order[{i}][column]')
            if col_index is None:
                break
            col_name = request.args.get(f'columns[{col_index}][data]')
            if col_name not in ['player', 'player1', 'player2', 'country', 'rank', 'rank_change', 'prev_rank', 'points', 'tournaments']:
                col_name = 'rank'
            descending = request.args.get(f'order[{i}][dir]') == 'desc'
            if descending:
                if col_name in ['player', 'player1', 'player2']:
                    df.sort_values(by=col_name, ascending=False, inplace=True, key=lambda col: col.str.lower())
                elif col_name != 'rank':
                    df.sort_values(by=[col_name, 'rank'], ascending=[False, True], inplace=True)
                else:
                    df.sort_values(by='rank', ascending=False, inplace=True)
                # Save changes to dataframe in session to reflect changes when downloading altered table
                if 'ascending' in session:
                    session.pop('ascending')
                session['descending'] = col_name
            else:
                if col_name in ['player', 'player1', 'player2']:
                    df.sort_values(by=col_name, ascending=True, inplace=True, key=lambda col: col.str.lower())
                elif col_name != 'rank':
                    df.sort_values(by=[col_name, 'rank'], ascending=[True, True], inplace=True)
                else:
                    df.sort_values(by='rank', ascending=True, inplace=True)
                # Save changes to dataframe in session to reflect changes when downloading altered table
                if 'descending' in session:
                    session.pop('descending')
                session['ascending'] = col_name
            i += 1
        start = request.args.get('start', type=int)
        length = request.args.get('length', type=int)
        df = df[start:start+length]
        # response
        return {
            'data': df.to_dict('records'),
            'recordsFiltered': total_filtered,
            'recordsTotal': total_records,
            'draw': request.args.get('draw', type=int)
        } 


@app.route('/api/<category>', methods=['GET'])
@limiter.limit(f"{per_day}/day;{per_minute}/minute", error_message=f'Please limit API calls to {per_day}/day, {per_minute}/minute')
def rank_category(category):
    """
    category - badminton category to view
    Return: json data containing current 25 top players for the input category
    """
    # error_message = not_verified()
    # if error_message:
    #     return jsonify(error_message)
    date = getDates()[0]
    df = generate_table(category, date, '25')
    if isinstance(df, pd.DataFrame): 
        data = df.to_json(orient='records')
    else:
        return jsonify(["Invalid Input!"])
    return jsonify(json.loads(data))


@app.route('/api/<category>/<rows>', methods=['GET'])
@limiter.limit(f"{per_day}/day;{per_minute}/minute", error_message=f'Please limit API calls to {per_day}/day, {per_minute}/minute')
def rank_category_rows(category, rows):
    """
    category - badminton category to view
    rows - number of players to get
    Return: json containing current top {rows} players for the input category
    """
    # error_message = not_verified()
    # if error_message:
    #     return jsonify(error_message)
    date = getDates()[0]
    df = generate_table(category, date, rows)
    if isinstance(df, pd.DataFrame): 
        data = df.to_json(orient='records')
    else:
        return jsonify(["Invalid Input!"])
    return jsonify(json.loads(data))


@app.route('/api/<category>/<year>/<week>/<rows>', methods=['GET'])
@limiter.limit(f"{per_day}/day;{per_minute}/minute", error_message=f'Please limit API calls to {per_day}/day, {per_minute}/minute')
def rank_year_week(category, year, week, rows):
    """
    category - badminton category to view
    year - the year of the rankings to get
    rows - number of players to get
    Return: json containing top {rows} players for the input category for chosen year
    """
    # error_message = not_verified()
    # if error_message:
    #     return jsonify(error_message)
    valid_weeks = getWeeks()
    if f'{year}-{week}' not in valid_weeks.keys():
        return jsonify(["Invalid Input"])
    valid_weeks = getWeeks()
    date = valid_weeks[f'{year}-{week}']
    df = generate_table(category, date, rows)
    if isinstance(df, pd.DataFrame): 
        data = df.to_json(orient='records')
    else:
        return jsonify(["Invalid Input!"])
    return jsonify(json.loads(data))

@app.route('/api/<category>/<year>/<month>/<day>/<rows>', methods=['GET'])
@limiter.limit(f"{per_day}/day;{per_minute}/minute", error_message=f'Please limit API calls to {per_day}/day, {per_minute}/minute')
def rank_ymd(category, year, month, day, rows):
    """
    category - badminton category to view
    rows - number of players to get
    Return: json containing top {rows} players for the input category for chosen year
    """
    # error_message = not_verified()
    # if error_message:
    #     return jsonify(error_message)
    date = f'{year}/{month}/{day}'
    df = generate_table(category, date, rows)
    if isinstance(df, pd.DataFrame):
        data = df.to_json(orient='records')
    else:
        return jsonify(["Invalid Input!"])
    return jsonify(json.loads(data))



# @app.route('/seed')
# def seed():
#     date_dict = scores.getValidDates()
#     seed_flag = False
#     for date in valid_dates:
#         # Check if the database contains the data for this date
#         if not db.child('dates').child(date).shallow().get().val():
#             for category in ['MS', 'WS', 'MD', 'WD', 'XD']:
#                 print(f'Starting {category} {date}')
#                 result = scores.getTable(category, date_dict[date], categories[category]).to_json(orient='records')
#                 data = json.loads(result)
#                 db.child('dates').child(date).child(category).set(data)
#                 print(f'Done for {category} {date}')
#             seed_flag = True
#         # Since the dates are ordered, break once finding a date that is contained in database
#         else:
#             break
#     if seed_flag:
#         print("Successfully seeded new data!")
#     else:
#         print("Nothing to seed. Everything is up to date!")
#     return render_template('home.html')


# @app.route('/upload')
# def upload():
    # The next two lines delete everything in the database
    # for date in valid_dates:
    #     db.child('dates').child(date).remove()

    # Uploading every csv file onto firebase database
    # for date in valid_dates:
    #     date_file_name = '_'.join(date.split('/'))
    #     for category in ['MS','WS','MD','WD','XD']:
    #         df = pd.read_csv(path + f'/rankings/{category}/{category}_{date_file_name}.csv')
    #         result = df.to_json(orient='records')
    #         data = json.loads(result)
    #         db.child('dates').child(date).child(category).set(data)

    # for thing in db.child('dates').child('2021/08/17').child('MD').child('0').get().each():
    #     print(thing.key())
    #     print(thing.val())

    # how to check if a child exists
    # print('test')
    # if not db.child('dates').child('2021/08/17').shallow().get().val():
    #     print('date does not exist')
    # else:
    #     print('date exists!')
    # print('done')
    # return render_template('home.html')


# Helper function for generating the ranking table, memoized for efficiency
@cache.memoize(timeout=600)
def generate_table(category, date, num_rows):
    # Check if data for date exists, if category is valid, and if number of rows is a number
    if (not db.child('dates').child(date).shallow().get().val()) or (not num_rows.isnumeric()) or (category not in categories.keys()):
        return None
    players = db.child('dates').child(date).child(category).get()
    if category in ['MS', 'WS']:
        cols = ['rank', 'rank_change', 'prev_rank', 'country', 'player', 'member_id', 'points', 'tournaments', 'profile_link']
    else:
        cols = ['rank', 'rank_change', 'prev_rank', 'country', 'player1', 'player2', 'member_id1', 'member_id2', 'points', 'tournaments', 'profile_link1', 'profile_link2']
    df = pd.DataFrame(columns=cols)
    for idx, player in enumerate(players.each()):
        if idx >= int(num_rows):
            break
        player_dict = player.val()
        row = [ player_dict[col] for col in cols ]
        df.loc[idx] = row
    # display(df)
    df = df.astype({'rank': 'int32', 
                    'rank_change': 'int32', 
                    'prev_rank': 'int32',
                    'points': 'int32',
                    'tournaments': 'int32'})
    return df

def not_verified():
    if 'user' not in session:
        return ["Please log in on the website before accessing data!"]
    # See if the user's token has expired, and if so, refresh to get a new one
    try:
        auth.get_account_info(session['user'])
    except:
        session['user'] = auth.refresh(session['refreshToken'])['idToken']
    if not auth.get_account_info(session['user'])['users'][0]['emailVerified']:
        return ["Please verify your account before accessing data!", {"Resend Verification": "http://127.0.0.1:5000/authentication/resend_verification"}]
    return []
