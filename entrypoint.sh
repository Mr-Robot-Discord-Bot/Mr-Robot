#!/bin/sh
cat > .env << EOF
Mr_Robot=$1
whtraffic=$2
openai_api_key=$3
db_repo=$4
git_ssh_key_pub=$5
git_ssh_key_priv=$6
git_ssh_known_host=$7
EOF
cd /root && python3 bot.py
