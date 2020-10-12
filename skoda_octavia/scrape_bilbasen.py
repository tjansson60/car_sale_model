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

url = '''https://www.bilbasen.dk/brugt/bil/Skoda/ms-Octavia-Serie?
    yearfrom=2010&
    pricefrom=0&
    includeengroscvr=false&
    includeleasing=false&
    newandused=usedonly&
    page={}
'''


def parse_url(url):
    url = url.replace('\n', '').replace(' ', '')
    driver = webdriver.Firefox(firefox_options=options)
    driver.get(url)

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
    return results


results = []
for page in tqdm.tqdm(range(1, 55)):  # 687/32 = 21.46
    print(url.format(page))
    soup = parse_url(url.format(page))
    try:
        soup = parse_url(url.format(page))
        results = results + parse_soup(soup)
    except:
        pass

# Create the dataframe
df = pd.DataFrame.from_records(results, columns=['headline', 'year', 'odometer', 'price', 'description', 'horsepower', 'region'])

# Process the headline to get the transmission type
df['transmissionManual'] = True
df.loc[df['headline'].str.contains('DSG'), 'transmissionManual'] = False

# Fuel type
df['fuelTypeGasoline'] = True
df.loc[df['headline'].str.contains('TDi'), 'fuelTypeGasoline'] = False

# Car type
df['carTypeStationCar'] = False
df.loc[df['headline'].str.contains('Combi'), 'carTypeStationCar'] = True

# EngineSize
df['engineSize'] = df.iloc[:, 0].str.extract('(\d,\d)', expand=False)

# Trim
df['trim'] = np.nan

df.loc[df['headline'].str.contains('L&K'), 'trim']            = 'L&K'
df.loc[df['headline'].str.contains('RS'), 'trim']             = 'RS'
df.loc[df['headline'].str.contains('Celebration'), 'trim']    = 'Celebration'
df.loc[df['headline'].str.contains('Joy'), 'trim']            = 'Joy'
df.loc[df['headline'].str.contains('Dynamic'), 'trim']        = 'Dynamic'
df.loc[df['headline'].str.contains('Ambition'), 'trim']       = 'Ambition'
df.loc[df['headline'].str.contains('Style'), 'trim']          = 'Style'
df.loc[df['headline'].str.contains('GreenLine'), 'trim']      = 'Greenline'
df.loc[df['headline'].str.contains('Active'), 'trim']         = 'Active'
df.loc[df['headline'].str.contains('Ambiente'), 'trim']       = 'Ambiente'
df.loc[df['headline'].str.contains('Elegance'), 'trim']       = 'Elegance'
df.loc[df['headline'].str.contains('Classic'), 'trim']        = 'Classic'
df.loc[df['headline'].str.contains('Comfort'), 'trim']        = 'Comfort'
df.loc[df['headline'].str.contains('Fresh'), 'trim']          = 'Fresh'
df.loc[df['headline'].str.contains('Sport'), 'trim']          = 'Sport'
df.loc[df['headline'].str.contains('Tour de France'), 'trim'] = 'Tour de France'
df.loc[df['headline'].str.contains('VM Edition'), 'trim']     = 'VM Edition'
df.loc[df['headline'].str.contains('Family'), 'trim']         = 'Family'

print(df.head())
print(f'Number of cars: {df.shape[0]}')

# Save the file
df.to_parquet(f'data_{timestamp}.parquet')
