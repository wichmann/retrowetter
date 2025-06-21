
"""
A simple Streamlit app to visualize climate data provided by the DWD (Deutscher
Wetterdienst).

This app allows users to select a weather station, view daily measurements, and
analyze heat days and specific dates over the years.
"""

import pandas as pd
import streamlit as st

import dwd_provider


APP_TITLE = 'RetroWetter'


@st.cache_data
def get_station_list():
    station_options = dwd_provider.read_stations_list()
    return station_options


def prepare_sidebar():
    # create a sidebar for navigation
    st.sidebar.title(APP_TITLE)
    st.sidebar.write('This is a simple app to visualize climate data provided by the DWD.')
    st.sidebar.header('Configuration')

    # create a dropdown to select a station
    st.sidebar.subheader('Select Station')
    st.sidebar.write('Select a weather station by name.')
    station_options = get_station_list()
    selected_station = st.sidebar.selectbox(
        label='Select weather station...',
        options=station_options[['Stationsname']],
        index=10
    )

    # get index of the selected station and get measurements for that station
    selected_station_data = station_options[station_options['Stationsname'] == selected_station]
    selected_station_id = selected_station_data[['Stations_id']]['Stations_id'].values[0]
    daily_measurements = dwd_provider.prepare_data(selected_station_id)

    # create a double slider to select a range of years
    st.sidebar.subheader('Select Year Range')
    st.sidebar.write('Select a year range to view weather data.')
    year_range = st.sidebar.slider(
        'Select Year Range',
        min_value=int(daily_measurements.index.year.min()),
        max_value=int(daily_measurements.index.year.max()),
        value=(int(daily_measurements.index.year.min()), int(daily_measurements.index.year.max())),
        step=1
    )

    # create input fields to select a specific date  
    st.sidebar.subheader('Select Specific Date')
    st.sidebar.write('Select a specific date to view that days weather.')
    selected_date = st.sidebar.date_input(
        'Select Date',
        value=daily_measurements.index[-1].date(),
        min_value=daily_measurements.index.min().date(),
        max_value=daily_measurements.index.max().date()
    )

    return daily_measurements, selected_date, year_range, selected_station_data


def prepare_todays_measurements(container, daily_measurements, selected_date):
    # filter the daily measurements data based on the selected date
    todays_measurements = daily_measurements[daily_measurements.index.date == selected_date]
    yesterdays_measurements = daily_measurements[daily_measurements.index.date == selected_date - pd.Timedelta(days=1)]
    # display the daily measurements data
    container.header('📅 Some days weather')
    col1, col2, col3 = container.columns(3)
    todays_minimum = todays_measurements['TNK'].values[0]
    yesterdays_minimum = yesterdays_measurements['TNK'].values[0]
    col1.metric("Tagesminimum der Lufttemperatur", f"{todays_minimum} °C", f'{todays_minimum-yesterdays_minimum:.1f} °C', border=True)
    todays_middle = todays_measurements['TMK'].values[0]
    yesterdays_middle = yesterdays_measurements['TMK'].values[0]
    col2.metric("Tagesmittel der Temperatur", f"{todays_middle} °C", f'{todays_middle-yesterdays_middle:.1f} °C', border=True)
    todays_maximum = todays_measurements['TXK'].values[0]
    yesterdays_maximum = yesterdays_measurements['TXK'].values[0]
    col3.metric("Tagesmaximum der Lufttemperatur", f"{todays_maximum} °C", f'{todays_maximum-yesterdays_maximum:.1f} °C', border=True)
    todays_rain = todays_measurements['RSK'].values[0]
    yesterdays_rain = yesterdays_measurements['RSK'].values[0]
    col1.metric("Tägliche Niederschlagshöhe", f"{todays_rain} mm", f'{todays_rain-yesterdays_rain:.1f} mm', border=True)
    rain_types = {
        0: 'kein Niederschlag',
        1: 'Regen',
        #2: 'Schnee',
        #3: 'Graupel',
        4: 'Regen', #'Unbekannt',
        #5: 'Eisregen',
        6: 'Regen',
        7: 'Schnee',
        8: 'Schneeregen',
        9: 'Fehlkennung'
    }
    if 'RSKF' in todays_measurements and todays_measurements['RSKF'].values[0] != 0:
        todays_rain_type = todays_measurements['RSKF'].values[0]
        yesterdays_rain_type = yesterdays_measurements['RSKF'].values[0]
        col2.metric('Niederschlagsform', f'{rain_types[todays_rain_type]}', f'{rain_types[yesterdays_rain_type]}', border=True, delta_color='off')
    if 'SHK_TAG' in todays_measurements and todays_measurements['SHK_TAG'].values[0] != 0 and todays_measurements['SHK_TAG'].values[0] != -999:
        todays_snow = todays_measurements['SHK_TAG'].values[0]
        yesterdays_snow = yesterdays_measurements['SHK_TAG'].values[0]
        col3.metric("Tägliche Schneehoehe", f"{todays_snow} cm", f'{todays_snow-yesterdays_snow:.1f} cm', border=True)
    todays_upm = todays_measurements['UPM'].values[0]
    yesterdays_upm = yesterdays_measurements['UPM'].values[0]
    col1.metric("Tagesmittel der Relativen Feuchte", f"{todays_upm} %", f'{todays_upm-yesterdays_upm:.1f} %', border=True)
    todays_vpm = todays_measurements['VPM'].values[0]
    yesterdays_vpm = yesterdays_measurements['VPM'].values[0]
    col2.metric("Tagesmittel des Dampfdruckes", f"{todays_vpm} hPa", f'{todays_vpm-yesterdays_vpm:.1f} hPa', border=True)
    if 'NM' in todays_measurements and todays_measurements['NM'].values[0] != -999.0:
        todays_nm = todays_measurements['NM'].values[0]
        yesterdays_nm = yesterdays_measurements['NM'].values[0]
        cloudiness_types = {
            0: '☀️',
            1: '🌤️',
            2: '🌤️',
            3: '⛅',
            4: '⛅',
            5: '🌥️',
            6: '🌥️',
            7: '☁️',
            8: '☁️'
        }
        col3.metric("Bedeckungsgrad", f"{cloudiness_types[round(todays_nm, 0)]}", f"{cloudiness_types[round(yesterdays_nm, 0)]}", border=True)


def prepare_heat_days(container, daily_measurements, year_range):    
    heat_days = dwd_provider.count_heat_days_per_year(daily_measurements)
    # display the heat days data
    container.header('🥵 Heat Days per Year')
    container.write('Heat Days Data (Days with Maximum Temperature >= 30°C)')

    # filter the heat days data based on the selected year range
    heat_days = heat_days[(heat_days.index >= year_range[0]) & (heat_days.index <= year_range[1])]
    # create a line chart for heat days
    container.bar_chart(heat_days, stack='layered', use_container_width=True)
    with container.expander('Raw data'):
        # display the heat days data as a table
        st.write(f'Heat Days from {year_range[0]} to {year_range[1]}')
        st.dataframe(heat_days.reset_index(), use_container_width=True)


def prepare_this_day_over_years(container, daily_measurements, selected_date):
    container.header('📈 One day over the years')
    # extract only necessary columns from daily measurements
    this_day_in_year_measurements = daily_measurements[['TNK', 'TMK', 'TXK']]
    # filter the daily measurements data based on the selected date
    this_day_in_year_measurements = this_day_in_year_measurements[(daily_measurements.index.month == selected_date.month) & (daily_measurements.index.day == selected_date.day)]
    #if this_day_in_year_measurements.empty:
    #    container.write(f'No data available for {selected_date}.')
    #    return
    xx = {
        ' TNK': 'Tagesminimum',
        ' TMK': 'Tagesmittel',
        ' TXK': 'Tagesmaximum'
    }
    this_day_in_year_measurements= this_day_in_year_measurements.rename(columns=xx)
    # create a line chart for the selected date
    container.line_chart(this_day_in_year_measurements[['TNK', 'TMK', 'TXK']],
                         x_label='Years', y_label='Temperature °C',
                         # ('Minimaltemperatur °C', 'Mittlere Temperatur °C', 'Maximaltemperatur °C')
                         color= ('#ff0', '#00f', '#f00'), use_container_width=True)
    with container.expander('Raw data'):
        # display the daily measurements data as a table
        st.write(f'Measurements for {selected_date.day:02d}.{selected_date.month:02d} over the years')
        st.dataframe(this_day_in_year_measurements.reset_index(), use_container_width=True)


def prepare_map(container, selected_station_data):
    container.header('📍 Weather station location')
    container.map(selected_station_data, latitude='geoBreite', longitude='geoLaenge', zoom=7, use_container_width=True)


def prepare_yearly_median(container, daily_measurements):
    container.header('📊 Yearly Median')
    # calculate the yearly median for the daily measurements
    daily_measurements['year'] = daily_measurements.index.year
    yearly_median = daily_measurements.groupby('year')['TMK'].median().rename('yearly_median')
    # create a line chart for the yearly median
    container.line_chart(yearly_median, x_label='Years', y_label='Temperature °C', use_container_width=True)
    with container.expander('Raw data'):
        st.dataframe(yearly_median.reset_index(), use_container_width=True)


def main():
    st.set_page_config(
        page_title='',
        page_icon='☀️',
        layout='wide',
        initial_sidebar_state='expanded',
        menu_items={
            #'Get Help': 'https://www.extremelycoolapp.com/help',
            #'Report a bug': "https://www.extremelycoolapp.com/bug",
            'About': f'# {APP_TITLE}\nA simple app to visualize climate data provided by the DWD.'
        }
    )
    st.title(APP_TITLE)
    daily_measurements, selected_date, year_range, selected_station_data = prepare_sidebar()
    maincol1, maincol2 = st.columns([1,1], gap='medium')
    prepare_todays_measurements(maincol1, daily_measurements, selected_date)
    prepare_map(maincol1, selected_station_data)
    prepare_this_day_over_years(maincol2, daily_measurements, selected_date)
    prepare_yearly_median(maincol2, daily_measurements)
    prepare_heat_days(maincol2, daily_measurements, year_range)


if __name__ == "__main__":
    main()
