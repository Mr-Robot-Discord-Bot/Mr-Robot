import asyncio
import atexit
import json
import logging.config
import logging.handlers
import os
import signal
import sys

import aiosqlite
import disnake
import httpx
from dotenv import load_dotenv

from mr_robot.bot import MrRobot
from mr_robot.constants import Client

load_dotenv()


def setup_logging() -> None:
    with open(Client.logging_config_file, "r") as file:
        config = json.load(file)
    try:
        os.mkdir("logs")
    except FileExistsError:
        ...
    logging.config.dictConfig(config)
    queue_handler = logging.getHandlerByName("queue_handler")
    if queue_handler is not None:
        queue_handler.listener.start()  # type: ignore[reportAttributeAccessIssue]
        atexit.register(queue_handler.listener.stop)  # type: ignore[reportAttributeAccessIssue]


async def main():
    setup_logging()
    logger = logging.getLogger(Client.name)
    logger.info("Logger Initialized!")
    async with httpx.AsyncClient(timeout=httpx.Timeout(None)) as session:
        client = MrRobot(
            intents=disnake.Intents.all(),
            session=session,
            db=await aiosqlite.connect(Client.db_name),
            db_name=Client.db_name,
        )
        if client.git:
            logger.info("Pulling DB")
            await client.git.pull(Client.db_name)
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
        finally:
            if not client.is_closed():
                await client.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
