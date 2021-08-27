import requests
from IPython.display import display
import re
import datetime
import pandas as pd
from bs4 import BeautifulSoup
import requests

# Get all valid dates to get rankings from
def getValidDates():
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

def getWeeks():
    valid_weeks = {}
    page = requests.get('https://bwfbadminton.com/rankings/2/bwf-world-rankings/6/men-s-singles/2009/41/?rows=25&page_no=1')
    soup = BeautifulSoup(page.content, "html.parser")
    dates = soup.find(id="ranking-week").find_all('option')
    for date in dates[:-1]:
        date_string = date.text.strip().split(" ")
        ymd_list = date_string[2][1:-1].split('-')
        valid_weeks[f'{ymd_list[0]}-{date_string[1]}'] = '/'.join(ymd_list)
    valid_weeks["2009-40"] = "2009/10/01"
    return valid_weeks

# today's date
today = datetime.date.today().isocalendar()

# Used to get the url for the rankings table
categories = {
        'MS': '472',
        'WS': '473', 
        'MD': '474', 
        'WD': '475', 
        'XD': '476'
        }
alt_names = {
    "MEN'S SINGLES": 'MS',
    "WOMEN'S SINGLES": 'WS',
    "MEN'S DOUBLES": 'MD',
    "WOMEN'S DOUBLES": 'WD',
    "MIXED DOUBLES": 'XD'
}


# function to get the table at the url(only used for seeding at this point since we're using Firebase)
# Link is: https://bwf.tournamentsoftware.com/ranking/category.aspx?id={ date_value }&category={ category_value }&C472FOC=&p=1&ps=100

def getTable(category, date_value, category_value):
    page_number = 1
    # Singles categories
    if category in ['MS', 'WS']:
        # Initialize empty dataframe
        df = pd.DataFrame(columns=['rank', 'rank_change', 'prev_rank', 'country', 'player', 'member_id', 'points', 'tournaments'])
        # Iterate through each page by 100
        while True:
            page = requests.get(f"https://bwf.tournamentsoftware.com/ranking/category.aspx?id={ date_value }&category={ category_value }&C472FOC=&p={page_number}&ps=100")
            soup = BeautifulSoup(page.content, 'html.parser')
            
            # Check if we've accounted for all possible rows(If this page's df is empty, we reached the end)
            if not pd.read_html(page.text):
                break
            df2 = pd.read_html(page.text)[0]
            
            # clean data to only include the 100 rows and rename columns
            df2 = df2[:-1]
            df2.columns = df2.columns.map(lambda x: x.replace(' ', '').lower())
            df2.drop(['rank.1','unnamed:2','unnamed:5'], axis=1, inplace=True)
            df2.rename(columns={'memberid':'member_id'}, inplace=True)
            
            # Get names of each player in pair, then the previous rank, then the ranking change with '-' indicating drop in rank
            player = []
            member_id = []
            profile_link = []
            previous_ranks = []
            rank_changes = []
            skip = False
            profile_url_prefix = "https://bwf.tournamentsoftware.com"
            for idx, row in enumerate(soup.find_all('tr')[2:-1]):
#               Check if the row has 2 flags and 2 names to ensure there are two valid players
#               print(row.find_all('td')[0].string)
                rank = int(row.find_all('td')[0].string)
#               print(row.find('a').string)
                player.append(row.find('a').string)
#               print(row.find_all('td')[6].string)
                member_id.append(row.find_all('td')[6].string)
#               print(profile_url_prefix + row.find_all('td')[5].find('a')['href'])
                profile_link.append(profile_url_prefix + row.find_all('td')[5].find('a')['href'])
                
                if 'title' in row.find_all('td')[1].attrs:
                    prev_rank = int(row.find_all('td')[1]['title'].split(' ')[2])
                    ranking_change = prev_rank - rank
                else:
                    prev_rank = 0
                    ranking_change = rank - prev_rank
                previous_ranks.append(prev_rank)
                rank_changes.append(ranking_change)
            page_number += 1


            # Get additional data 
            # Check to see if the lens of each column match
            if not (len(player) == len(member_id) == len(previous_ranks) ==len(rank_changes) == len(profile_link)):
                print(f'player: {len(player)}')
                print(f'member_id: {len(member_id)}')
                print(f'previous_ranks: {len(previous_ranks)}')
                print(f'rank_changes: {len(rank_changes)}')
                print(f'profile_link: {len(profile_link)}')
#             display(df2.index[df2['player'].isna()])
            
            # Drop invalid rows(0 or 1 player in the row) before appending columns
            df2.dropna(subset=['player'], inplace = True)
            
            df2['country'] = df2['player'].apply(lambda x: '/'.join(re.findall('\[(.*?)\]', x)))
            
            # append columns
            df2['player'] = player
            df2['member_id'] = member_id
            df2['profile_link'] = profile_link
            df2['prev_rank'] = previous_ranks
            df2['rank_change'] = rank_changes

            df2.drop(['country.1', 'confederation'], axis=1, inplace=True)
            
            df = df.append(df2)
#         display(df)
        return df

    # Doubles Categories
    if category in ['MD', 'WD', 'XD']:
        # Initialize empty dataframe
        df = pd.DataFrame(columns=['rank', 'rank_change', 'prev_rank', 'country', 'player1', 'player2', 'member_id1', 'member_id2', 'points', 'tournaments'])
        
        # Iterate through each page by 100
        while True:
            page = requests.get(f"https://bwf.tournamentsoftware.com/ranking/category.aspx?id={ date_value }&category={ category_value }&C472FOC=&p={page_number}&ps=100")
            soup = BeautifulSoup(page.content, 'html.parser')
            
            # Check if we've accounted for all possible rows(If this page's df is empty, we reached the end)
            if not pd.read_html(page.text):
                break
            df2 = pd.read_html(page.text)[0]
            
            # clean data to only include the 100 rows and rename columns
            df2 = df2[:-1]
            df2.columns = df2.columns.map(lambda x: x.replace(' ', '').lower())
            df2.drop(['rank.1','unnamed:2','unnamed:5', 'memberid'], axis=1, inplace=True)
            
            
            # Get names of each player in pair, member IDs, profile links, previous rank, then the ranking change(negative value indicates drop in rank)
            player_1 = []
            player_2 = []
            member_id1 = []
            member_id2 = []
            profile_link1 = []
            profile_link2 = []
            previous_ranks = []
            rank_changes = []
            profile_url_prefix = "https://bwf.tournamentsoftware.com"
            skip = False
            for idx, row in enumerate(soup.find_all('tr', class_="doubles")):
                # Check if the row has 2 flags and 2 names to ensure there are two valid players
                if len(row.find_all('td')[3]) == 2 and len(row.find_all('td')[4]) == 2:
                    # Now check that none of the two flags or player names are empty('skip' flag will )
                    for flag in row.find_all('td')[3]:
                        # If there is no flag
                        if not flag.string:
#                             print('flag is missing!')
                            df2['country'].iloc[idx] = pd.NA
                            skip = True
                    for i, name in enumerate(row.find_all('td')[4]):
                        # If there is no flag
                        if not name.find('a').string:
                            df2['player'].iloc[idx] = pd.NA
                            skip = True
                    if skip:
                        skip = False
                        continue
                    # rank
                    rank = int(row.find_all('td')[0].string)
                    # player names
                    player_1.append(row.find_all('a')[0].string)
                    player_2.append(row.find_all('a')[1].string)
                    # member IDs
                    member_id1.append(list(row.find_all('td')[6].childGenerator())[0])
                    member_id2.append(list(row.find_all('td')[6].childGenerator())[2])
                    # profile links
                    profile_link1.append(profile_url_prefix + row.find_all('td')[5].find_all('a')[0]['href'])
                    profile_link2.append(profile_url_prefix + row.find_all('td')[5].find_all('a')[1]['href'])
                    if 'title' in row.find_all('td')[1].attrs:
                        # If 'title' attribute exists, its value will be previous ranking(0 indicates none)
                        prev_rank = int(row.find_all('td')[1]['title'].split(' ')[2])
                        ranking_change = prev_rank - rank
                    else:
                        prev_rank = 0
                        ranking_change = rank - prev_rank
                    previous_ranks.append(prev_rank)
                    rank_changes.append(ranking_change)
            page_number += 1


            # Get additional data 
            # Check to see if the lens of each column match
            if not (len(player_1) == len(player_2) == len(member_id1) == len(member_id2) == len(previous_ranks) ==len(rank_changes) == len(profile_link1) == len(profile_link2)):
                print(f'player1: {len(player_1)}')
                print(f'player2: {len(player_2)}')
                print(f'member_id1: {len(member_id1)}')
                print(f'member_id2: {len(member_id2)}')
                print(f'previous_ranks: {len(previous_ranks)}')
                print(f'rank_changes: {len(rank_changes)}')
                print(f'profile_link1: {len(profile_link1)}')
                print(f'profile_link2: {len(profile_link2)}')
            
            
            
            # Drop invalid rows(0 or 1 player in the row) before appending columns(we set player column to NA if invalid)
            df2.dropna(subset=['country', 'player'], inplace = True)
            
            # country will be in the form 'country1/country2'
            df2['country'] = df2['player'].apply(lambda x: '/'.join(re.findall('\[(.*?)\]', x)))
            
            
            # Drop rows without two players before attaching additional columns
            invalid_idx = df2['country'].index[df2['country'].str.contains('/') == False].values.tolist()
            df2.drop(invalid_idx, inplace=True)
            
            # append columns
            df2['player1'] = player_1
            df2['player2'] = player_2
            df2['member_id1'] = member_id1
            df2['member_id2'] = member_id2
            df2['profile_link1'] = profile_link1
            df2['profile_link2'] = profile_link2
            df2['prev_rank'] = previous_ranks
            df2['rank_change'] = rank_changes
            
            df2.drop(['player', 'country.1', 'confederation'], axis=1, inplace=True)
            
            # append the dataframe for the current page(df2) to the overall dataframe(df)
            df = df.append(df2)
#         display(df)
        return df

