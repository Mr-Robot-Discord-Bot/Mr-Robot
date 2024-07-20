import logging
from typing import Literal

import disnake
import psutil
import sqlalchemy
from disnake.ext import commands

from mr_robot.bot import MrRobot
from mr_robot.constants import Client
from mr_robot.database import Greeter, Guild
from mr_robot.utils.helpers import Embeds
from mr_robot.utils.messages import DeleteButton

logger = logging.getLogger(__name__)


class Status(commands.Cog):
    def __init__(self, client: MrRobot):
        self.bot = client

    @commands.Cog.listener()
    async def on_ready(self):

        async with self.bot.db.begin() as session:

            # Merge Guilds
            for guild in self.bot.guilds:
                await session.merge(Guild(id=guild.id, name=guild.name))
                logger.debug("Merged Guild: %s", guild)

            # Retrieve Guilds
            existing_guilds = await session.scalars(sqlalchemy.select(Guild))
            existing_guilds = existing_guilds.all()
            logger.debug(f"{existing_guilds=}")
            await session.commit()

        # Db clean up
        bot_guildids = {guild.id for guild in self.bot.guilds}
        async with self.bot.db.begin() as session:
            for guild in existing_guilds:
                if guild.id not in bot_guildids:
                    logger.debug(f"Removed {Guild(id=guild.id, name=guild.name)}.")
                    sql_query = sqlalchemy.delete(Guild).where(Guild.id == guild.id)
                    await session.execute(sql_query)
                    await session.commit()

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
            async with self.bot.db.begin() as session:
                sql_query = sqlalchemy.select(Greeter).where(
                    Greeter.guild_id == interaction.guild.id
                )
                result = await session.scalars(sql_query)
                result = result.one_or_none()
            if getattr(result, feature, None) is None:
                return ":x:"
            else:
                return ":white_check_mark:"

        embed = Embeds.emb(Embeds.green, "Status")
        embed.add_field(
            "Shards ",
            f"`{self.bot.shard_count}`",
        )
        embed.add_field(
            "Latency ",
            f"`{int(self.bot.latency * 1000)}ms`",
        )
        embed.add_field(
            "Uptime ",
            disnake.utils.format_dt(self.bot.start_time, style="R"),
        )
        embed.add_field(
            "Cpu Usage ",
            f"`{psutil.cpu_percent()}%`",
        )
        embed.add_field(
            "Memory Usage ",
            f"`{psutil.virtual_memory().percent}%`",
        )
        embed.add_field(
            "Available Usage ",
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
            "Members ",
            f"`{interaction.guild.member_count}`",
        )
        embed.add_field(
            "Channels ",
            f"`{len(interaction.guild.channels)}`",
        )
        embed.add_field(
            "Welcomer ",
            await get_greeter_status("wlcm_channel"),
        )
        embed.add_field(
            "Goodbyer ",
            await get_greeter_status("bye_channel"),
        )
        if self.bot.owner_id == interaction.author.id and Client.debug_mode:
            embed.add_field(
                "Extensions loaded",
                f"```{'\n'.join(self.bot.extensions)}```",
                inline=False,
            )
        await interaction.send(
            embed=embed, components=[DeleteButton(interaction.author)]
        )


def setup(client: MrRobot):
    client.add_cog(Status(client))
