import logging

import disnake
from disnake.ext import commands

from mr_robot.bot import MrRobot

logger = logging.getLogger(__name__)


class DeleteButtonListner(commands.Cog):
    def __init__(self, client: MrRobot):
        self.bot = client

    @commands.Cog.listener()
    async def on_button_click(self, interaction: disnake.MessageInteraction):
        if interaction.component.custom_id == "delete":
            await interaction.response.defer()
            if interaction.message.interaction:
                if interaction.message.interaction.author.id == interaction.author.id:
                    await interaction.delete_original_message()
                else:
                    await interaction.send(
                        ":octagonal_sign: This delete button is not for you :octagonal_sign:",
                        ephemeral=True,
                    )


def setup(client: MrRobot):
    client.add_cog(DeleteButtonListner(client))
