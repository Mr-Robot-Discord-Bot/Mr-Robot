import logging

import disnake
from disnake.ext import commands

logger = logging.getLogger(__name__)


class DeleteButtonListner(commands.Cog):
    def __init__(self, client):
        self.bot = client
        logger.debug("DeleteButtonListner Cog Loaded")

    @commands.Cog.listener()
    async def on_button_click(self, interaction: disnake.MessageInteraction):
        await interaction.response.defer()
        if not interaction.message.interaction:
            if interaction.author.guild_permissions.manage_messages:  # type: ignore
                await interaction.delete_original_message()
            else:
                await interaction.send(
                    ":cry: This button is not for you", ephemeral=True
                )
        else:
            if interaction.message.interaction.author.id == interaction.author.id:
                await interaction.delete_original_message()
            else:
                await interaction.send(
                    ":cry: This button is not for you", ephemeral=True
                )


def setup(client: commands.Bot):
    client.add_cog(DeleteButtonListner(client))
