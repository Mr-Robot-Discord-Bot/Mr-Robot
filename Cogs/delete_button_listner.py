import logging

import disnake
from disnake.ext import commands

logger = logging.getLogger(__name__)


class DeleteButtonListner(commands.Cog):
    def __init__(self, client):
        self.bot = client
        logger.info("DeleteButtonListner Cog Loaded")

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


def setup(client: commands.Bot):
    client.add_cog(DeleteButtonListner(client))
