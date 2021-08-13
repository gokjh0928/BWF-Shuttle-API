from flask import render_template, request, redirect, url_for, flash, send_file
import pandas as pd
import os
from .import bp as app
import math
from IPython.display import display
from io import StringIO
import time
import scores
# The path to the project's directory
path = os.getcwd()

valid_dates = scores.valid_dates

categories = {
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
        if num_rows:
            num_rows = int(num_rows)
        date = (request.form.get('date').split(' ')[0][:4], request.form.get('date').split(' ')[-1][:-1])
        # If the csv file already exists for the given date
        if os.path.isfile(path + f'/rankings/{category}/{category}_{date[0]}_{date[1]}.csv'):
            time.sleep(4)
            print('File exists!!!!')
            df = pd.read_csv(path + f'/rankings/{category}/{category}_{date[0]}_{date[1]}.csv', header=0)
            df = df[:int(num_rows)] if num_rows else df[:25]
        # Else, we should create a csv file for this date(storing it in rankings folder for later use)
        else:    
            # If number of rows was specified
            if num_rows:
                csv_string = scores.getTable(category, date[0], date[1], int(math.ceil(num_rows / 100.0)) * 100)
                df = pd.read_csv(StringIO(csv_string), header=0)[:num_rows]
            # else, default is 25 rows
            else:
                csv_string = scores.getTable(category, date[0], date[1])
                df = pd.read_csv(StringIO(csv_string), header=0)[:25]
            df['change_+/-'] = df['change_+/-'].map(lambda x: '+' + str(x) if (str(x) != '0' and '-' not in str(x)) else str(x))
        context = {
            'table': df.values,
            'category': categories[request.form.get('category-select')],
            'category_abbr': request.form.get('category-select'),
            'date': request.form.get('date').split(' ')[0],
            'year': date[0],
            'week': date[1],
            'rows': num_rows if num_rows else 25
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
    print(path)

    return send_file(path + f'/rankings/{category}/{category}_{year}_{week}.csv',
                     mimetype='text/csv',
                     attachment_filename=f'{category}_{year}_{week}.csv',
                     as_attachment=True)

@app.route('/seed')
def seed():
    for date in scores.valid_dates:
        date = (date[0].split(' ')[0][:4], date[1].split(' ')[-1][:-1])
        for category in ['MS', 'WS', 'MD', 'WD', 'XD']:
            if not os.path.isfile(path + f'/rankings/{category}/{category}_{date[0]}_{date[1]}.csv'):
                print(f'Starting {category} {date}')
                scores.getTable(category, int(date[0]), int(date[1]), 10000000)
                print(f'Done for {category} {date}')
    return render_template('home.html')

# <!-- <a href="{{ url_for('rankings.download', type='JSON') }}" class="btn btn-primary" role="button" aria-pressed="true">JSON</a> -->
#     <!-- <a href="{{ url_for('rankings.download', type='EXCEL') }}" class="btn btn-primary" role="button" aria-pressed="true">EXCEL</a> -->