#!/usr/bin/env python

import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Load the parquet file into a DataFrame
df = pd.read_parquet("2024-Aug-20-15-58-dataframe.parquet")

bin_size_odo = 15_000
bin_size_age = 12
cut_year = 2005
cut_odo = 250_000
num_before = df.shape[0]

# Data cleaning
df["Year"] = pd.to_numeric(df["Year"], errors="coerce")  # Convert the Year column to numeric, forcing any errors to NaN and then dropping those rows
df["Odometer_km"] = pd.to_numeric(df["Odometer_km"], errors="coerce")  # Convert the Odometer column to numeric, forcing any errors to NaN and then dropping those rows
df = df.dropna(subset=["Year"])  # Drop rows where Year is NaN (if any exist after conversion)
df = df.dropna(subset=["Odometer_km"])
df["Year"] = df["Year"].astype(int)  # Convert the Year column to integers after cleaning
df["Odometer_km"] = df["Odometer_km"].astype(int)  # Convert the Year column to integers after cleaning
df = df[df["Year"] >= cut_year]  # Drop listings where the Year is before 2000
df = df[df["Odometer_km"] <= cut_odo]  # Drop listings where the Year is before 2000
num_after = df.shape[0]

# Calculate age
df['Date'] = pd.to_datetime(df[['Year', 'Month']].assign(DAY=1))
today = pd.Timestamp(datetime.today())
df['Age'] = (today.year - df['Date'].dt.year) * 12 + (today.month - df['Date'].dt.month)
df = df.drop(columns=['Date'])

# Plotting the histogram for Odometer_km in bins of 10000 km
plt.figure(figsize=(14, 6))
plt.suptitle(f'Histograms of car listings. Number cars in plots: {num_after} (before cleaning: {num_before})\nCleaning: removed cars with model year before {cut_year} and cars with odometer above {cut_odo}km.', fontsize=16)

# Odometer histogram
plt.subplot(1, 2, 1)
plt.hist(df["Odometer_km"], bins=range(0, int(df["Odometer_km"].max()) + bin_size_odo, bin_size_odo), edgecolor="black")
plt.title(f"Histogram of Odometer Readings. Bin size: {bin_size_odo}km")
plt.xlabel("Odometer (km)")
plt.ylabel("Frequency")
plt.grid(True)

# Age histogram
plt.subplot(1, 2, 2)
plt.hist(df["Age"], bins=range(0, int(df["Age"].max()) + bin_size_age, bin_size_age), edgecolor="black")
plt.title(f"Histogram of car age in months. Bin size: {bin_size_age}months")
plt.xlabel("Age")
plt.ylabel("Frequency")
plt.grid(True)

plt.tight_layout()

# Save the plot as a PNG file
output_path = 'histogram.png'  # Replace with your desired file path
plt.savefig(output_path, format='png')
