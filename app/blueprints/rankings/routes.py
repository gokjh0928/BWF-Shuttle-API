from flask import render_template, request, redirect, url_for, flash, send_file, json, jsonify, Response
from app.context_processor import db
import pandas as pd
import os
from .import bp as app
import math
from IPython.display import display
from io import StringIO
import time
import scores
from app import cache

# The path to the project's directory
path = os.getcwd()
# Dictionary with valid dates as keys and values being the ones used for getting the url
valid_dates = sorted(list(scores.getValidDates().keys()), reverse=True)
# Dict with keys formated like '{year}-{week}' and value being corresponding year/month/day
valid_weeks = scores.getWeeks()

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
    context = {
            # all possible dates from which to get information from BWF Website
            'dates': valid_dates
        }
    return render_template('ranking.html', **context)

@app.route('/tables', methods=['GET', 'POST'])
def table():
    if request.method == 'POST':
        category = request.form.get('category-select')
        num_rows = request.form.get('num-rows')
        num_rows = int(num_rows) if num_rows else 25
        date = request.form.get('date')

        # Check if entry for the date exists(not processed the latest ranking tables yet in database)
        if not db.child('dates').child(date).shallow().get().val():
            flash(f'Table for {date} does not exist', 'info')
            return redirect(url_for('rankings.home'))
        else:
            # if existing in database, generate ranking table
            df = generate_table(category, date, num_rows)

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
    return render_template('ranking-table.html')


@app.route('/players')
def players():
    return render_template('players.html')

@app.route('/download/<type>/<category>/<year>/<week>/<rows>')
def download(type, category, year, week, rows):
    """
    type - type of file to download(csv, json, etc)
    category - chosen badminton category
    year, week - chosen date to download from
    rows - number of rows
    Return: downloaded csv file that use wants
    """
    df = generate_table(category, valid_weeks[f'{year}-{week}'], rows)
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
        return jsonify(["Invalid Input"])

    
    


@app.route('/api/<category>', methods=['GET'])
@cache.cached(timeout=120)
def rank_category(category):
    """
    category - badminton category to view
    Return: json data containing 25 top players for the input category
    """
    date = valid_dates[0]
    if not db.child('dates').child(date).shallow().get().val():
        return jsonify(["Invalid Input"])
    data= generate_table(category, date, 25).to_json(orient='records')
    return jsonify(json.loads(data))


@app.route('/api/<category>/<rows>', methods=['GET'])
@cache.cached(timeout=120)
def rank_category_rows(category, rows):
    """
    category - badminton category to view
    rows - number of players to get
    Return: json containing top {rows} players for the input category
    """
    date = valid_dates[0]
    if not db.child('dates').child(date).shallow().get().val():
        return jsonify(["Invalid Input"])
    data = generate_table(category, date, int(rows)).to_json(orient='records')
    return jsonify(json.loads(data))


@app.route('/api/<category>/<year>/<week>/<rows>', methods=['GET'])
@cache.cached(timeout=120)
def rank_year_week(category, year, week, rows):
    """
    category - badminton category to view
    year - the year of the rankings to get
    rows - number of players to get
    Return: json containing top {rows} players for the input category
    """
    if f'{year}-{week}' not in valid_weeks.keys():
        return jsonify(["Invalid Input"])
    date = valid_weeks[f'{year}-{week}']
    if not db.child('dates').child(date).shallow().get().val():
        return jsonify(["Invalid Input"])
    data = generate_table(category, date, int(rows)).to_json(orient='records')
    return jsonify(json.loads(data))

@app.route('/api/<category>/<year>/<month>/<day>/<rows>', methods=['GET'])
@cache.cached(timeout=120)
def rank_ymd(category, year, month, day, rows):
    """
    category - badminton category to view
    rows - number of players to get
    Return: json containing top {rows} players for the input category
    """
    date = f'{year}/{month}/{day}'
    if not db.child('dates').child(date).shallow().get().val():
        return jsonify(["Invalid Input"])
    data = generate_table(category, date, int(rows)).to_json(orient='records')
    return jsonify(json.loads(data))



# @app.route('/seed')
# def seed():
#     date_dict = scores.getValidDates()
#     for date in valid_dates:
#         # Check if the database contains the data for this date
#         if not db.child('dates').child(date).shallow().get().val():
#             for category in ['MS', 'WS', 'MD', 'WD', 'XD']:
#                 print(f'Starting {category} {date}')
#                 result = scores.getTable(category, date_dict[date], categories[category]).to_json(orient='records')
#                 data = json.loads(result)
#                 db.child('dates').child(date).child(category).set(data)
#                 print(f'Done for {category} {date}')
#         # Since the dates are ordered, break once finding a date that is contained in database
#         else:
#             break
#     return render_template('home.html')

# <!-- <a href="{{ url_for('rankings.download', type='JSON') }}" class="btn btn-primary" role="button" aria-pressed="true">JSON</a> -->
#     <!-- <a href="{{ url_for('rankings.download', type='EXCEL') }}" class="btn btn-primary" role="button" aria-pressed="true">EXCEL</a> -->

@app.route('/upload')
def upload():
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
    print('test')
    if not db.child('dates').child('2021/08/17').shallow().get().val():
        print('date does not exist')
    else:
        print('date exists!')
    print('done')
    return render_template('home.html')


# Helper function for generating the ranking table, memoized for efficiency
@cache.memoize(300)
def generate_table(category, date, num_rows):
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
    return df