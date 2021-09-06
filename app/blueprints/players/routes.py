from flask import render_template, request, redirect, url_for, flash, Markup, session, json, jsonify, Response
from pandas.core.frame import DataFrame
from app.context_processor import db, auth, getDates, getWeeks
import pandas as pd
import os
from .import bp as app
import requests
from bs4 import BeautifulSoup
# from IPython.display import display
from pprint import pprint
from app import cache
from app import limiter
# headless webdriver to get the Prize Money, Titles/Finals after clicking links
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

chrome_options = Options()
chrome_options.add_argument("--headless")


# URL prefix to search player
search_url_prefix = "https://bwf.tournamentsoftware.com/find/player?q="
# URL prefix to get profile page
profile_url_prefix = 'https://bwf.tournamentsoftware.com/player-profile/'



@app.route('/', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        if len(request.form.get('player-search')) <= 3:
            flash('Search term needs to be longer than 3 characters', 'info')
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

@app.route('/player-profile/<profile_suffix>')
@cache.cached(timeout=300)
def player_profile(profile_suffix):
    driver = webdriver.Chrome(options=chrome_options, executable_path='./chromedriver')
    driver.get(profile_url_prefix + profile_suffix)
    player_info = {}
    personal_info = {}
    personal_info['Name'] = driver.find_element_by_css_selector('h2.media__title.media__title--large').find_element_by_css_selector('span.nav-link__value').get_attribute("innerText").strip()
    win_loss_info = {}
#     modules = profile_soup.find_all('div', class_='module module--card')
    visited_titles = []
    still_visiting_modules = True
    while still_visiting_modules:
        print('Refreshed here')
        modules = driver.find_elements_by_css_selector('div.module.module--card')
        for idx, module in enumerate(modules):
    #         title = module.find('span', class_='module__title-main').string.strip()
            title = module.find_element_by_css_selector('span.module__title-main').get_attribute("innerText").strip()
            print(title)
            # Will contain game statistics and personal details(if section exists)
            if title not in visited_titles and title == "Statistics":
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
                    win_loss_info[stat_class.replace('tabStats', '')] = stat_dict
                visited_titles.append(title)
                print('Finished Statistics section')
            # Contains prize money info(Ignoring this since it's apparently not as accurate as it seems)      
#             if title not in visited_titles and title == "Prize Money":
#                 module.find_element_by_link_text("All").click()
#                 try:
#                     element = WebDriverWait(driver, 10).until(
#                         EC.presence_of_element_located((By.CSS_SELECTOR , "table.table--new.table--bordered"))
#                     )
#                 finally:
#                     page_source = driver.page_source
#                     total_df = pd.read_html(page_source)[0].rename(columns={'Unnamed: 0':'time_period'}).set_index('time_period').transpose()
#                     total_df.columns = total_df.columns.map(lambda x: x.replace(' ', '_').lower())
#                     detailed_df = pd.read_html(page_source)[1]
#                     detailed_df.columns = detailed_df.columns.map(lambda x: x.replace(' ', '_').lower())
#     #             pprint(json.loads(total_df.to_json()))
#     #             pprint(json.loads(detailed_df.to_json(orient='records')))
#                 prize_money_dict = {
#                     'total': total_df.to_dict(),
#                     'detailed': detailed_df.to_dict('records')
#                 }
#                 visited_titles.append(title)
#                 driver.refresh()
#                 print('Finished Prize Money section')
#                 if idx == len(modules) - 1:
#                     still_visiting_modules = False
#                 break

            if title == "Titles/Finals":
                module.find_element_by_link_text("All").click()
                try:
                    # Wait until the page is completely loaded after button click
                    element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID , "form0"))
                    )
                finally:
                    tournaments_by_years = driver.find_element_by_id('form0').find_elements_by_css_selector('div.list__item')
                    titles_dict = {}
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
                        
                print('Finished Titles/Finals section')
                still_visiting_modules = False
    driver.close()
    player_info['Personal Details'] = personal_info
    player_info['Game Statistics'] = win_loss_info
    pprint(json.loads(json.dumps(player_info, indent=4)))
    return jsonify(json.loads(json.dumps(player_info, indent=4)))


@cache.memoize(timeout=120)
def get_search_results(search_term):
    page = requests.get(search_url_prefix + search_term.lower().replace(' ', '+'))
    # pprint(driver.page_source)
    soup = BeautifulSoup(page.content, 'html.parser')
    search_results = []
    for player in soup.find(id="searchResultArea").find_all('li', class_='list__item'):
        link_suffix = player.find('a', class_="nav-link media__link")['href']
        player_name = player.find('h5', class_="media__title").find('span', {'class': 'nav-link__value'}).string.strip()
        player_id = player.find('span', class_="media__title-aside").string.strip()
        if player_id and player_id[0] == '(' and player_id[-1] == ')':
            player_id = player_id[1:-1]
        association = player.find('small', class_="media__subheading").find('span', class_="nav-link__value").string.strip()
        search_results.append((link_suffix, player_name, player_id, association))
    return search_results
    