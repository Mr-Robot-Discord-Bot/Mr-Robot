import asyncio
import logging.config
import logging.handlers
import signal
import sys
from pathlib import Path

import disnake
import httpx
from sqlalchemy import event
from sqlalchemy.engine import Engine

import mr_robot.log
from mr_robot.bot import MrRobot
from mr_robot.constants import Client, Database


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, _):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


async def main():
    mr_robot.log.setup_logging()
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
