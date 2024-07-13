import asyncio
import atexit
import json
import logging.config
import logging.handlers
import signal
import sys
from pathlib import Path

import coloredlogs
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
    logging.config.dictConfig(config)
    queue_handler = logging.getHandlerByName("queue_handler")
    if queue_handler is not None:
        queue_handler.listener.start()  # type: ignore[reportAttributeAccessIssue]
        atexit.register(queue_handler.listener.stop)  # type: ignore[reportAttributeAccessIssue]


def setup_logging() -> None:
    root_logger = logging.getLogger()

    log_file = Path(Client.log_file_name)
    log_file.parent.mkdir(exist_ok=True)

    formatter = "[ %(levelname)s | %(name)s | %(module)s | L%(lineno)d ] %(asctime)s: %(message)s"
    file_formatter = logging.Formatter(
        "[ %(levelname)s | %(name)s | %(module)s | %(funcName)s | %(filename)s | L%(lineno)d ] %(asctime)s: %(message)s"
    )

    file_handler = logging.handlers.RotatingFileHandler(
        log_file, mode="a", maxBytes=(1000000 * 20), backupCount=5
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    # console_handler = logging.StreamHandler()
    # console_handler.setFormatter(formatter)
    # root_logger.addHandler(console_handler)

    file_handler.setLevel(logging.DEBUG)
    # console_handler.setLevel(logging.INFO)

    coloredlogs.install(
        level=logging.DEBUG, stream=sys.stdout, logger=root_logger, fmt=formatter
    )

    root_logger.setLevel(logging.DEBUG)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("mafic").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("disnake").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("core").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine.Engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.orm").setLevel(logging.WARNING)
    logging.getLogger("aiosqlite").setLevel(logging.WARNING)
    logging.getLogger("streamlink").disabled = True

    root_logger.info("Logger Initialized!")


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, _):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


async def main():
    setup_logging()
    logger = logging.getLogger(Client.name)
    async with httpx.AsyncClient(timeout=httpx.Timeout(None)) as session:
        client = MrRobot(
            intents=disnake.Intents.all(),
            http_session=session,
        )
        await client.init_db()
        if client.git:
            try:
                if not Path(Database.db_name).exists():
                    logger.info("Pulling DB")
                    client.db_exsists = False
                    await client.git.pull(Database.db_name)
                else:
                    logger.info("Db file found!")
                    client.db_exsists = True
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
