import asyncio
import logging
import os
import time
from typing import Dict, List

import httpx
import mafic
from aiocache import cached
from disnake.ext import commands
from git_api import Git

logger = logging.getLogger(__name__)


class MrRobot(commands.AutoShardedInteractionBot):
    """Mr Robot Bot"""

    def __init__(self, session: httpx.AsyncClient, db, db_name, **kwargs):
        super().__init__(**kwargs)
        self.pool = mafic.NodePool(self)
        self.loop.create_task(self.add_nodes())
        self.start_time = time.time()
        self.session = session
        self.db = db
        self.token = os.getenv("GIT_TOKEN")
        self.repo = os.getenv("GIT_DB_REPO")
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
    async def _request(self, url: str) -> Dict | List:
        resp = await self.session.get(url, headers={"User-Agent": "Magic Browser"})
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

    def load_bot_extensions(self):
        """Loads extensions"""
        for file in os.listdir("Cogs"):
            if file.endswith(".py"):
                try:
                    self.load_extension(f"Cogs.{str(file[:-3])}")
                except Exception as error:
                    raise error
