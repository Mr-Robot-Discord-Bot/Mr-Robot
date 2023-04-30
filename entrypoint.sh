#!/bin/sh
cat > .env << EOF
Mr_Robot=$1
whtraffic=$2
whcontent=$3
openai_api_key=$4
mongodb_uri=$5
EOF
cd lavalink_server ; java -jar Lavalink.jar &
cd /root && python3 bot.py
