# Climate analysis from DWD weather data

Possible visualization libraries:
 - Dash
 - Streamlit
 - Bokeh
 - Plotly
 - PyScript
 - Jupyter Notebook

Data source:
 - https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/daily/kl/historical/

Sources:
 - https://www.dwd.de/DE/leistungen/cdc/cdc_ueberblick-klimadaten.html
 - https://github.com/jdemaeyer/dwdparse
 - Open weather data for humans. (wetterdienst.eobs.org, https://github.com/earthobservations/wetterdienst)

## Build
Run app for development:

    pipenv run streamlit run app.py

Build Docker container for development:

    docker build -t retrowetter .
    docker run -p 8501:8501 -d retrowetter

Update and create translation files:

    pipenv run pybabel extract . -o locales/base.pot
    pybabel init -l de_DE en_US -i locales/base.pot -d locales
    pybabel update -i locales/base.pot -d locales
    pybabel compile -d locales

## Todo
- Reimplement with Dash (https://dash.plotly.com/minimal-app) to compare with Steamlit.
- Use Bokeh for plots.
- Run app directly in browser with PyScript (https://pyscript.com/@examples/bokeh/latest).
