import logging
import time

import disnake
from disnake.ext import commands

from mr_robot.bot import MrRobot

logger = logging.getLogger(__name__)


class CommandInvokationManager(commands.Cog):
    """Patches application command invokation"""

    def __init__(self, client: MrRobot) -> None:
        self.bot = client

    @commands.Cog.listener(disnake.Event.slash_command)
    async def handler_command(
        self, interaction: disnake.ApplicationCommandInteraction
    ) -> None:
        """Event listener for slash command invocation"""
        start = time.perf_counter()
        await self.bot.wait_for(
            disnake.Event.slash_command_completion,
            check=lambda inter: interaction.application_command.name
            == inter.application_command.name,
        )
        elapsed_time = time.perf_counter() - start
        logger.debug(f"{interaction.application_command.name} took {elapsed_time:.4f}s")


def setup(client: MrRobot) -> None:
    client.add_cog(CommandInvokationManager(client))
