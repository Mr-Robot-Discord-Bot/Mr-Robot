import asyncio
import atexit
import json
import logging.config
import logging.handlers
import os
import signal
import sys

import disnake
import httpx
from dotenv import load_dotenv
from sqlalchemy import event
from sqlalchemy.engine import Engine

from mr_robot.bot import MrRobot
from mr_robot.constants import Client, Database

load_dotenv()


def setup_logging_modern() -> None:
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


def setup_logging() -> None:
    os.makedirs("logs", exist_ok=True)
    file_handler = logging.handlers.RotatingFileHandler(
        Client.log_file_name, mode="a", maxBytes=(1000000 * 20), backupCount=5
    )
    console_handler = logging.StreamHandler()

    file_handler.setLevel(logging.DEBUG)
    console_handler.setLevel(logging.INFO)
    logging.basicConfig(
        level=logging.DEBUG,
        format="[%(levelname)s|%(module)s|%(funcName)s|L%(lineno)d] %(asctime)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
        handlers=[console_handler, file_handler],
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("mafic").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("disnake").setLevel(logging.INFO)
    logging.getLogger("streamlink").disabled = True


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, _):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


async def main():
    setup_logging()
    logger = logging.getLogger(Client.name)
    logger.info("Logger Initialized!")
    async with httpx.AsyncClient(timeout=httpx.Timeout(None)) as session:
        client = MrRobot(
            intents=disnake.Intents.all(),
            http_session=session,
        )
        await client.init_db()
        if client.git:
            logger.info("Pulling DB")
            try:
                await client.git.pull(Database.db_name)
            except httpx.HTTPStatusError:
                logger.warning(f"Failed to pull {Database.db_name} from github.")
            except (httpx.ConnectError, httpx.ConnectTimeout):
                logger.error("Failed to connect with github", exc_info=True)
                await client.close()

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
            logger.warning("Closing Client")
            if not client.is_closed():
                await client.close()
            exit()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
