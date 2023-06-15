import logging
import os
import subprocess

import disnake
from disnake.ext import commands, tasks

from utils import Embeds, delete_button

REPO_URL = "https://github.com/mr-robot-discord-bot/mr-robot.git"
REPO_PATH = REPO_URL.split("/")[-1].split(".")[0]
DB_REPO = os.getenv("db_repo")
logger = logging.getLogger(__name__)


class Oscmd(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        logger.info("Oscmd Cog Loaded")

    @commands.Cog.listener()
    async def on_ready(self):
        subprocess.run("chmod 600 .ssh/id_rsa", shell=True)
        subprocess.run(
            "git config --global user.email 'mr-robot@gmail.com'", shell=True
        )
        subprocess.run("git config --global user.name 'Mr Robot'", shell=True)
        self.push_db.start()

    @commands.is_owner()
    @commands.slash_command(name="owner", guild_ids=[1088928716572344471])
    async def owner(self, interaction):
        """Bot Owner Commands"""
        ...

    @tasks.loop(hours=24)
    async def push_db(self):
        if not DB_REPO:
            logger.warning("DB_REPO not set, Hence db won't update")
            return
        elif not os.path.exists(".ssh/id_rsa.pub"):
            logger.warning("SSH key not found, Hence db won't update")
            return
        logger.info("Pushing DB")
        try:
            file = DB_REPO.split("/")[-1].split(".")[0] if DB_REPO else None
            subprocess.run(f"rm -rf {file}; git clone {DB_REPO}", shell=True)
            subprocess.run(f"cp mr-robot.db {file}", shell=True)
            subprocess.run(f"cd {file} && git add .", shell=True)
            subprocess.run(f"cd {file} && git commit -m 'Auto Commit'", shell=True)
            subprocess.run(f"cd {file} && git push", shell=True)
        except Exception as error:
            logger.exception(error, exc_info=True)

    @owner.sub_command(name="backup", description="Backup the database")
    async def backup(self, interaction: disnake.GuildCommandInteraction):
        try:
            await self.push_db()
            await interaction.send(
                embed=Embeds.emb(Embeds.green, "Backup Completed"),
                components=[delete_button],
            )
        except Exception as error:
            raise commands.CommandError(str(error))

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
