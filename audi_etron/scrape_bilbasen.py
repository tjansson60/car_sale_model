#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import pickle
import tqdm
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Setup gecko
sys.setrecursionlimit(100000)  # default is 1000. Needed to be increased to save soup
driver_path = "/home/tjansson/bin/geckodriver"
timestamp = datetime.datetime.now().strftime("%Y-%b-%d")

url = """https://www.bilbasen.dk/brugt/bil/Audi/e-tron?
    IncludeEngrosCVR=true&
    PriceFrom=0&
    includeLeasing=false&
    IncludeCallForPrice=false&
    page={}
"""


def load_url_soup(filename):
    with open(filename, "rb") as f:
        results = pickle.load(f)
    return results


def save_url_soup(url, filename, pages=12, debug=False):
    """Defaults to 32 listings per page, so 687 results requires 150/32 = 4.. pages"""
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
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
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

    # Car type
    df["S-line"] = False
    df.loc[df["headline"].str.contains("S-line"), "S-line"] = True

    # EngineNumber
    df["EngineNumber"] = None
    df.loc[df["headline"].str.contains("50"), "EngineNumber"] = 50
    df.loc[df["headline"].str.contains("55"), "EngineNumber"] = 55

    # Quattro - Pointless as they are all Quattro
    # df["Quattro"] = None
    # df.loc[df["headline"].str.contains("uattro"), "Quattro"] = True

    # Sportback
    df["Sportback"] = None
    df.loc[df["headline"].str.contains("Sportback"), "Sportback"] = True

    # Prestige
    df["Prestige"] = None
    df.loc[df["headline"].str.contains("Prestige"), "Prestige"] = True

    # Trim
    df["trim"] = np.nan
    df.loc[df["headline"].str.contains("Advanced"), "trim"] = "Advanced"
    df.loc[df["headline"].str.contains("Attitude"), "trim"] = "Attitude"
    df.loc[df["headline"].str.contains("edition"), "trim"] = "edition one"

    print(df)
    print(f"Number of cars: {df.shape[0]}")

    df.drop_duplicates(inplace=True)
    print(f"Number of cars: {df.shape[0]} after deduplication")

    # Save the file
    df.to_parquet(filename)
    print(f"Dataframe saved to {filename}")


if __name__ == "__main__":
    filename_soups = f"{timestamp}-soups.pickle"
    filename_dataframe = f"{timestamp}-dataframe.parquet"

    save_url_soup(url, filename_soups, pages=12)
    soups = load_url_soup(filename_soups)
    results = parse_soups(soups)
    create_dataframe_from_soup(results, filename_dataframe)
