FROM python:3.11-slim

ENV PIP_NO_CACHE_DIR=false

RUN apt update && apt install -y libraqm*

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt


ENTRYPOINT ["python3", "bot.py"]
