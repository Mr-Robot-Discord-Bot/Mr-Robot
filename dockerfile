FROM ubuntu:latest

RUN apt update -y && apt install -y python3.11 python3-pip git libraqm*

COPY . /root
WORKDIR /root

RUN pip3 install -r requirements.txt

RUN chmod 755 entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
