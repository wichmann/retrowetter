
"""
This script downloads and processes climate data from the German Weather
Service (DWD).

It retrieves daily and monthly climate data, including station information,
and provides functions to read and manipulate this data using pandas. It
downloads the data files, reads them into pandas DataFrames, and allows for
further analysis or processing.
"""

import zipfile
from io import BytesIO

import requests
import numpy as np
import pandas as pd


# URLs for the DWD data
stations_list_url = 'https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/daily/kl/historical/KL_Tageswerte_Beschreibung_Stationen.txt'
measurements_data_url = 'https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/daily/kl/historical/tageswerte_KL_00078_19610101_20241231_hist.zip'
monthly_avergages_url = 'https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/monthly/kl/historical/monatswerte_KL_00078_19610101_20241231_hist.zip'


def download_file(url):
    response = requests.get(url)
    if response.status_code == 200:
        return BytesIO(response.content)
    else:
        raise Exception(f"Failed to download file from {url}")

def read_csv_from_zip(zip_file, filename):
    with zipfile.ZipFile(zip_file) as z:
        with z.open(filename) as f:
            return pd.read_csv(f, sep=';', encoding='latin1', low_memory=False)

def read_stations_list():
    #stations_file = download_file(stations_list_url)
    with open('data/stations.csv', 'r', encoding='utf-8') as stations_file:
        stations_df = pd.read_csv(stations_file, sep=';')
    #stations_df.set_index('Stations_id', inplace=True)
    stations_df['von_datum'] = pd.to_datetime(stations_df['von_datum'], format='%Y%m%d')
    stations_df['bis_datum'] = pd.to_datetime(stations_df['bis_datum'], format='%Y%m%d')
    # eliminate all columns that are not needed
    stations_df = stations_df[['Stations_id', 'Stationsname', 'Bundesland', 'geoBreite', 'geoLaenge']]
    return stations_df

def read_measurements_data():
    measurements_file = download_file(measurements_data_url)
    return read_csv_from_zip(measurements_file, 'produkt_klima_tag_19610101_20241231_00078.txt')

def read_monthly_averages():
    monthly_file = download_file(monthly_avergages_url)
    return read_csv_from_zip(monthly_file, 'produkt_klima_monat_19610101_20241231_00078.txt')

def count_heat_days_per_year(df):
    """
    Count the number of heat days (days with maximum temperature >= 30°C)
    in the DataFrame.
    """
    df['year'] = df.index.year
    # df = df[df['TXK'] >= 30].groupby(df['year']).size()
    desertdays_data = df[df['TXK'] >= 35]
    desertdays_data = desertdays_data.groupby('year').size().rename('desertdays')
    heatdays_data = df[df['TXK'] >= 30]
    heatdays_data = heatdays_data.groupby('year').size().rename('heatdays')
    tropicalnights_data = df[df['TNK'] >= 20]
    tropicalnights_data = tropicalnights_data.groupby('year').size().rename('tropicalnights')
    return heatdays_data.to_frame().join(desertdays_data).join(tropicalnights_data).fillna(0)

def count_summer_days_per_year(df):
    """
    Count the number of very hot days (days with maximum temperature >= 25°C)
    in the DataFrame.
    """
    df['year'] = df.index.year
    return df[df['TXK'] >= 25].groupby('year').size()

def count_tropical_nights_per_year(df):
    """
    Count the number of tropical nights (days with minimum temperature >= 20°C)
    in the DataFrame.
    """
    df['year'] = df.index.year
    return df[df['TNK'] >= 20].groupby('year').size()


def prepare_data(station_id):
    # read the daily measurements data
    daily_measurements = read_csv_from_zip('data/tageswerte_KL_00078_19610101_20241231_hist.zip', 'produkt_klima_tag_19610101_20241231_00078.txt')
    #
    # NM;Tagesmittel des Bedeckungsgrades;Achtel;
    # RSK;tgl. Niederschlagshoehe;mm;
    # RSKF;tgl. Niederschlagsform (=Niederschlagshoehe_ind);numerischer Code;
    # SHK_TAG;Schneehoehe Tageswert;cm;
    # TGK;Minimum der Lufttemperatur am Erdboden in 5cm Hoehe;°C;
    # TMK;Tagesmittel der Temperatur;°C
    # TNK;Tagesminimum der Lufttemperatur in 2m Hoehe;°C;
    # TXK;Tagesmaximum der Lufttemperatur in 2m Höhe;°C
    # UPM;Tagesmittel der Relativen Feuchte;%;
    # VPM;Tagesmittel des Dampfdruckes;hpa;
    #
    # set second column as date
    daily_measurements['MESS_DATUM'] = pd.to_datetime(daily_measurements['MESS_DATUM'], format='%Y%m%d')
    daily_measurements.set_index('MESS_DATUM', inplace=True)
    # remove whitespaces from column header
    daily_measurements.rename(columns=lambda x: x.strip(), inplace=True)
    # fill missing values for temperature columns with NaN
    #  - TGK = Minimum der Lufttemperatur am Erdboden in 5cm Hoehe in °C
    #  - TMK = Tagesmittel der Temperatur in °C
    #  - TNK = Tagesminimum der Lufttemperatur in 2m Hoehe in °C
    #  - TXK = Tagesmaximum der Lufttemperatur in 2m Höhe in °C
    daily_measurements['TXK'] = pd.to_numeric(daily_measurements['TXK'], errors='coerce')
    daily_measurements['TNK'] = pd.to_numeric(daily_measurements['TNK'], errors='coerce')
    daily_measurements['TMK'] = pd.to_numeric(daily_measurements['TMK'], errors='coerce')
    daily_measurements['TGK'] = pd.to_numeric(daily_measurements['TGK'], errors='coerce')
    daily_measurements['RSK'] = pd.to_numeric(daily_measurements['RSK'], errors='coerce')
    return daily_measurements


def main():
    daily_measurements = prepare_data('78')
    # count heat days, summer days and tropical nights
    heat_days = count_heat_days_per_year(daily_measurements)
    summer_days = count_summer_days_per_year(daily_measurements)
    tropical_nights = count_tropical_nights_per_year(daily_measurements)
    
    # create diagram of heat days, summer days and tropical nights
    heat_days.plot(kind='bar', title='Heat Days per Year (TXK >= 30°C)')


if __name__ == "__main__":
    main()
