#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import pickle
import tqdm
import numpy as np
import pandas as pd
from selenium import webdriver
from bs4 import BeautifulSoup
import datetime
from selenium.webdriver.firefox.options import Options

# Setup gecko
sys.setrecursionlimit(100000)  # default is 1000. Needed to be increased to save soup
options = Options()
options.add_argument("--headless")
driver_path = "/home/tjansson/bin/geckodriver"
timestamp = datetime.datetime.now().strftime("%Y-%b-%d")

url = """https://www.bilbasen.dk/brugt/bil/VW/ms-Passat-Serie?
    IncludeEngrosCVR=true&
    YearFrom=2020&
    PriceFrom=0&
    includeLeasing=false&
    Fuel=11&
    IncludeCallForPrice=false&
    page={}
"""


def load_url_soup(filename):
    with open(filename, "rb") as f:
        results = pickle.load(f)
    return results


def save_url_soup(url, filename, pages=12, debug=False):
    """Defaults to 32 listings per page, so 687 results requires 687/32 = 21.46 pages"""
    results = []

    for page in tqdm.tqdm(range(1, pages)):
        print(url.format(page))
        soup = parse_url(url.format(page))
        if debug:
            print(soup)
        results.append(soup)

    with open(filename, "wb") as file:
        pickle.dump(results, file, protocol=pickle.HIGHEST_PROTOCOL)
    print(f"Soup saved to: {filename}")


def parse_url(url):

    driver = webdriver.Firefox(options=options, executable_path=driver_path)

    url = url.replace("\n", "").replace(" ", "")
    driver.get(url)

    data = driver.page_source
    soup = BeautifulSoup(data, "html.parser")
    driver.close()

    return soup


def parse_soups(soups):
    pages = []
    for s in soups:
        parsed_soup = parse_soup(s)
        pages.append(parsed_soup)

    # Reformat results
    output = [item for page in pages for item in page]
    return output


def parse_soup(soup):
    results = []

    # Loop over the cars in the page
    for div in soup.select("div[class*=bb-listing-clickable]"):
        odometer = None
        year = None
        price = None
        headline = None
        horsepower = None
        region = None

        # Price
        price = float(div.find(attrs={"class": "col-xs-3 listing-price"}).text.strip().split()[0].replace(".", ""))

        # Headline
        headline = div.find(attrs={"class": "listing-heading darkLink"}).text.strip()

        # Horsepower
        horsepower = float(div.find("span", class_="variableDataColumn").attrs["data-hk"].strip().split()[0])

        # Region
        region = div.find(attrs={"class": "col-xs-2 listing-region"}).text.strip()

        # Year and odometer
        datas = div.find_all("div", class_=lambda v: v and "col-xs-2 listing-data" in v)
        for data in datas:
            data_string = data.text.strip()
            if "." in data_string:
                odometer = float(data_string.replace(".", ""))
            else:
                if data_string != "-":
                    year = int(data_string.strip())

        results.append((headline, year, odometer, price, horsepower, region))
    return results


def create_dataframe_from_soup(results, filename):
    # Create the dataframe
    df = pd.DataFrame.from_records(
        results, columns=["headline", "year", "odometer", "price", "horsepower", "region"]
    )

    # Process the headline to get the transmission type
    # df["transmissionManual"] = True
    # df.loc[df["headline"].str.contains("DSG"), "transmissionManual"] = False

    # Fuel type
    # df["fuelTypeGasoline"] = True
    # df.loc[df["headline"].str.contains("TDi"), "fuelTypeGasoline"] = False

    # Car type
    df["carTypeStationCar"] = False
    df.loc[df["headline"].str.contains("Variant"), "carTypeStationCar"] = True

    # EngineSize
    df["engineSize"] = df.iloc[:, 0].str.extract("(\d,\d)".replace(',', '.'), expand=False)

    # Trim
    df["trim"] = np.nan
    df.loc[df["headline"].str.contains("High"), "trim"] = "High"
    df.loc[df["headline"].str.contains("Pro"), "trim"] = "Pro"

    print(df)
    print(f"Number of cars: {df.shape[0]}")

    # Save the file
    df.to_parquet(filename)
    print(f"Dataframe saved to {filename}")


if __name__ == "__main__":
    filename_soups = f"{timestamp}-soups.pickle"
    filename_dataframe = f"{timestamp}-dataframe.parquet"

    save_url_soup(url, filename_soups, pages=6)
    soups = load_url_soup(filename_soups)
    results = parse_soups(soups)
    create_dataframe_from_soup(results, filename_dataframe)
