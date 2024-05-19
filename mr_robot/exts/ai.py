import logging

import google.generativeai as genai
from disnake.ext import commands
from google.generativeai.types import BlockedPromptException

from mr_robot.bot import MrRobot
from mr_robot.constants import Client
from mr_robot.utils.helpers import delete_button

logger = logging.getLogger(__name__)

genai.configure(api_key=Client.gemini_api_key)

generation_config = {
    "temperature": 1,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 2048,
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
]


class Ai(commands.Cog):
    def __init__(self, client: MrRobot):
        self.bot = client
        self.model = genai.GenerativeModel(
            model_name="gemini-1.0-pro",
            generation_config=generation_config,  # type: ignore[reportArgumentType]
            safety_settings=safety_settings,
        )
        self.conv = self.model.start_chat(
            history=[
                {"role": "user", "parts": ["How are you?"]},
                {"role": "model", "parts": ["I'm running on great specs, Sir!"]},
                {"role": "user", "parts": ["What is your name?"]},
                {"role": "model", "parts": ["My name is MR Robot."]},
                {"role": "user", "parts": ["Who created you?"]},
                {"role": "model", "parts": ["I am created by Known Black Hat, Sir!"]},
            ]
        )

    @commands.slash_command(name="ai", dm_permission=False)
    async def ai(self, _):
        """Interact with ai"""
        ...

    @ai.sub_command(name="chat")
    async def slash_ai_generate_text(self, interaction, query: str):
        """
        Talk to Mr Robot AI system

        Parameters
        ----------
        query : Query to ask Mr Robot
        """
        await interaction.response.defer()
        try:
            await self.conv.send_message_async(query)
            if self.conv.last:
                await interaction.send(self.conv.last.text, components=[delete_button])
            else:
                await interaction.send("Ai module didn't responded")
        except BlockedPromptException:
            await interaction.send(
                "This request can't be fulfiled as its against my tos!"
            )


def setup(client: MrRobot):
    client.add_cog(Ai(client))
