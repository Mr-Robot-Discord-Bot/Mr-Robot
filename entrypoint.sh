#!/bin/sh
cat > .env << EOF
Mr_Robot=$1
whtraffic=$2
openai_api_key=$3
db_token=$4
db_repo=$5
EOF
cd /root && python3 bot.py
