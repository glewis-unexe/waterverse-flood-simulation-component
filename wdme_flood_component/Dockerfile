#docker build -t gaztastic/wdme_flood_component:8 .
#docker push gaztastic/wdme_flood_component:8

FROM python:3.13
EXPOSE 9999

COPY . /app


RUN apt-get update -y
RUN apt-get upgrade -y
RUN apt-get install -y nano

WORKDIR /app
RUN pip install -r requirements.txt

CMD ["fastapi", "run", "main.py", "--port", "9999"]

