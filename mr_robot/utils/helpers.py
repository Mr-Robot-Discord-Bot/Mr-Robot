import datetime
import logging
import random
import re
import time
from functools import partial, wraps
from typing import Any, Awaitable, Callable, Optional

import aiohttp
import disnake
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from mr_robot.constants import Client

load_dotenv()
logger = logging.getLogger(__name__)


def parse_time(duration: str) -> datetime.timedelta:
    PATTERNS = {
        "seconds": r"(?i)(\d+)\s*(?:seconds?|secs?|s)\b",
        "minutes": r"(?i)(\d+)\s*(?:minutes?|mins?|m)\b",
        "hours": r"(?i)(\d+)\s*(?:hours?|hrs?|h)\b",
        "days": r"(?i)(\d+)\s*(?:days?|d)\b",
        "years": r"(?i)(\d+)\s*(?:years?|yrs?|y)\b",
        "weeks": r"(?i)(\d+)\s*(?:weeks?|wks?|w)\b",
        "months": r"(?i)(\d+)\s*(?:months?|mnths?|mons?)\b",
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
            days=result["days"] + result["months"] * 30 + result["years"] * 365,
            weeks=result["weeks"],
            hours=result["hours"],
        )
    keys = re.findall(r"\d+\s*\S+", duration)
    keys = ", ".join(map(repr, keys))
    raise ValueError(f"Failed to parse {keys}")


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
        Em.timestamp = datetime.datetime.now()
        Em.set_footer(
            text=Client.name,
            icon_url="https://cdn.discordapp.com/avatars/1239962447285063691/f780c7c8c052c66c89f9270aebd63bc2.webp?size=128",
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
    webhook_url: str,
    embed: Optional[disnake.Embed] = None,
    content: Optional[str] = None,
    username: str = "Discord Webhook",
    avatar_url: str = "https://cdn.discordapp.com/avatars"
    "/1087375480304451727/f780c7c8c052c66c89f9270aebd63bc2"
    ".png?size=1024",
) -> None:
    """Sends Webhook to the guild"""
    async with aiohttp.ClientSession() as session:
        webhook = disnake.Webhook.from_url(webhook_url, session=session)
        if embed:
            await webhook.send(embed=embed, username=username, avatar_url=avatar_url)
        elif content:
            await webhook.send(content, username=username, avatar_url=avatar_url)
        elif content and embed:
            await webhook.send(
                content, embed=embed, username=username, avatar_url=avatar_url
            )
        else:
            raise ValueError("Webhook content & embed is empty")


def log_elapsed_time[
    T, **P
](func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        start = time.perf_counter()

        func_ret = await func(*args, **kwargs)

        end = time.perf_counter()
        logger.debug(f"{func.__name__} took {end - start:.4f}")

        return func_ret

    return wrapper
