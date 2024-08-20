#!/usr/bin/env python

from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import datetime
import time

timestamp = datetime.datetime.now().strftime("%Y-%b-%d_%H-%M-%S")


def parse_car_listings(html_content):
    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(html_content, "html.parser")

    # Initialize lists to hold the data
    car_models = []
    prices = []
    years = []
    months = []
    odometers = []
    fuel_types = []

    # Find all car listings
    listings = soup.find_all("div", class_="Listing_makeModel__7yqgs")

    for listing in listings:
        # Extract car model
        model = listing.find("h3", class_="font-bold").text.strip()

        # Extract price
        price = (
            (
                listing.find_next("div", class_="Listing_price__6B3kE")
                .find("h3", class_="font-bold color-primary")
                .text.strip()
            )
            .split(" kr.")[0]
            .replace(".", "")
        )

        # Extract details like year, km, range, fuel type
        detail_elements = listing.find_next("ul", class_="ListingDetails_list__WPBUe").find_all("li")
        year = month = odometer = fuel_type = None

        for detail in detail_elements:
            detail_text = detail.text.strip()
            if " km" in detail_text and " km/l" not in detail_text and " rækkevidde" not in detail_text:
                odometer = detail_text.replace(" km", "").replace(".", "")
            if "/" in detail_text and " km/l" not in detail_text:
                year = detail_text.split("/")[1]
                month = detail_text.split("/")[0]
            else:
                fuel_type = detail_text

        # Append the data to the lists
        car_models.append(model)
        prices.append(price)
        years.append(year)
        months.append(month)
        odometers.append(odometer)
        fuel_types.append(fuel_type)

    # Create a DataFrame from the extracted data
    df = pd.DataFrame(
        {
            "Model": car_models,
            "Price_DKK": prices,
            "Year": years,
            "Month": months,
            "Odometer_km": odometers,
            "Fuel_Type": fuel_types,
        }
    )

    return df


def extract_data_to_parquet(base_url, output_file, debug=False):
    options = webdriver.ChromeOptions()
    options.headless = True  # Run in headless mode
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    # Remove the "navigator.webdriver" property to avoid detection
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    all_data = pd.DataFrame()

    page_number = 1
    while True:
        print(f"Loading page {page_number}...")
        if page_number == 1:
            url = base_url
            driver.get(url)
            time.sleep(5)  # Do this first time only
        else:
            url = f"{base_url}&page={page_number}"
            driver.get(url)

        # Wait for the page to fully load
        try:
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "html")))
        except TimeoutException:
            print(f"Timeout reached while loading page {page_number}. Ending extraction.")
            break

        # Get the entire page source
        page_source = driver.page_source

        # Save the full page source to an HTML file
        if debug:
            filename_html = f"{timestamp}-page-{page_number}-page_source.html"
            with open(filename_html, 'w', encoding='utf-8') as file:
                file.write(page_source)
            print(f"Full page source saved to {filename_html}")

        # Parse the HTML and append the data to all_data
        page_data = parse_car_listings(page_source)
        if page_data.empty:
            print("No more data found, ending extraction.")
            break

        all_data = pd.concat([all_data, page_data], ignore_index=True)
        page_number += 1

    driver.quit()

    # Save the DataFrame to a Parquet file
    print(all_data)
    all_data.to_parquet(output_file)
    print(f"Data extraction complete. Saved to {output_file}")


if __name__ == "__main__":
    # base_url = "https://www.bilbasen.dk/brugt/bil/vw/ms-golf-serie?includeengroscv=true&includeleasing=false&make=vw&model=vw-golf_vii&model=vw-golf_vii&model=vw-golf_vi&model=vw-golf_iv&model=vw-golf_iii&model=vw-golf_ii"
    base_url = "https://www.bilbasen.dk/brugt/bil/audi/ms-a3-serie?includeengroscvr=true&includeleasing=false&make=seat&make=skoda&make=vw&model-seat=leon&model-skoda=ms-octavia-serie&model-vw=ms-golf-serie"
    timestamp = datetime.datetime.now().strftime("%Y-%b-%d-%H-%M")
    filename_dataframe = f"{timestamp}-dataframe.parquet"
    extract_data_to_parquet(base_url, filename_dataframe, debug=False)
