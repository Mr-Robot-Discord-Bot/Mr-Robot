import asyncio
import logging
import os
import time
from typing import Any

import aiosqlite
import disnake
import httpx
import mafic
from aiocache import cached
from disnake.ext import commands
from dotenv import load_dotenv

from git_api import Git
from utils import proxy_generator

proxy_mode = False
PROXY = None

file_handler = logging.FileHandler("mr-robot.log", mode="w")
console_handler = logging.StreamHandler()

file_handler.setLevel(logging.INFO)
console_handler.setLevel(logging.INFO)
logging.basicConfig(
    level=logging.NOTSET,
    format="%(levelname)s - %(name)s - %(filename)s - %(module)s - %(funcName)s - %(message)s",
    handlers=[console_handler, file_handler],
)

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("disnake").setLevel(logging.INFO)
logging.getLogger("aiosqlite").setLevel(logging.INFO)
logger = logging.getLogger(__name__)


class MrRobot(commands.AutoShardedInteractionBot):
    """Mr Robot Bot"""

    def __init__(self, session: httpx.AsyncClient, db, db_name, **kwargs):
        super().__init__(**kwargs)
        self.pool = mafic.NodePool(self)  # type: ignore
        self.loop.create_task(self.add_nodes())
        self.start_time = time.time()
        self.session = session
        self.db = db
        self.token = os.getenv("db_token")
        self.repo = os.getenv("db_repo")
        self.git = None
        self.db_name = db_name
        if self.token and self.repo:
            owner, repo = self.repo.split("/")
            self.git = Git(
                token=self.token,
                owner=owner,
                repo=repo,
                username="Mr Robot",
                email="mr_robot@mr_robot_discord_bot.com",
                client=session,
            )
        logger.info("Mr Robot is ready")

    @cached(ttl=60 * 60 * 12)
    async def _request(self, url: str) -> Any:
        resp = await self.session.get(url, headers={"User-Agent": "Magic Browser"})
        logger.info(f"HTTP Get: {resp.status_code} {url}")
        if resp.status_code == 200:
            return await resp.json()
        else:
            logger.error(
                f"HTTP Get Error: Status: {resp.status_code} Url: {url} Text: {resp.text} Req Header: {resp.request.headers} Res Header: {resp.headers}"
            )
            raise Exception(f"Unexpected response code {resp.status_code} for {url}")

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
    db_name = "mr-robot.db"
    async with httpx.AsyncClient(timeout=httpx.Timeout(None)) as session:
        client = MrRobot(
            proxy=PROXY,
            intents=disnake.Intents.all(),
            session=session,
            db=await aiosqlite.connect(db_name),
            db_name=db_name,
        )
        if client.git:
            logger.info("Pulling DB")
            await client.git.pull(db_name)
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
