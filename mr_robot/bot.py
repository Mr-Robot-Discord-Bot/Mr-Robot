import asyncio
import logging
import time
from typing import Dict, List

import httpx
import mafic
from aiocache import cached
from disnake.ext import commands
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from mr_robot.constants import Client, Database, Lavalink
from mr_robot.database import Base
from mr_robot.utils.extensions import walk_extensions
from mr_robot.utils.git_api import Git

logger = logging.getLogger(__name__)


class MrRobot(commands.AutoShardedInteractionBot):
    """Mr Robot Bot"""

    def __init__(self, http_session: httpx.AsyncClient, **kwargs):
        super().__init__(**kwargs)
        self.pool = mafic.NodePool(self)
        self.loop.create_task(self.add_nodes())
        self.start_time = time.time()
        self.http_session = http_session
        self.token = Client.github_token
        self.repo = Client.github_db_repo
        self.git = None
        self.db_exsists = True
        self.db_engine = create_async_engine(Database.uri)
        self.db_session = async_sessionmaker(
            self.db_engine, expire_on_commit=False, class_=AsyncSession
        )
        if self.token and self.repo:
            owner, repo = self.repo.split("/")
            self.git = Git(
                token=self.token,
                owner=owner,
                repo=repo,
                username=Client.name,
                email=f"{Client.name}@mr_robot_discord_bot.com",
                client=http_session,
            )
        logger.info("Mr Robot is ready")

    @property
    def db(self) -> async_sessionmaker[AsyncSession]:
        """Alias of bot.db_session"""
        return self.db_session

    async def init_db(self) -> None:
        """Initializes the database"""
        async with self.db_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def close(self) -> None:
        """Close session when bot is shutting down"""
        await super().close()
        if self.db_engine:
            await self.db_engine.dispose()
        if self.http_session:
            await self.http_session.aclose()

    @cached(ttl=60 * 60 * 12)
    async def _request(self, url: str) -> Dict | List:
        resp = await self.http_session.get(url, headers={"User-Agent": "Magic Browser"})
        logger.info(f"HTTP Get: {resp.status_code} {url}")
        if resp.status_code == 200:
            return resp.json()
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
                    host=Lavalink.host,
                    port=Lavalink.port,
                    password=Lavalink.password,
                    label=Lavalink.label,
                )
                break
            except Exception:
                await asyncio.sleep(2**exp_pow)
                exp_pow += 1
                logger.warning(f"Trying to reload player after {2**exp_pow} seconds")

    def load_bot_extensions(self) -> None:
        """Loads extensions released by walk_extensions()"""
        for ext in walk_extensions():
            logger.info(f"{ext} extension loaded!!")
            self.load_extension(ext)
        logger.info("Extension loading successful!")
