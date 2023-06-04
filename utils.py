import datetime
import logging
import random
import re
from functools import partial
from typing import Any

import aiohttp
import disnake
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


def parse_time(duration: str):
    PATTERNS = {
        "seconds": r"(\d+)\s*(?:seconds?|secs?|s)\b",
        "minutes": r"(\d+)\s*(?:minutes?|mins?|m)\b",
        "hours": r"(\d+)\s*(?:hours?|hrs?|h)\b",
        "days": r"(\d+)\s*(?:days?|day)\b",
        "weeks": r"(\d+)\s*(?:weeks?|wk|w)\b",
        "months": r"(\d+)\s*(?:months?)\b",
    }
    result = dict.fromkeys(PATTERNS, 0)

    def _extract(key: str, match: re.Match[str]) -> str:
        value = int(match.group(1))
        result[key] = value
        return " "

    for key, pattern in PATTERNS.items():
        extractor = partial(_extract, key)
        duration = re.sub(pattern, extractor, duration, count=1)

    if duration.isspace():
        return datetime.timedelta(
            seconds=result["seconds"],
            minutes=result["minutes"],
            days=result["days"],
            weeks=result["weeks"] + result["months"] * 4,
            hours=result["hours"],
        )
    keys = re.findall(r"\d+\s*\S+", duration)
    keys = ", ".join(map(repr, keys))
    raise ValueError(f"Failed to parse {keys}")


delete_button: disnake.ui.Button = disnake.ui.Button(
    emoji="💣", style=disnake.ButtonStyle.red, custom_id="delete"
)


def url_button_builder(label: str, url: str, emoji: str) -> disnake.ui.Button:
    """Returns a url button"""
    return disnake.ui.Button(
        label=label, url=url, style=disnake.ButtonStyle.link, emoji=emoji
    )


class Embeds(disnake.Embed):
    """Embeds"""

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
            content, embed=embed, username=username, avatar_url=avatar_url  # type: ignore
        )
