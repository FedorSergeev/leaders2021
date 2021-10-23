FROM continuumio/miniconda3
RUN apt-get update && apt-get -y  upgrade && apt-get -y install build-essential
RUN conda update conda
RUN conda install python=3.8 geopandas
RUN mkdir /src
RUN mkdir /src/logs && touch /src/logs/logs.log
COPY . /src/
RUN rm /src/Dockerfile
RUN pip install -r /src/requirements.txt
RUN chmod +x  /src/server.py
ENTRYPOINT cd /src && python server.py
EXPOSE 5000