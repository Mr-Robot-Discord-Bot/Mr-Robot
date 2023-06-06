import logging
import os
import subprocess

import disnake
from disnake.ext import commands

from utils import Embeds, delete_button

REPO_PATH = "mr-robot"
REPO_URL = "https://github.com/mr-robot-discord-bot/mr-robot.git"
logger = logging.getLogger(__name__)


class Oscmd(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        logger.info("Oscmd Cog Loaded")

    @commands.is_owner()
    @commands.slash_command(name="owner", guild_ids=[1088928716572344471])
    async def owner(self, interaction):
        """Bot Owner Commands"""
        ...

    @owner.sub_command(name="db", description="Runs SQL Query")
    async def db(self, interaction, query):
        try:
            await self.bot.db.execute(query)
            await self.bot.db.commit()
            await interaction.send(
                embed=Embeds.emb(Embeds.green, "Query Executed"),
                components=[delete_button],
            )
        except Exception as e:
            await interaction.send(
                embed=Embeds.emb(Embeds.red, "Error", f"```{e}```"),
                components=[delete_button],
            )

    @owner.sub_command(name="cmd", description="Runs Console Commands")
    async def cmd(self, interaction, command_string):
        output = subprocess.getoutput(command_string)
        await interaction.send(
            embed=Embeds.emb(
                Embeds.green, "Shell Console", f"```\n{output[:1900]}\n```"
            ),
            components=[delete_button],
        )

    @owner.sub_command(name="update", description="Updates the code from gihub")
    async def update(self, interaction):
        await self.bot.change_presence(
            status=disnake.Status.dnd, activity=disnake.Game(name="Update")
        )
        await interaction.send(
            components=[delete_button],
            embed=Embeds.emb(Embeds.green, "Updating..."),
        )
        os.system(f"git clone {REPO_URL}")
        for i in os.listdir():
            if i != REPO_PATH or i != ".env" or i != "Logs" or not i.endswith(".db"):
                os.system(f"rm -rf {i}")
        os.system(f"mv {REPO_PATH}/* .")
        os.system(f"rm -rf {REPO_PATH}")
        await interaction.send(
            components=[delete_button],
            embed=Embeds.emb(Embeds.green, "Update Completed"),
        )
        os.system("python bot.py")

    @owner.sub_command(name="link")
    async def link(self, interaction, id, expire=0, number_of_uses=1):
        """
        Generate invite link for a server

        Parameters
        ----------
        id : Server ID
        expire : Time in seconds for which invite link will be valid
        number_of_uses : Number of times invite link can be used
        """
        server = self.bot.get_channel(int(id))
        link = await server.create_invite(
            temporary=True, max_age=int(expire), max_uses=int(number_of_uses)
        )
        await interaction.send(link, components=[delete_button])

    @owner.sub_command(name="shutdown", description="Shutdown myself")
    async def reboot(self, interaction):
        await interaction.send(
            embed=Embeds.emb(Embeds.red, "Shutting down"), components=[delete_button]
        )
        await self.bot.change_presence(
            status=disnake.Status.dnd, activity=disnake.Game(name="Shutting down")
        )
        exit()


def setup(client: commands.Bot):
    client.add_cog(Oscmd(client))
