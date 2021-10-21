FROM continuumio/miniconda3
RUN apt-get update && apt-get -y install build-essential
RUN pip install folium flask && conda install geopandas
RUN mkdir /src
RUN mkdir /logs && touch /logs/logs.log
COPY . /src/
RUN rm /src/Dockerfile
RUN chmod +x  /src/server.py
ENTRYPOINT cd /src && python server.py
EXPOSE 5000