#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tqdm
import numpy as np
import pandas as pd
from selenium import webdriver
#from selenium.webdriver.support.ui import Select
from bs4 import BeautifulSoup
import datetime
from selenium.webdriver.firefox.options import Options
options = Options()
options.add_argument("--headless")

timestamp = datetime.datetime.now().strftime("%Y-%b-%d")
url = '''https://www.bilbasen.dk/brugt/bil/Citro%C3%ABn/C1?
    fuel=0&
    yearfrom=0&
    yearto=0&
    pricefrom=0&
    priceto=10000000&
    mileagefrom=-1&
    mileageto=10000001&
    includeengroscvr=false&
    includeleasing=false&
    newandused=usedonly&
    page={}
'''


def parse_url(url):
    url = url.replace('\n', '').replace(' ', '')
    driver = webdriver.Firefox(firefox_options=options)
    driver.get(url)

    # Make sure we get 96 answers per page
    #select = Select(driver.find_element_by_id('itemsPerPage'))
    #select.select_by_visible_text('96')
    #select.select_by_value('96')

    data = driver.page_source
    soup = BeautifulSoup(data, 'html.parser')
    driver.close()
    return soup


def parse_soup(soup):
    results = []

    # Loop over the cars in the page
    for div in soup.select("div[class*=bb-listing-clickable]"):
        headline    = None
        description = None
        odometer    = None
        year        = None
        price       = None
        horsepower  = None


        #<div class="col-xs-2 listing-data">152.000</div>
        #<div class="col-xs-2 listing-data">2010</div>
        #<div class="col-xs-3 listing-price">99.900 kr.</div>
        #</div>
        #<div class="row">
        #<div class="col-xs-2 listing-region">Syd- og Vestsjælland</div>


        # Price
        price = float(div.find(attrs={'class': 'col-xs-3 listing-price'}).text.strip().split()[0].replace('.', ''))

        # Headline
        headline  = div.find(attrs={'class': 'listing-heading darkLink'}).text.strip()

        # Horsepower
        horsepower = float(div.find("span", class_="variableDataColumn").attrs['data-hk'].strip().split()[0])

        # Description
        description = div.find(attrs={'class': 'listing-description expandable-box'}).text.strip()

        # Region
        region = div.find(attrs={'class': 'col-xs-2 listing-region'}).text.strip()

        # Dealer - not working
        #dealer = div.find(attrs={'class': 'dealer-private-string'}).text.strip()

        # Year and odometer
        datas = div.find_all("div", class_=lambda v: v and 'col-xs-2 listing-data' in v)
        for data in datas:
            data_string = data.text.strip()
            if '.' in data_string:
                odometer = float(data_string.replace('.', ''))
            else:
                if data_string != '-':
                    year = int(data_string.strip())

        results.append((headline, year, odometer, price, description, horsepower, region))
    print(results)
    return results



results = []
for page in tqdm.tqdm(range(1, 20)):  # 492/32 = 15.375
    print(url.format(page))
    soup = parse_url(url.format(page))
    try:
        soup = parse_url(url.format(page))
        results = results + parse_soup(soup)
    except:
        pass

# Create the dataframe
df = pd.DataFrame.from_records(results, columns=['headline', 'year', 'odometer', 'price', 'description', 'horsepower', 'region'])
print(df)

# Process the headline to get the transmission type
# df['transmissionManual'] = True
# df.loc[df['headline'].str.contains('DSG'), 'transmissionManual'] = False

# Fuel type
df['fuelType'] = 'Gasoline'
df.loc[df['headline'].str.contains('HDi'), 'fuelType'] = 'Diesel'

# Car type
# df['carTypeStationCar'] = False
# df.loc[df['headline'].str.contains('Combi'), 'carTypeStationCar'] = True

# EngineSize
df['engineSize'] = df.iloc[:, 0].str.extract('(\d,\d)', expand=False)

# Trim
df['trim'] = 'Unknown'
trimlevels = [
    'Scoop',
    'Exclusive',
    'Airspace',
    'Triumph',
    'Sport',
    'SportLine',
    'Cool',
    'Seduction',
    'Prestige',
    'Feel',
    'VTR',
    'Iconic',
    'Street',
]


for trimlevel in trimlevels:
    df.loc[df['headline'].str.contains(trimlevel), 'trim'] = trimlevel

print(df.head())
print(f'Number of cars: {df.shape[0]}')

# Save the file
df.to_parquet(f'data_{timestamp}.parquet')
