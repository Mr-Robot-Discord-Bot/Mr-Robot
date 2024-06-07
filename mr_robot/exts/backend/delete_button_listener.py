import logging

import disnake
from disnake.ext import commands

from mr_robot.bot import MrRobot
from mr_robot.constants import ButtonCustomId

logger = logging.getLogger(__name__)


class DeleteButtonListener(commands.Cog, slash_command_attrs={"dm_permission": False}):
    """Handles Delete Button"""

    def __init__(self, client: MrRobot) -> None:
        self.bot = client

    # button schema
    # PREFIX:PERMS:USER_ID:MESSAGE_ID
    @commands.Cog.listener("on_button_click")
    async def handle_delete_button(
        self, interaction: disnake.MessageInteraction
    ) -> None:
        """Deletes a message if a user is authorized"""
        if not interaction.component.custom_id:
            return
        if not interaction.component.custom_id.startswith(ButtonCustomId.delete):
            return

        logger.debug(
            f"{self.__class__.__name__} recv: {interaction.component.custom_id}"
        )

        custom_id = interaction.component.custom_id.removeprefix(ButtonCustomId.delete)

        perms, user_id, *msg_id = custom_id.split(":")

        delete_msg = None
        if msg_id:
            if msg_id[0]:
                delete_msg = int(msg_id[0])

        perms, user_id = int(perms), int(user_id)

        if not (is_orignal_author := interaction.author.id == user_id):
            permissions = disnake.Permissions(perms)
            user_permissions = interaction.permissions
            if not permissions.value & user_permissions.value:
                await interaction.response.send_message(
                    "Sorry, this delete button is not for you!",
                    ephemeral=True,
                    delete_after=5,
                )
                return

        if isinstance(
            interaction.channel,
            (disnake.TextChannel, disnake.Thread, disnake.VoiceChannel),
        ) and isinstance(interaction.me, disnake.Member):
            if (
                not hasattr(interaction.channel, "guild")
                or not (
                    myperms := interaction.channel.permissions_for(interaction.me)
                ).read_messages
            ):

                await interaction.response.defer()
                await interaction.delete_original_message()
                return

            await interaction.message.delete()

            if not delete_msg or not myperms.manage_messages or not is_orignal_author:
                return

            if msg := interaction.bot.get_message(delete_msg):
                if msg.edited_at:
                    return
            else:
                msg = interaction.channel.get_partial_message(delete_msg)

            try:
                await msg.delete()
            except disnake.NotFound:
                ...
            except disnake.Forbidden:
                logger.warning("Cache is unreliable or something is weird")
        else:
            logger.debug(f"Interaction's channel don't have required type.")

    # @commands.Cog.listener()
    # async def on_button_click(self, interaction: disnake.MessageInteraction):
    #     if interaction.component.custom_id == "delete":
    #         await interaction.response.defer()
    #         if interaction.message.interaction:
    #             if interaction.message.interaction.author.id == interaction.author.id:
    #                 await interaction.delete_original_message()
    #             else:
    #                 await interaction.send(
    #                     ":octagonal_sign: This delete button is not for you :octagonal_sign:",
    #                     ephemeral=True,
    #                 )


def setup(client: MrRobot):
    client.add_cog(DeleteButtonListener(client))
