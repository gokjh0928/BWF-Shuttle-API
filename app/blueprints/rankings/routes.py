from flask import render_template, request, redirect, url_for, flash, send_file, json, jsonify
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
valid_dates = sorted(list(scores.getValidDates().keys()), reverse=True)

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
            flash('Date does not exist', 'info')
            return redirect(url_for('rankings.home'))
        else:
            # if existing in database, generate ranking table
            df = generate_table(category, date, num_rows)

            context = {
                'table': df.values,
                'category': category_full_name[request.form.get('category-select')],
                'category_abbr': request.form.get('category-select'),
                'date': date,
                'year': date[0],
                'week': date[1],
                'rows': num_rows
            }
            return render_template('ranking-table.html', **context)
    return render_template('ranking-table.html')


@app.route('/players')
def players():
    return render_template('players.html')

@app.route('/download/<type>/<category>/<year>/<week>/<rows>')
def download(type, category, year, week, rows):
    print(type, category, year, week, rows)
    # print(os.path.abspath(os.path.join(path, os.pardir)))
    path_to_file = path + f'/rankings/{category}/{category}_{date_file_name}.csv'
    
    return send_file(path + f'/rankings/{category}/{category}_{date_file_name}.csv',
                    mimetype='text/csv',
                    attachment_filename=f'{category}_{year}_{week}.csv',
                    as_attachment=True)

@app.route('/api/<category>/<year>/<month>/<day>/<rows>', methods=['GET'])
@cache.cached(timeout=120)
def rank(category, year, month, day, rows):
    date = f'{year}/{month}/{day}'
    if not db.child('dates').child(date).shallow().get().val():
        return {"Invalid Input"}
    df = generate_table(category, date, int(rows))
    result = df.to_json(orient='records')
    return jsonify(json.loads(result))



@app.route('/seed')
def seed():
    # Getting the CSV files
    date_dict = scores.getValidDates()
    dates = list(date_dict.keys())
    for date in dates:
        for category in ['MS', 'WS', 'MD', 'WD', 'XD']:
            date_file_name = '_'.join(date.split('/'))
            if not os.path.isfile(path + f'/rankings/{category}/{category}_{date_file_name}.csv'):
                print(f'Starting {category} {date}')
                print(date_dict[date])
                df = scores.getTable(category, date_dict[date], categories[category], 10000000)
                df.to_csv(path + f'/rankings/{category}/{category}_{date_file_name}.csv', index=False)
                print(f'Done for {category} {date}')
    return render_template('home.html')

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
        if idx >= num_rows:
            break
        player_dict = player.val()
        row = [ player_dict[col] for col in cols ]
        df.loc[idx] = row
    display(df)
    return df