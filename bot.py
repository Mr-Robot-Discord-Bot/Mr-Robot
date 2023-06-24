import asyncio
import logging
import os
import subprocess
import time
from typing import Any

import aiohttp
import aiosqlite
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
DB_REPO = os.getenv("db_repo")
logger = logging.getLogger(__name__)


class MrRobot(commands.AutoShardedInteractionBot):
    """Mr Robot Bot"""

    def __init__(self, session, db, **kwargs):
        super().__init__(**kwargs)
        self.pool = mafic.NodePool(self)  # type: ignore
        self.loop.create_task(self.add_nodes())
        self.start_time = time.time()
        self.session = session
        self.db = db
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
                logger.error(f"Unexpected response code {resp.status} for {url}")
                raise Exception(f"Unexpected response code {resp.status} for {url}")

    async def add_nodes(self):
        """Adds Nodes to the pool"""
        exp_pow = 1
        while True:
            try:
                await self.wait_until_ready()
                await self.pool.create_node(
                    host="lavalink",
                    port=2333,
                    label="MAIN",
                    password="youshallnotpass",
                )
                break
            except Exception:
                await asyncio.sleep(2**exp_pow)
                exp_pow += 1
                logger.warning(f"Trying to reload player after {2**exp_pow} seconds")

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
    try:
        subprocess.run(f"git clone {DB_REPO}", shell=True, check=True)
        file = DB_REPO.split("/")[-1].split(".")[0] if DB_REPO else None
        subprocess.run(f"mv {file}/mr-robot.db .", shell=True, check=True)
    except subprocess.CalledProcessError:
        logger.warning("Unable to clone db repo")
    async with aiohttp.ClientSession() as session:
        client = MrRobot(
            proxy=PROXY,
            intents=disnake.Intents.all(),
            session=session,
            db=await aiosqlite.connect("mr-robot.db"),
        )
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
