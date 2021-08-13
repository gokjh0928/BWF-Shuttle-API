import requests
from IPython.display import display, clear_output as co
import os
from os import system, name
import datetime
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
import requests
import json, math
from pprint import pprint

# Get all valid dates to get rankings from
valid_dates = []
page = requests.get('https://bwfbadminton.com/rankings/2/bwf-world-rankings/6/men-s-singles/2009/41/?rows=25&page_no=1')
soup = BeautifulSoup(page.content, "html.parser")
dates = soup.find(id="ranking-week").find_all('option')
for date in dates[:-1]:
    date_string = date.text.strip().split(" ")
    date_tuple = (date_string[2][1:-1], f'({date_string[0]} {date_string[1]})')
    valid_dates.append(date_tuple)
valid_dates.append(("2009-10-01", "(Week 40)"))


# today's date
today = datetime.date.today().isocalendar()


# Used to get the url for the rankings table
categories = {
        'MS': '6/men-s-singles',
        'WS': '7/women-s-singles', 
        'MD': '8/men-s-doubles', 
        'WD': '9/women-s-doubles', 
        'XD': '10/mixed-doubles'
        }
alt_names = {
    "MEN'S SINGLES": 'MS',
    "WOMEN'S SINGLES": 'WS',
    "MEN'S DOUBLES": 'MD',
    "WOMEN'S DOUBLES": 'WD',
    "MIXED DOUBLES": 'XD'
}

def getTable(category, year=today[0], week=today[1], rows=25):

    # Get the ranking page containing top 100 rows
    #page = requests.get(driver.current_url)
    page = requests.get(f'https://bwfbadminton.com/rankings/2/bwf-world-rankings/{categories[category]}/{year}/{week}/?rows=100&page_no=1')
    #soup = BeautifulSoup(page.content, "html.parser")
    df = pd.DataFrame(columns=['rank', 'country/territory', 'player', 'change_+/-', 'win/lose', 'prize_money', 'points/tmts', 'break-down', 'link', 'member_id'])
    # get number of pages to look at to get all the rows needed
    q,r = divmod(rows, 100)
    num_pages = q if r == 0 else q+1
    for page_number in range(1, num_pages+1):
        # Get the specfic page
        page = requests.get(f'https://bwfbadminton.com/rankings/2/bwf-world-rankings/{categories[category]}/{year}/{week}/?rows=100&page_no={page_number}')
        soup = BeautifulSoup(page.content, "html.parser")
        df2 = pd.read_html(page.text)[0]
        # Check if we've accounted for all possible rows
        if df2.empty:
            break
        # Get only the relevant columns(even columns since odd columns are just rows filled with NaN values)
        df2 = df2.iloc[::2]

        # adjust the column names
        df2.columns = df2.columns.map(lambda x: x.replace(' ', '').lower() if isinstance(x, str) else x)
        df2.rename(columns={'prizemoney':'prize_money', 'change+/-':'change_+/-'}, inplace=True)
        
        # Get all ranking change data for every player
        rankingchanges = soup.find_all(class_="ranking-change")
    
        # adjust rankingchanges and players for doubles to ensure each row has two players 
        if category in ['MD', 'WD', 'XD']:
            # print(page_number)
            # Check for error where there's only one player in a pair instead of two players
            invalid_df = df2[(df2['country/territory'].str.strip().str.contains(' ') == False)]
            invalid_names = []

            # If the above error exists, clean data
            if not invalid_df.empty:
                # Drop the rows in this dataframe where the errors are
                df2.drop(invalid_df.index.values.tolist(), inplace = True)
                # Make sure that ranking changes from this page are only for the rows without errors
                # rankingchanges = [i for j, i in enumerate(rankingchanges) if j not in invalid_df.index]
                invalid_names = invalid_df['player'].values.tolist()
                print(invalid_names)
            
            # Get all players' anchor tags containing links to their profiles if not in invalid players and if the link is valid
            players = []
            for idx, player in enumerate(soup.find_all(class_="tooltip")):
                if ((player['title'] not in invalid_names) and (len(player['href'].split('/')) == 6)) and (player['href'].split('/')[4]):
                    players.append(player)
                elif player['title'] in invalid_names:
                    print(f"found invalid title of {player['title']}")
                    # delete the rankingchanges corresponding to the deleted rows
                    rankingchanges[(idx + 1) // 2] = 'remove'
                    # need to remove to allow for duplicates later on
                    invalid_names.remove(player['title'])
                    
            #players = [player for player in soup.find_all(class_="tooltip") if ((player['title'] not in invalid_names) and (len(player['href'].split('/')) == 6)) and (player['href'].split('/')[4])]
            # print([player for player in soup.find_all(class_="tooltip") if (player['title'] in invalid_names) or (len(player['href'].split('/')) != 6)])


        # Differences btw doubles and singles: doubles drops all invalid data, singles leaves it in and replaces missing values with '(Missing)'
        if category in ['MD', 'WD', 'XD']:
            # Now drop rows where both players are empty AKA whole row is empty
            dropped_idx = df2['player'].index[df2['player'].isna()]
            df_index = df.index.values.tolist()
            for idx in [df_index.index(i) for i in dropped_idx]:
                rankingchanges[idx] = 'remove'


            df2.dropna(subset=['player'], inplace = True)
            while 'remove' in rankingchanges:
                rankingchanges.remove('remove')

            
            # Pair individual names, links, member_ids
            player_links = list(zip(*[iter(player['href'] for player in players)]*2))
            # pair player names
            # print(len(players))
            # print(len(df2))
            df2['player'] = np.array(f'{pair[0]}, {pair[1]}' for pair in zip(*[iter(player['title'] for player in players)]*2))
            # pair links
            df2['link'] = np.array(f'{pair[0]},{pair[1]}' for pair in player_links)
            # pair member IDs from the links
            # print([f'{str(pair[0])}, {str(pair[1])}' for pair in player_links if (len(str(pair[0]).split("/")) != 6 or len(str(pair[1]).split("/")) != 6)])
            df2['member_id'] = np.array(f'{str(pair[0]).split("/")[4]}, {str(pair[1]).split("/")[4]}' for pair in player_links)
        else:
            # get all players' anchor tags containing links to their profiles
            players = [player for player in soup.find_all(class_="tooltip")]
            # get specifically the href links from each player's anchor tag
            player_links = [player['href'] if player["href"] else "(Missing)" for player in players]
            if '(Missing)' in player_links:
                print("Empty link found!!!!!")
            
            df2['link'] = np.array(player_links)
            if not df2[df2['link'] == '(Missing)'].empty:
                display(df2[df2['link'] == '(Missing)'])

            # get member ID from the player links
            df2['member_id'] = df2['link'].map(lambda x: x.split('/')[4] if x != "(Missing)" else x)

        df2['change_+/-'] = df2['change_+/-'].astype(np.int32).astype('string')
        display(df2)
        for idx, change in enumerate(rankingchanges):
                if change.string.strip() != '0':
                    # assign '+' or '-' depending on whether the ranking change is positive or negative
                    print(idx, change.string)
                    print(len(df2))
                    if 'arrow-up' in change.parent.find('img')['src']:
                        df2['change_+/-'].iloc[idx] = '+' + df2['change_+/-'].iloc[idx]
                    else:
                        df2['change_+/-'].iloc[idx] = '-' + df2['change_+/-'].iloc[idx]
        df = df.append(df2)
    
    # Convert ranking table into dataframe and clean the data and fill in missing values
    df = df.drop('break-down', axis=1)
    df['prize_money'] = df[['prize_money']].fillna(value=0)
    df['player'] = df[['player']].fillna(value="(Missing)")
    df['country/territory'] = df[['country/territory']].fillna(value="(Missing)")

    # Rearrange order of columns so rank is first column
    df['rank'] = df['rank'].astype(np.int64)
    # Get only the number of rows needed
    df = df.head(rows)
    # Doubles categories has two countries, so split using '/'
    if category in ['MD', 'WD', 'XD']:
        df['country/territory'] = df['country/territory'].map(lambda x: x.replace(' ', ' / '))
    # Reset index since odd numbered rows were dropped bc they were just NaN
    df.reset_index(drop=True, inplace=True)
    # Reorder columns
    df = df[['rank','country/territory','player','change_+/-','win/lose','prize_money','points/tmts', 'link', 'member_id']]
    # Turn dataframe to JSON
    # result = df.to_json(orient='records')
    # parsed = json.loads(result)
    # with open(f'{category}_playertable_{year}_{week}.json', 'w') as f:
    #     json.dump(parsed, f) 
    #     f.close()
    from app.blueprints.rankings.routes import path
    # Download the csv file created into the rankings table
    df.to_csv(path + f'/rankings/{category}/{category}_{year}_{week}.csv', index=False)
    return df.to_csv(index=False)


# def csv_to_json():
#     test = os.getcwd()
#     print(test)
#     df = pd.read_csv(test + f'/rankings/MD/MD_2019_18.csv')
#     display(df)
#     result = df.to_json(orient='records')
#     parsed = json.loads(result)
#     with open(test + f'{category}_playertable_{year}_{week}.json', 'w') as f:
#         json.dump(parsed, f) 
#         f.close()
#     return

# class Player:
#     def __init__(self, name, country, rankings, categories, ranking_changes, earnings, age, record):
#         self.name = name
#         self.country = country
#         self.rankings = rankings
#         self.categories = categories
#         self.ranking_changes = ranking_changes
#         self.earnings = earnings
#         self.age = age
#         self.record = record
        
# today = datetime.date.today().isocalendar()
# getTable('XD', today[0], today[1], 1000000)
#getTable('MS', validDates[0][0], validDates[0][1], 10)

# csv_to_json()