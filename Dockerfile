# app/Dockerfile

FROM python:3.13-slim

LABEL org.opencontainers.image.title="RetroWetter"
LABEL org.opencontainers.image.description="A simple app to visualize weather data to show climate trends."
LABEL org.opencontainers.image.version="0.1.0"
LABEL org.opencontainers.image.authors="wichmann@bbs-os-brinkstr.de"
LABEL org.opencontainers.image.licenses="MIT License"
LABEL org.opencontainers.image.documentation="https://github.com/wichmann/retrowetter/blob/master/README.md"
LABEL org.opencontainers.image.source="https://github.com/wichmann/retrowetter"

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

COPY * /app/
COPY data/stations.csv /app/data/
COPY locales/ /app/locales/

RUN pip3 install -r requirements.txt

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
