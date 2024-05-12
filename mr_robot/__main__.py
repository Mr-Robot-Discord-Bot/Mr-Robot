import asyncio
import logging
import signal
import sys

import aiosqlite
import disnake
import httpx
from dotenv import load_dotenv

from mr_robot.bot import MrRobot
from mr_robot.constants import Client

# from mr_robot.utils.helpers import proxy_generator

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
        try:
            client.load_bot_extensions()
        except Exception:
            await client.close()
            raise

        loop = asyncio.get_running_loop()

        future: asyncio.Future = asyncio.ensure_future(
            client.start(Client.token or ""), loop=loop
        )
        loop.add_signal_handler(signal.SIGINT, lambda: future.cancel())
        loop.add_signal_handler(signal.SIGTERM, lambda: future.cancel())

        try:
            await future
        except asyncio.CancelledError:
            logger.info("Received signal to terminate bot and event loop")
            # logger.warning(
            #     "Unable to connect to Discord falling back to proxy mode", exc_info=True
            # )
            # proxy_mode = True
            # PROXY = proxy_generator() if proxy_mode else None
        finally:
            if not client.is_closed():
                await client.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
