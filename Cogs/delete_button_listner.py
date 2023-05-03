import disnake
from disnake.ext import commands

from utils import Embeds


class DeleteButtonListner(commands.Cog):
    def __init__(self, client):
        self.bot = client

    @commands.Cog.listener()
    async def on_button_click(self, interaction: disnake.MessageInteraction):
        await interaction.response.defer()
        if interaction.author.id == interaction.message.interaction.author.id:
            await interaction.delete_original_message()
        else:
            await interaction.send(embed=Embeds.emb(":cry: This button is not for you"))


def setup(client: commands.Bot):
    client.add_cog(DeleteButtonListner(client))
