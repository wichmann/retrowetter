
"""
A simple Streamlit app to visualize climate data provided by the DWD (Deutscher
Wetterdienst).

This app allows users to select a weather station, view daily measurements, and
analyze heat days and specific dates over the years.
"""

import gettext

import babel.core
import streamlit as st
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression

import dwd_provider


APP_TITLE = 'RetroWetter'


# set up translation
_ = gettext.gettext
language = st.sidebar.selectbox(_('Select language'), ['de', 'en'])
try:
  localizator = gettext.translation('messages', localedir='locales', languages=[language])
  localizator.install()
  _ = localizator.gettext 
except:
    pass


# set up locale for date formatting
locale = babel.core.Locale.parse(st.context.locale, sep='-')


@st.cache_data
def get_station_list():
    station_options = dwd_provider.read_stations_list()
    return station_options


@st.cache_data
def get_station_data(station_data):
    station_id = station_data[['Stations_id']]['Stations_id'].values[0]
    station_data = dwd_provider.prepare_data(station_id)
    return station_data


def prepare_sidebar():
    # create a sidebar for navigation
    st.sidebar.title(APP_TITLE)
    st.sidebar.write(_('This is a simple app to visualize climate data provided by the DWD.'))
    st.sidebar.header(_('Configuration'))


def prepare_station_selection():
    # create a dropdown to select a station
    st.sidebar.subheader(_('Select Station'))
    st.sidebar.write(_('Select a weather station by name.'))
    station_options = get_station_list()
    selected_station = st.sidebar.selectbox(
        label=_('Select weather station...'),
        options=station_options[['Stationsname']],
        index=10
    )
    # get index of the selected station and get measurements for that station
    selected_station_data = station_options[station_options['Stationsname'] == selected_station]
    return selected_station_data


def prepare_time_selection(daily_measurements):
    # create a double slider to select a range of years
    st.sidebar.subheader(_('Select Year Range'))
    st.sidebar.write(_('Select a year range to view weather data.'))
    year_range = st.sidebar.slider(
        _('Select Year Range'),
        min_value=int(daily_measurements.index.year.min()),
        max_value=int(daily_measurements.index.year.max()),
        value=(int(daily_measurements.index.year.min()), int(daily_measurements.index.year.max())),
        step=1
    )
    # create input fields to select a specific date  
    st.sidebar.subheader(_('Select Specific Date'))
    st.sidebar.write(_('Select a specific date to view that days weather.'))
    selected_date = st.sidebar.date_input(
        _('Select Date'),
        value=daily_measurements.index[-1].date(),
        min_value=daily_measurements.index.min().date(),
        max_value=daily_measurements.index.max().date()
    )
    return selected_date, year_range


def prepare_todays_measurements(container, daily_measurements, selected_date):
    todays_measurements, yesterdays_measurements = dwd_provider.calculate_measurements_for_today_and_yesterday(daily_measurements, selected_date)
    container.header(_('📅 Some days weather'))
    col1, col2, col3 = container.columns(3)
    todays_minimum = todays_measurements['TNK'].values[0]
    yesterdays_minimum = yesterdays_measurements['TNK'].values[0]
    col1.metric(_('Daily minimum of air temperature'), f"{todays_minimum} °C", f'{todays_minimum-yesterdays_minimum:.1f} °C', border=True)
    todays_middle = todays_measurements['TMK'].values[0]
    yesterdays_middle = yesterdays_measurements['TMK'].values[0]
    col2.metric(_('Daily average of temperature'), f"{todays_middle} °C", f'{todays_middle-yesterdays_middle:.1f} °C', border=True)
    todays_maximum = todays_measurements['TXK'].values[0]
    yesterdays_maximum = yesterdays_measurements['TXK'].values[0]
    col3.metric(_('Daily maximum of air temperature'), f"{todays_maximum} °C", f'{todays_maximum-yesterdays_maximum:.1f} °C', border=True)
    todays_rain = todays_measurements['RSK'].values[0]
    yesterdays_rain = yesterdays_measurements['RSK'].values[0]
    col1.metric(_('Daily rainfall'), f"{todays_rain} mm", f'{todays_rain-yesterdays_rain:.1f} mm', border=True)
    if 'RSKF' in todays_measurements and dwd_provider.check_if_value_is_valid(todays_measurements['RSKF'].values[0]):
        todays_rain_type = todays_measurements['RSKF'].values[0]
        yesterdays_rain_type = yesterdays_measurements['RSKF'].values[0]
        todays_rain_type_str = f'{dwd_provider.get_rain_type(todays_rain_type)}'
        yesterdays_rain_type_str = f'{dwd_provider.get_rain_type(yesterdays_rain_type)}'
        col2.metric(_('Type of Rain'), todays_rain_type_str, yesterdays_rain_type_str, border=True, delta_color='off')
    if 'SHK_TAG' in todays_measurements and dwd_provider.check_if_value_is_valid(todays_measurements['SHK_TAG'].values[0]):
        todays_snow = todays_measurements['SHK_TAG'].values[0]
        yesterdays_snow = yesterdays_measurements['SHK_TAG'].values[0]
        col3.metric(_('Daily snow fall'), f"{todays_snow} cm", f'{todays_snow-yesterdays_snow:.1f} cm', border=True)
    if 'UPM' not in todays_measurements or dwd_provider.check_if_value_is_valid(todays_measurements['UPM'].values[0]):
        todays_upm = todays_measurements['UPM'].values[0]
        yesterdays_upm = yesterdays_measurements['UPM'].values[0]
        col1.metric(_('Daily average of relative humidity'), f"{todays_upm} %", f'{todays_upm-yesterdays_upm:.1f} %', border=True)
    if 'PM' in todays_measurements and dwd_provider.check_if_value_is_valid(todays_measurements['PM'].values[0]):
        todays_vpm = todays_measurements['PM'].values[0]
        yesterdays_vpm = yesterdays_measurements['PM'].values[0]
        col2.metric(_('Daily average of vapor pressure'), f"{todays_vpm} hPa", f'{todays_vpm-yesterdays_vpm:.1f} hPa', border=True)
    if 'NM' in todays_measurements and dwd_provider.check_if_value_is_valid(todays_measurements['NM'].values[0]):
        todays_nm = todays_measurements['NM'].values[0]
        yesterdays_nm = yesterdays_measurements['NM'].values[0]
        col3.metric(_('Cloud amount'), f"{dwd_provider.get_cloudiness_type(todays_nm)}", f"{dwd_provider.get_cloudiness_type(yesterdays_nm)}", border=True)


def prepare_heat_days(container, daily_measurements):    
    container.header(_('🥵 Heat Days per Year'))
    container.write(_('Heat Days Data (Days with Maximum Temperature >= 30°C)'))
    heat_days = dwd_provider.calculate_heat_days_per_year(daily_measurements)
    fig = create_heat_days_chart(heat_days)
    container.plotly_chart(fig, use_container_width=True)
    with container.expander(_('Raw data')):
        # display the heat days data as a table
        st.write(_('Heat Days, Desert Days and Tropical Nights per Year'))
        st.dataframe(heat_days.reset_index(), use_container_width=True)


def create_heat_days_chart(heat_days):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=heat_days.index, y=heat_days['heatdays'],
                        name=_('heat days per year'),
                        marker_color='indianred'))
    fig.add_trace(go.Bar(x=heat_days.index, y=heat_days['desertdays'],
                        name=_('desert days per year'),
                        marker_color='blue'))
    fig.add_trace(go.Bar(x=heat_days.index, y=heat_days['tropicalnights'],
                        name=_('tropical nights per year'),
                        marker_color='green'))
    fig.add_trace(go.Scatter(x=heat_days.index, y=create_trend(heat_days, 'heatdays'), mode='lines',
                             name=_('heat days trend'), marker_color='indianred'))
    fig.update_layout(xaxis_title=_('Year'), yaxis_title=_('Number of days'),
                    legend=dict(orientation='h', y=1.1), barmode='overlay')
    return fig


def create_trend(df, column_name):
    model = LinearRegression()
    X = df.index.values.reshape(-1, 1)
    Y = df[[column_name]].values
    model.fit(X, Y)
    predicted_y = model.predict(X)
    #heat_data[f'{column_name}trend'] = model.predict(X)
    predicted_y = predicted_y.flatten()
    return predicted_y


def prepare_this_day_over_years(container, daily_measurements, selected_date):
    container.header(_('📈 One day over the years'))
    this_day_in_year_measurements = dwd_provider.calculate_temperatures_for_this_day_over_years(daily_measurements, selected_date.month, selected_date.day)
    # create a line chart for the selected date
    container.line_chart(this_day_in_year_measurements,
                         x_label=_('Years'), y_label=_('Temperature °C'),
                         color= ('#ff0', '#00f', '#f00'), use_container_width=True)
    with container.expander(_('Raw data')):
        # display the daily measurements data as a table
        st.write(f'Measurements for {selected_date.day:02d}.{selected_date.month:02d} over the years')
        st.dataframe(this_day_in_year_measurements.reset_index(), use_container_width=True)


def prepare_map(container, selected_station_data):
    container.header(_('📍 Weather station location'))
    container.map(selected_station_data, latitude='geoBreite', longitude='geoLaenge', zoom=7, use_container_width=True)


def prepare_yearly_median(container, daily_measurements):
    container.header(_('📊 Yearly Median'))
    yearly_median = dwd_provider.calculate_yearly_median(daily_measurements)
    container.line_chart(yearly_median, x_label=_('Years'), y_label=_('Temperature °C'), use_container_width=True)
    with container.expander(_('Raw data')):
        # display the daily measurements data as a table
        st.write(_('Yearly median of daily average temperature'))
        st.dataframe(yearly_median.reset_index(), use_container_width=True)


def prepare_rainfall_in_month_over_the_years(container, daily_measurements, selected_date):
    container.header(_('🌧️ Rainfall in Month over the Years'))
    rainfall_in_month = dwd_provider.calculate_rainfall_per_month_over_years(daily_measurements, selected_date.month)
    container.bar_chart(rainfall_in_month, x_label=_('Years'), y_label=_('Rainfall in Month (mm)'), use_container_width=True)
    with container.expander(_('Raw data')):
        # display the daily measurements data as a table
        st.write(_('Rainfall in Month over the years'))
        st.dataframe(rainfall_in_month.reset_index(), use_container_width=True)


def main():
    about_text = _('A simple app to visualize climate data provided by the DWD.')
    st.set_page_config(
        page_title='',
        page_icon='☀️',
        layout='wide',
        initial_sidebar_state='expanded',
        menu_items={
            #'Get Help': 'https://www.extremelycoolapp.com/help',
            #'Report a bug': "https://www.extremelycoolapp.com/bug",
            'About': f'# {APP_TITLE}\n{about_text}'
        }
    )
    st.title(APP_TITLE)
    prepare_sidebar()
    selected_station_data = prepare_station_selection()
    daily_measurements = get_station_data(selected_station_data)
    selected_date, year_range = prepare_time_selection(daily_measurements)
    daily_measurements = dwd_provider.filter_dataframe_by_year(daily_measurements, year_range[0], year_range[1])
    maincol1, maincol2 = st.columns([1,1], gap='medium')
    prepare_todays_measurements(maincol1, daily_measurements, selected_date)
    prepare_this_day_over_years(maincol1, daily_measurements, selected_date)
    prepare_map(maincol1, selected_station_data)
    prepare_yearly_median(maincol2, daily_measurements)
    prepare_heat_days(maincol2, daily_measurements)
    prepare_rainfall_in_month_over_the_years(maincol2, daily_measurements, selected_date)


if __name__ == "__main__":
    main()
