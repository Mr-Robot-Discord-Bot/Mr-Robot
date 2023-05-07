import asyncio
import logging
import os
import time
from typing import Any

import aiohttp
import disnake
import mafic
from aiocache import cached
from disnake.ext import commands
from dotenv import load_dotenv

from utils import proxy_generator

proxy_mode = False
PROXY = None
console_handler = logging.StreamHandler()
file_handler = logging.FileHandler("mr-robot.log")
console_handler.setLevel(logging.INFO)
file_handler.setLevel(logging.INFO)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(module)-15s - %(name)s - %(message)s",
    handlers=[console_handler, file_handler],
)
logger = logging.getLogger(__name__)


class MrRobot(commands.AutoShardedInteractionBot):
    """Mr Robot Bot"""

    def __init__(self, session, **kwargs):
        super().__init__(**kwargs)
        self.pool = mafic.NodePool(self)  # type: ignore
        self.loop.create_task(self.add_nodes())
        self.start_time = time.time()
        self.session = session
        logger.info("Mr Robot is ready")

    @cached(ttl=60 * 60 * 12)
    async def _request(self, url: str) -> Any:
        async with self.session.get(
            url, headers={"User-Agent": "Magic Browser"}
        ) as resp:
            if resp.status == 200:
                logger.info(f"Sending Http Request to {url}")
                return await resp.json()
            else:
                logger.error(f"Unexpected response code {resp.status}")
                raise Exception(f"Unexpected response code {resp.status}")

    async def add_nodes(self):
        """Adds Nodes to the pool"""
        await self.wait_until_ready()
        await self.pool.create_node(
            host="lavalink",
            port=2333,
            label="MAIN",
            password="youshallnotpass",
        )

    def load_extensions(self):
        """Loads extensions"""
        for file in os.listdir("Cogs"):
            if file.endswith(".py"):
                try:
                    self.load_extension(f"Cogs.{str(file[:-3])}")
                except Exception as error:
                    raise error


load_dotenv()


async def main():
    global PROXY
    async with aiohttp.ClientSession() as session:
        client = MrRobot(proxy=PROXY, intents=disnake.Intents.all(), session=session)
        client.load_extensions()
        try:
            await client.start(os.getenv("Mr_Robot"))  # type: ignore
        except (disnake.errors.LoginFailure, disnake.errors.HTTPException):
            logger.warning("Unable to connect to Discord falling back to proxy mode")
            proxy_mode = True
            PROXY = proxy_generator() if proxy_mode else None
        finally:
            await client.close()


if __name__ == "__main__":
    asyncio.run(main())
