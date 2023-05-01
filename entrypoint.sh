#!/bin/sh
cat > .env << EOF
Mr_Robot=$1
whtraffic=$2
openai_api_key=$3
mongodb_uri=$4
EOF
cd lavalink_server ; java -jar Lavalink.jar &
cd /root && python3 bot.py
