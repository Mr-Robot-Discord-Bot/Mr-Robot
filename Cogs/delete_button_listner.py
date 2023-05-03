import disnake
from disnake.ext import commands

from utils import Embeds


class DeleteButtonListner(commands.Cog):
    def __init__(self, client):
        self.bot = client

    @commands.Cog.listener()
    async def on_button_click(self, interaction: disnake.MessageInteraction):
        await interaction.response.defer()
        try:
            if interaction.author.id == interaction.message.interaction.author.id:
                await interaction.delete_original_message()
            else:
                await interaction.send(
                    embed=Embeds.emb(
                        Embeds.red, ":cry: This button is not for you :cry:"
                    ),
                    ephemeral=True,
                )
        except AttributeError:
            if interaction.author.guild_permissions.manage_messages:
                await interaction.delete_original_message()
            else:
                await interaction.send(
                    embed=Embeds.emb(
                        Embeds.red, ":cry: This button is not for you :cry:"
                    ),
                    ephemeral=True,
                )


def setup(client: commands.Bot):
    client.add_cog(DeleteButtonListner(client))
