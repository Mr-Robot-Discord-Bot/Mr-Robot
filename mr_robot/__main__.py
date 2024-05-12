import asyncio
import logging
import os

import aiosqlite
import disnake
import httpx
from dotenv import load_dotenv

from mr_robot.bot import MrRobot
from mr_robot.utils.helpers import proxy_generator

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
        client.load_bot_extensions()
        try:
            if token := os.getenv("BOT_TOKEN"):
                await client.start(token)
        except (disnake.errors.LoginFailure, disnake.errors.HTTPException):
            logger.warning(
                "Unable to connect to Discord falling back to proxy mode", exc_info=True
            )
            proxy_mode = True
            PROXY = proxy_generator() if proxy_mode else None
        finally:
            await client.close()


if __name__ == "__main__":
    asyncio.run(main())
