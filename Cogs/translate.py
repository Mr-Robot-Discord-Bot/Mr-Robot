import disnake
import googletrans as gt
from disnake.ext import commands
from googletrans import Translator

from utils import DeleteButton, Embeds


class Translate(commands.Cog):
    def __init__(self, client):
        self.bot = client

    async def autocomp_langs(inter: disnake.Interaction, user_input: str):
        if user_input == "":
            return [lang for lang in list(gt.LANGUAGES.values())[:20]]
        else:
            return [
                lang for lang in gt.LANGUAGES.values() if user_input.lower() in lang
            ]

    @commands.slash_command(name="translate")
    async def slash_translate(
        self,
        interaction,
        message,
        language: str = commands.Param(autocomplete=autocomp_langs),
    ):
        """
        Translate a message to a language using google translate

        Parameters
        ----------
        message : Message to translate
        language : Language to translate to
        """
        translator = Translator()
        try:
            translation = translator.translate(message, dest=language)
            await interaction.send(
                view=DeleteButton(author=interaction.author),
                embed=Embeds.emb(
                    Embeds.orange,
                    f"Translation {gt.LANGUAGES[translation.src]} to {language}",
                    translation.text,
                ),
            )
        except Exception as e:
            if "invalid destination language" in str(e):
                await interaction.send(
                    embed=Embeds.emb(
                        Embeds.orange,
                        "Destination Translation Language List (DTLL) :",
                        str(gt.LANGUAGES).replace(",", "\n"),
                    )
                )


def setup(client: commands.Bot):
    client.add_cog(Translate(client))
