FROM ubuntu:latest

RUN apt update -y && apt install -y python3.11 python3-pip openjdk-11-jre

COPY . /root
WORKDIR /root

RUN pip3 install -r requirements.txt

RUN chmod 755 entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
