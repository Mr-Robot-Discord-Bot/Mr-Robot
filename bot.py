import os
import time

import disnake
import mafic
from disnake.ext import commands
from dotenv import load_dotenv

from utils import proxy_generator

proxy_mode = False
start_time = time.time()
PROXY = None


class MrRobot(commands.InteractionBot):
    """Mr Robot Bot"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.start_time = time.time()

        self.pool = mafic.NodePool(self)
        self.loop.create_task(self.add_nodes())

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


if __name__ == "__main__":
    while True:
        client = MrRobot(proxy=PROXY, intents=disnake.Intents.all())
        client.load_extensions()
        try:
            client.loop.run_until_complete(client.start(os.getenv("Mr_Robot")))
        except (disnake.errors.LoginFailure, disnake.errors.HTTPException):
            print(" [!] Unable to connect to Discord falling back to proxy mode")
            proxy_mode = True
            PROXY = proxy_generator() if proxy_mode else None
        finally:
            client.loop.close()
