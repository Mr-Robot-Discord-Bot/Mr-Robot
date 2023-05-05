import asyncio
import os
import time

import aiohttp
import disnake
import mafic
from disnake.ext import commands
from dotenv import load_dotenv

from utils import SESSION_CTX, proxy_generator

proxy_mode = False
PROXY = None


class MrRobot(commands.InteractionBot):
    """Mr Robot Bot"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.pool = mafic.NodePool(self)  # type: ignore
        self.loop.create_task(self.add_nodes())
        self.start_time = time.time()

    async def add_nodes(self):
        """Adds Nodes to the pool"""
        while True:
            try:
                await self.wait_until_ready()
                await self.pool.create_node(
                    host="localhost",
                    port=2333,
                    label="MAIN",
                    password="youshallnotpass",
                )
                break
            except Exception:
                print("[!] Unable to connect to Lavalink")
                time.sleep(5)

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
    client = MrRobot(proxy=PROXY, intents=disnake.Intents.all())
    async with aiohttp.ClientSession() as session:
        SESSION_CTX.set(session)
        client.load_extensions()
        try:
            await client.start(os.getenv("Mr_Robot"))  # type: ignore
        except (disnake.errors.LoginFailure, disnake.errors.HTTPException):
            print(" [!] Unable to connect to Discord falling back to proxy mode")
            proxy_mode = True
            PROXY = proxy_generator() if proxy_mode else None
        finally:
            await client.close()


if __name__ == "__main__":
    asyncio.run(main())
