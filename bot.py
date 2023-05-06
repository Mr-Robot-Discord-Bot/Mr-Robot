import asyncio
import logging
import os
import time

import aiohttp
import disnake
import mafic
from disnake.ext import commands
from dotenv import load_dotenv

from utils import SESSION_CTX, proxy_generator

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


class MrRobot(commands.InteractionBot):
    """Mr Robot Bot"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.pool = mafic.NodePool(self)  # type: ignore
        self.loop.create_task(self.add_nodes())
        self.start_time = time.time()
        logger.info("Mr Robot is ready")

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
    client = MrRobot(proxy=PROXY, intents=disnake.Intents.all())
    async with aiohttp.ClientSession() as session:
        SESSION_CTX.set(session)
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
