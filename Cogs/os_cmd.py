import asyncio
import io
import logging
import os
from pathlib import Path

import disnake
from disnake.ext import commands, tasks

from git_api import Git
from utils import Embeds, delete_button

REPO_URL = "https://github.com/mr-robot-discord-bot/mr-robot.git"
REPO_PATH = REPO_URL.split("/")[-1].split(".")[0]
logger = logging.getLogger(__name__)


class Oscmd(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        logger.info("Oscmd Cog Loaded")
        self.first_task = True
        self.token = os.getenv("db_token")
        self.repo = os.getenv("db_repo")
        if not self.token or not self.repo:
            logger.warning("DB_REPO or DB_TOKEN not set, Hence db won't update")
            return
        owner, repo = self.repo.split("/")
        self.git = Git(
            token=self.token,
            owner=owner,
            repo=repo,
            username="Mr Robot",
            email="mr_robot@mr_robot_discord_bot.com",
            client=self.bot.session,
        )

    @commands.is_owner()
    @commands.slash_command(name="owner", guild_ids=[1088928716572344471])
    async def owner(self, interaction):
        """Bot Owner Commands"""
        ...

    @tasks.loop(hours=1)
    async def pull_push_db(self):
        if not self.token or not self.repo:
            logger.warning(
                "Db info related env vars are not set, Hence db won't update"
            )
            return
        elif self.first_task:
            self.first_task = False
            logger.debug("Skipping Db Push")
            return
        logger.debug("Pushing DB")
        await self.git.pull(path="mr-robot.db")
        await self.git.push(file=Path("./mr-robot.db"), commit_msg="chore: auto update")

    @owner.sub_command(name="backup", description="Backup the database")
    async def backup(self, interaction: disnake.GuildCommandInteraction):
        try:
            await self.pull_push_db()
            await interaction.send(
                embed=Embeds.emb(Embeds.green, "Backup Completed"),
                components=[delete_button],
            )
        except Exception as error:
            raise commands.CommandError(str(error))

    @owner.sub_command(name="cmd", description="Runs Console Commands")
    async def cmd(self, interaction, command_string):
        out = await asyncio.subprocess.create_subprocess_shell(
            command_string, stdout=asyncio.subprocess.PIPE
        )
        await interaction.send(
            file=disnake.File(
                io.BytesIO(await out.stdout.read()), filename="cmd.txt"
            ),  # type: ignore
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
