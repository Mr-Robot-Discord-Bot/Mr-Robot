import logging

import disnake
import googletrans as gt
from disnake.ext import commands
from googletrans import Translator

from mr_robot.bot import MrRobot
from mr_robot.utils.helpers import Embeds
from mr_robot.utils.messages import DeleteButton


async def autocomp_langs(_: disnake.CommandInteraction, user_input: str):
    if user_input == "":
        return [lang for lang in list(gt.LANGUAGES.values())[:20]]
    else:
        return [lang for lang in gt.LANGUAGES.values() if user_input.lower() in lang]


logger = logging.getLogger(__name__)


class Translate(commands.Cog):
    def __init__(self, client: MrRobot):
        self.bot = client

    @commands.slash_command(name="translate", dm_permission=False)
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
        translation = translator.translate(message, dest=language)
        await interaction.send(
            components=[DeleteButton(interaction.author)],
            embed=Embeds.emb(
                Embeds.yellow,
                f"Translation {gt.LANGUAGES[translation.src]} to {language}",
                translation.text,
            ),
        )


def setup(client: MrRobot):
    client.add_cog(Translate(client))
