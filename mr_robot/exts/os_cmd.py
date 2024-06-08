import asyncio
import io
import logging
import os
from pathlib import Path

import disnake
from disnake.abc import PrivateChannel
from disnake.ext import commands, tasks

from mr_robot.bot import MrRobot
from mr_robot.constants import Client
from mr_robot.utils.git_api import NothingToUpdate
from mr_robot.utils.helpers import Embeds
from mr_robot.utils.messages import DeleteButton

REPO_PATH = Client.github_bot_repo.split("/")[-2]
logger = logging.getLogger(__name__)


class Oscmd(commands.Cog):
    def __init__(self, bot: MrRobot):
        self.bot = bot
        self.first_task = True
        self.pull_push_db.start()

    @commands.is_owner()
    @commands.slash_command(name="owner", guild_ids=Client.debug_guilds)
    async def owner(self, _):
        """Bot Owner Commands"""
        ...

    @tasks.loop(hours=1)
    async def pull_push_db(self):
        if not self.bot.git:
            logger.warning(
                "Db info related env vars are not set, Hence db won't update"
            )
            return
        elif self.first_task:
            self.first_task = False
            logger.debug("Skipping Db Push")
            return
        logger.debug(f"Pushing DB to {Client.github_db_repo}")
        try:
            await self.bot.git.push(
                file=Path(self.bot.db_name), commit_msg="chore: auto update"
            )
        except NothingToUpdate:
            logger.debug("Nothing to update")

    @owner.sub_command(name="backup", description="Backup the database")
    async def backup(self, interaction: disnake.GuildCommandInteraction):
        try:
            await self.pull_push_db()
            await interaction.send(
                embed=Embeds.emb(Embeds.green, "Backup Completed"),
                components=[DeleteButton(interaction.author)],
            )
        except Exception as error:
            raise commands.CommandError(str(error))

    @owner.sub_command(name="cmd", description="Runs Console Commands")
    async def cmd(self, interaction, command_string):
        out = await asyncio.subprocess.create_subprocess_shell(
            command_string, stdout=asyncio.subprocess.PIPE
        )
        if not out.stdout:
            raise FileNotFoundError
        await interaction.send(
            file=disnake.File(io.BytesIO(await out.stdout.read()), filename="cmd.txt"),
            components=[DeleteButton(interaction.author)],
        )

    @owner.sub_command(name="update", description="Updates the code from gihub")
    async def update(self, interaction):
        await self.bot.change_presence(
            status=disnake.Status.dnd, activity=disnake.Game(name="Update")
        )
        await interaction.send(
            components=[DeleteButton(interaction.author)],
            embed=Embeds.emb(Embeds.green, "Updating..."),
        )
        os.system(f"git clone {Client.github_bot_repo}")
        for i in os.listdir():
            if i != REPO_PATH or i != ".env" or i != "Logs" or not i.endswith(".db"):
                os.system(f"rm -rf {i}")
        os.system(f"mv {REPO_PATH}/* .")
        os.system(f"rm -rf {REPO_PATH}")
        await interaction.send(
            components=[DeleteButton(interaction.author)],
            embed=Embeds.emb(Embeds.green, "Update Completed"),
        )
        os.system("python bot.py")

    @owner.sub_command(name="invite_link")
    async def link(
        self, interaction: disnake.CommandInteraction, id, expire=0, number_of_uses=1
    ):
        """
        Generate invite link for a server

        Parameters
        ----------
        id : Server ID
        expire : Time in seconds for which invite link will be valid
        number_of_uses : Number of times invite link can be used
        """
        server = self.bot.get_guild(int(id))
        channel = server.text_channels[0] if server else None
        logger.info(f"{channel=} {id=}")
        if (
            not channel
            or isinstance(channel, disnake.Thread)
            or isinstance(channel, PrivateChannel)
        ):
            await interaction.send("No Server Found with this id", ephemeral=True)
            return
        link = await channel.create_invite(
            temporary=True, max_age=int(expire), max_uses=int(number_of_uses)
        )
        await interaction.send(link.url, components=[DeleteButton(interaction.author)])

    @link.autocomplete("id")
    async def link_autocomplete(self, inter: disnake.GuildCommandInteraction, inp: str):
        inp = inp.lower()
        matching_dict = {}
        for guild in self.bot.guilds:
            if inp in guild.name:
                matching_dict[guild.name[:25]] = str(guild.id)

        sorted_dict = dict(
            sorted(matching_dict.items(), key=lambda x: x[0].index(inp))[:25]
        )
        return sorted_dict

    @owner.sub_command(name="shutdown", description="Shutdown myself")
    async def reboot(self, interaction):
        await interaction.send(
            embed=Embeds.emb(Embeds.red, "Shutting down"),
            components=[DeleteButton(interaction.author)],
        )
        await self.bot.change_presence(
            status=disnake.Status.dnd, activity=disnake.Game(name="Shutting down")
        )
        exit()


def setup(client: MrRobot):
    client.add_cog(Oscmd(client))
