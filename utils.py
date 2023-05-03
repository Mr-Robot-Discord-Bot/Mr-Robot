import datetime
import os
import random
import sys
from typing import Any

import aiohttp
import disnake
import pymongo
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

try:
    mongo_client = pymongo.MongoClient(os.getenv("mongodb_uri"))
    db = mongo_client.mr_robot
except Exception:
    print("utils.py: DB Error")
    sys.exit()


delete_button: disnake.ui.Button = disnake.ui.Button(
    emoji="💣", style=disnake.ButtonStyle.red
)


class Embeds:
    red = 0xFF0000
    green = 0x00FF00
    blue = 0x0000FF
    black = 0x000000
    orange = 0xFFA500
    yellow = 0xFFFF00

    @staticmethod
    def emb(color: Any = green, name="", value="") -> disnake.Embed:
        """Returns a embed"""
        Em = disnake.Embed(color=color, title=name, description=value)
        Em.timestamp = datetime.datetime.utcnow()
        Em.set_footer(
            text="MR ROBOT",
            icon_url="https://cdn.discordapp.com/avatars/1087375480304451727/"
            "f780c7c8c052c66c89f9270aebd63bc2.png?size=1024",
        )
        return Em


def proxy_generator() -> str:
    """Generates a proxy"""
    response = requests.get("https://sslproxies.org/")
    soup = BeautifulSoup(response.content, "html5lib")
    proxy = "http://" + random.choice(
        list(
            map(
                lambda x: x[0] + ":" + x[1],
                list(
                    zip(
                        map(lambda x: x.text, soup.findAll("td")[::8]),
                        map(lambda x: x.text, soup.findAll("td")[1::8]),
                    )
                ),
            )
        )
    )
    return proxy


async def send_webhook(
    webhook_url,
    embed=None,
    content=None,
    username=None,
    avatar_url="https://cdn.discordapp.com/avatars"
    "/1087375480304451727/f780c7c8c052c66c89f9270aebd63bc2"
    ".png?size=1024",
):
    """Sends Webhook to the guild"""
    async with aiohttp.ClientSession() as session:
        webhook = disnake.Webhook.from_url(webhook_url, session=session)
        await webhook.send(
            content, embed=embed, username=username, avatar_url=avatar_url
        )
