import os

import openai
from disnake.ext import commands

from utils import DeleteButton, Embeds

openai.api_key = os.getenv("openai_api_key")


class Ai(commands.Cog):
    def __init__(self, client):
        self.bot = client

    @commands.slash_command(name="ai")
    async def ai(self, interaction):
        """Interact with openai"""
        ...

    @ai.sub_command(name="chat")
    async def slash_ai_generate_text(self, interaction, query: str):
        """
        Talk to Mr Robot AI system

        Parameters
        ----------
        query : Query to ask Mr Robot
        """
        prompt = f"""
        User: How are you?
        Mr_Robot: I'm running on great specs, Sir!
        User: What is your name?
        Mr_Robot: My name is MR Robot.
        User: Who created you?
        Mr_Robot: I am created by Known Black Hat, Sir!
        User: {query}
        Mr_Robot: """

        try:
            completion = await openai.Completion.acreate(
                engine="text-davinci-002",
                prompt=prompt,
                temperature=0.5,
                max_tokens=500,
                n=1,
                stop=None,
            )
            await interaction.send(
                view=DeleteButton(),
                embed=Embeds.emb(
                    Embeds.green, "AI System", completion.choices[0].text.strip()
                ),
            )
        except Exception:
            await interaction.send(
                view=DeleteButton(),
                embed=Embeds.emb(
                    Embeds.red,
                    "Api Limit Reached",
                    """
                    Attention Discord users,

                    We need your help! The free tier usage for our Mr. Robot Discord bot's AI feature has been exhausted, and we require the purchase of a premium API to continue offering this feature. We kindly ask for your support through donations in cryptocurrency, with a minimum donation of $1 and a maximum of $10.

                    Your contributions, no matter how small, will help us achieve our goals and continue providing you with an innovative and exciting way to interact with each other through the Mr. Robot Discord bot. Donations can be made to the following cryptocurrency address:

                    `42XSJzfAXTjT5Vt5uatbH41SZRepyU2AJdWLVeGNkeZ3bbjUnyyL9X2Qq16BjzHLhkKYvWWcs3f3eKmuUbnJpjPeFm23v4v`

                    Thank you for your support and generosity.

                    Sincerely,

                    Known Black Hat
                                                    """,
                ),
            )

    @ai.sub_command(name="img")
    async def slash_ai_generate_img(self, interaction, prompt: str):
        """
        Generates Images using AI

        Parameters
        ----------
        prompt : Prompt to generate image
        """
        await interaction.response.defer()
        try:
            response = await openai.Image.acreate(prompt=prompt, n=1, size="512x512")
            await interaction.send(response["data"][0]["url"], view=DeleteButton())
        except Exception:
            await interaction.send(
                view=DeleteButton(),
                embed=Embeds.emb(
                    Embeds.red,
                    "Api Limit Reached",
                    """
                                                    Attention Discord users,

                                                    We need your help! The free tier usage for our Mr. Robot Discord bot's AI feature has been exhausted, and we require the purchase of a premium API to continue offering this feature. We kindly ask for your support through donations in cryptocurrency, with a minimum donation of $1 and a maximum of $10.

                                                    Your contributions, no matter how small, will help us achieve our goals and continue providing you with an innovative and exciting way to interact with each other through the Mr. Robot Discord bot. Donations can be made to the following cryptocurrency address:

                                                    `42XSJzfAXTjT5Vt5uatbH41SZRepyU2AJdWLVeGNkeZ3bbjUnyyL9X2Qq16BjzHLhkKYvWWcs3f3eKmuUbnJpjPeFm23v4v`

                                                    Thank you for your support and generosity.

                                                    Sincerely,

                                                    Known Black Hat
                                                    """,
                ),
            )


def setup(client: commands.Bot):
    client.add_cog(Ai(client))
