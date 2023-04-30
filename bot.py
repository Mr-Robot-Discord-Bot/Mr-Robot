import os
import sys
import time

import disnake
import mafic
from disnake.ext import commands
from dotenv import load_dotenv

from utils import proxy_generator

PROXY = proxy_generator()
with open("proxy_mode.conf", "r", encoding="utf-8") as file:
    data = file.read()
if data != "on":
    PROXY = None
start_time = time.time()


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
                pass


client = MrRobot(proxy=PROXY, intents=disnake.Intents.all())
load_dotenv()


unloaded_cog_list = []
loaded_cog_list = []


try:
    for file in os.listdir("Cogs"):
        if file.endswith(".py"):
            try:
                client.load_extension(f"Cogs.{str(file[:-3])}")
                loaded_cog_list.append(file[:-3])
            except Exception as e:
                unloaded_cog_list.append(file[:-3])
                raise e

except Exception as error:
    raise error


try:
    client.loop.run_until_complete(client.start(os.getenv("Mr_Robot")))
except disnake.errors.LoginFailure or disnake.errors.HTTPException:
    print(" [!] Unable to connect to Discord")
    with open("proxy_mode.conf", "w", encoding="utf-8") as file:
        data = file.write("on")
    sys.exit()
finally:
    client.loop.close()
