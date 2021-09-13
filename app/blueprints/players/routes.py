from typing import DefaultDict
from flask import render_template, request, redirect, url_for, flash, Markup, session, json, jsonify, Response
from pandas.core.frame import DataFrame
from app.context_processor import db, auth, getDates, getWeeks
import pandas as pd
import os
from .import bp as app
import requests
from bs4 import BeautifulSoup
from IPython.display import display
from pprint import pprint
from app import cache
from app import limiter
# headless webdriver to get the Prize Money, Titles/Finals after clicking links
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# limits number of api_calls allowed to prevent DDOS style attacks
per_day = 3000
per_minute = 80

chrome_options = Options()
chrome_options.add_argument("--headless")

# URL prefix to search player
search_url_prefix = "https://bwf.tournamentsoftware.com/find/player?q="
# URL prefix to get profile page
profile_url_prefix = 'https://bwf.tournamentsoftware.com/player-profile/'

@app.route('/', methods=['GET', 'POST'])
@limiter.limit(f"{per_day}/day;{per_minute}/minute", error_message=f'Please limit API calls to {per_day}/day, {per_minute}/minute')
def search():
    if request.method == 'POST':
        if len(request.form.get('player-search').strip()) <= 2:
            flash('Search term needs to be longer than 2 characters', 'info')
            return redirect(url_for('players.search'))
        # driver = webdriver.Chrome(options=chrome_options, executable_path='./chromedriver')
        search_results = get_search_results(request.form.get('player-search'))
        if not search_results:
            flash('No results available for given search term.', 'info')
            return redirect(url_for('players.search'))
        context = {
                'search_results': search_results
            }
        return render_template('player-search.html', **context)
    return render_template('player-search.html')

# @app.route('/player-profile/<profile_suffix>')
# def player_profile(profile_suffix):
#     player_data = get_player_data(profile_suffix)
#     # jsonify(json.loads(json.dumps(player_info, indent=4)))
#     context = {
#         k.replace(' ', '_').lower(): v for k, v in player_data.items()
#     }
#     context['profile_suffix'] = profile_suffix
#     pprint(context['prize_money'])

    # return render_template('player.html', ** context)

@cache.memoize(timeout=500)
def get_player_data(profile_suffix):
    driver = webdriver.Chrome(options=chrome_options, executable_path='./chromedriver')
    driver.get(profile_url_prefix + profile_suffix)
    player_info = {}
    personal_info = {}
    personal_info['name'] = driver.find_element_by_css_selector('h2.media__title.media__title--large').find_element_by_css_selector('span.nav-link__value').get_attribute("innerText").strip()
    win_loss_info = {}
    prize_money_dict = {}
    titles_dict = {}
#     modules = profile_soup.find_all('div', class_='module module--card')
    modules = driver.find_elements_by_css_selector('div.module.module--card')
    modules_left = []
    for module in modules:
        title = module.find_element_by_css_selector('span.module__title-main').get_attribute("innerText").strip().lower().replace(' ', '_')
        if title in ["statistics", "prize_money", "titles/finals"]:
            modules_left.append(title)

    # will need to reload driver to get both tables for prize money and titles
    while modules_left:
        modules = driver.find_elements_by_css_selector('div.module.module--card')
        for module in modules:
        #         title = module.find('span', class_='module__title-main').string.strip()
            title = module.find_element_by_css_selector('span.module__title-main').get_attribute("innerText").strip().lower().replace(' ', '_')
            print(title)
                # Will contain game statistics and personal details(if section exists)
            if title in modules_left and title == "statistics":
                # Check if personal details section exists(find_elements will return an empty list if not existing)
                if module.find_elements_by_css_selector('h4.subheading') and module.find_element_by_css_selector('h4.subheading').text.lower() == "personal details":
                    for div in module.find_element_by_css_selector('dl.list.list--flex.list--bordered').find_elements_by_css_selector('div.list__item'):
                        label = div.find_element_by_css_selector('dt.list__label').get_attribute("innerText").strip()
                        value = div.find_element_by_css_selector('span.nav-link__value').get_attribute("innerText").strip()
                        personal_info[label] = value
                for stat_class in ['tabStatsTotal', 'tabStatsSingles', 'tabStatsDoubles', 'tabStatsMixed']:
                    stat_list = module.find_element_by_id(stat_class).find_elements_by_css_selector('div.list__item')[:2]
                    stat_dict = {}
                    for stat in stat_list:
                        time_period = stat.find_element_by_tag_name('dt').get_attribute("innerText").strip()
                        win_loss = stat.find_element_by_css_selector('span.list__value-start').get_attribute("innerText").strip()
                        stat_dict[time_period] = win_loss
                    win_loss_info[stat_class.replace('tabStats', '').replace(' ', '_')] = stat_dict
                modules_left.remove(title)
                print('Finished Statistics section')
                continue
                # Contains prize money info(Ignoring this since it's apparently not as accurate as it seems)      
            if title in modules_left and title == "prize_money":
                module.find_element_by_link_text("All").click()
                try:
                    element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR , "table.table--new.table--bordered"))
                    )
                finally:
                    page_source = driver.page_source
                    total_df = pd.read_html(page_source)[0].rename(columns={'Unnamed: 0':'time_period'}).set_index('time_period').transpose()
                    total_df.columns = total_df.columns.map(lambda x: x.replace(' ', '_').lower())
                    detailed_df = pd.read_html(page_source)[1]
                    detailed_df.columns = detailed_df.columns.map(lambda x: x.replace(' ', '_').lower())
    #             pprint(json.loads(total_df.to_json()))
    #             pprint(json.loads(detailed_df.to_json(orient='records')))
                # copy_df = detailed_df[["event", "amount"]].copy()
                # copy_df['amount'] = copy_df['amount'].apply(lambda x: x.replace('$', '').replace(',', '')
                #                 if isinstance(x, str) else x).astype(float)
                # display(copy_df.groupby('event').sum())
                # display(total_df)
                # total_df = pd.DataFrame(data=mydata,index=myindex)
                prize_money_dict = {
                    'total': total_df.to_dict(),
                    'detailed': detailed_df.to_dict('records')
                }
                modules_left.remove(title)
                driver.refresh()
                print('Finished Prize Money section')
                break

            if title in modules_left and title == "titles/finals":
                module.find_element_by_link_text("All").click()
                try:
                    # Wait until the page is completely loaded after button click
                    element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID , "form0"))
                    )
                finally:
                    tournaments_by_years = driver.find_element_by_id('form0').find_elements_by_css_selector('div.list__item')
                    # The sections are divided by years, so look at the tournaments by year
                    for tournaments_for_year in tournaments_by_years:
                        # The year we're observing
                        year = tournaments_for_year.find_element_by_tag_name('dt').get_attribute("innerText").strip()
                        titles_dict[year] = {}
                        # Check each tournament for this year
                        for tournament in tournaments_for_year.find_elements_by_css_selector('li.list__item'):
                            # Get the tournament name
                            tournament_name = tournament.find_elements_by_css_selector('span.nav-link__value')[0].get_attribute("innerText").strip()
                            # Check if the tournament isn't a duplicate
                            if tournament_name in titles_dict[year]:
                                continue
                            # Get category(like Mens Singles, Womens Doubles, etc)
                            category = tournament.find_elements_by_css_selector('span.nav-link__value')[1].get_attribute("innerText").strip()
                            # Get the placing for this tournament
                            placing = tournament.find_element_by_tag_name('svg').get_attribute('title')
                            titles_dict[year][tournament_name] = {
                                'category': category,
                                'placing': placing
                            }
                modules_left.remove(title)
                print('Finished Titles/Finals section')
                break
    driver.quit()
    player_info['Personal Details'] = personal_info
    player_info['Game Statistics'] = win_loss_info if win_loss_info else ["No info available"]
    player_info['Prize Money'] = prize_money_dict if prize_money_dict else ["No info available"]
    player_info['Titles'] = titles_dict if titles_dict else ["No info available"]
    return player_info


@app.route('/download/<profile_suffix>')
@limiter.limit(f"{per_day}/day;{per_minute}/minute", error_message=f'Please limit API calls to {per_day}/day, {per_minute}/minute')
def download(profile_suffix):
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
    player_data = get_player_data(profile_suffix)
    name = player_data['Personal Details']['name'].replace(' ', '_')
    file = jsonify(json.loads(json.dumps(player_data, indent=4)))
    file.headers['Content-Disposition'] = f'attachment;filename={name}.json'
    return file


@cache.memoize(timeout=120)
def get_search_results(search_term):
    page = requests.get(search_url_prefix + search_term.lower().replace(' ', '+'))
    # pprint(driver.page_source)
    soup = BeautifulSoup(page.content, 'html.parser')
    search_results = []
    for player in soup.find(id="searchResultArea").find_all('li', class_='list__item'):
        profile_link = player.find('a', class_="nav-link media__link")
        if not profile_link:
            break
        link_suffix = profile_link['href'].replace('/player-profile/', '')
        player_name = player.find('h5', class_="media__title").find('span', {'class': 'nav-link__value'}).string.strip()
        player_id = player.find('span', class_="media__title-aside").string.strip()
        if player_id and player_id[0] == '(' and player_id[-1] == ')':
            player_id = player_id[1:-1]
        association = player.find('small', class_="media__subheading").find('span', class_="nav-link__value").string.strip()
        search_results.append((link_suffix, player_name, player_id, association))
    return search_results
    