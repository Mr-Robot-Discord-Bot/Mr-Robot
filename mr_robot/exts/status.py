import logging
import os
from typing import Literal

import disnake
import psutil
from disnake.ext import commands

from mr_robot.__main__ import PROXY
from mr_robot.bot import MrRobot
from mr_robot.utils.helpers import Embeds, delete_button

logger = logging.getLogger(__name__)


class Status(commands.Cog):
    def __init__(self, client):
        self.bot = client
        logger.info("Status Cog Loaded")

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.db.execute(
            "CREATE TABLE IF NOT EXISTS guilds (guild_id bigint primary key, name text)"
        )
        if PROXY:
            logger.info("Using Proxy: %s", PROXY)
        os.system("echo '' > Servers.inf")
        exsisting_guilds = await (
            await self.bot.db.execute("select guild_id, name from guilds")
        ).fetchall()
        logger.debug(exsisting_guilds)
        for guild in self.bot.guilds:
            with open("Servers.inf", "a+") as stats:
                stats.write(
                    f"\n\n [+] {guild.name} --> {', '.join([ f'{channel.name} [{channel.id}]' for channel in guild.channels])} \n"
                )
            if guild.id not in {guild[0] for guild in exsisting_guilds}:
                logger.info("Adding Guild: %s", guild)
                await self.bot.db.execute(
                    "INSERT INTO guilds (guild_id, name) VALUES (?, ?)",
                    (guild.id, guild.name),
                )
            else:
                logger.info("Updating Guild: %s", guild)
                await self.bot.db.execute(
                    "update guilds set name = ? where guild_id = ?",
                    (guild.name, guild.id),
                )

        for guild in exsisting_guilds:
            if guild[0] not in {guild.id for guild in self.bot.guilds}:
                logger.info("Removing Guild: %s", guild[1])
                tables = await (
                    await self.bot.db.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    )
                ).fetchall()
                for (table,) in tables:
                    await self.bot.db.execute(
                        f"delete from {table} where guild_id = ?", (guild[0],)
                    )
                await self.bot.db.commit()

        await self.bot.db.commit()
        with open("proxy_mode.conf", "r") as file:
            proxy_mode = file.read()
        if proxy_mode == "on":
            await self.bot.change_presence(
                status=disnake.Status.idle,
                activity=disnake.Game(name="In Starvation Mode"),
            )
        await self.bot.change_presence(
            activity=disnake.Streaming(
                name=f"In {len(self.bot.guilds)} Servers",
                url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            )
        )

    @commands.slash_command(name="status", dm_permission=False)
    async def slash_status(self, interaction):
        """Shows status of the bot"""

        async def get_greeter_status(feature: Literal["wlcm_channel", "bye_channel"]):
            result = await (
                await self.bot.db.execute(
                    f"""
                    select {feature} from greeter
                    where guild_id = ?
                    """,
                    (interaction.guild.id,),
                )
            ).fetchone()
            if result and result != (None,):
                return ":white_check_mark:"
            else:
                return ":x:"

        embed = Embeds.emb(Embeds.green, "Status")
        embed.add_field(
            "Shards: ",
            f"`{self.bot.shard_count}`",
        )
        embed.add_field(
            "Latency: ",
            f"`{int(self.bot.latency * 1000)}ms`",
        )
        embed.add_field(
            "Uptime: ",
            disnake.utils.format_dt(self.bot.start_time, style="R"),
        )
        embed.add_field(
            "Cpu Usage: ",
            f"`{psutil.cpu_percent()}%`",
        )
        embed.add_field(
            "Memory Usage: ",
            f"`{psutil.virtual_memory().percent}%`",
        )
        embed.add_field(
            "Available Usage: ",
            f"""`{
                str(
                    round(
                        psutil.virtual_memory().available
                        * 100
                        / psutil.virtual_memory().total
                    )
                )
                + "%"
                }`""",
        )
        embed.add_field(
            "Members: ",
            f"`{interaction.guild.member_count}`",
        )
        embed.add_field(
            "Channels: ",
            f"`{len(interaction.guild.channels)}`",
        )
        embed.add_field(
            "Welcomer: ",
            await get_greeter_status("wlcm_channel"),
        )
        embed.add_field(
            "Goodbyer: ",
            await get_greeter_status("bye_channel"),
        )
        await interaction.send(embed=embed, components=[delete_button])


def setup(client: MrRobot):
    client.add_cog(Status(client))
