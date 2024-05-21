from typing import Optional

import disnake

from mr_robot.constants import ButtonCustomId


class DeleteButton(disnake.ui.Button):
    """A button to delete messages"""

    def __init__(
        self,
        user: int | disnake.User | disnake.Member,
        *,
        allow_manage_message: bool = True,
        initial_message: Optional[disnake.Message | int] = None,
        style: Optional[disnake.ButtonStyle] = None,
        emoji: Optional[str | disnake.Emoji | disnake.PartialEmoji] = None,
    ) -> None:
        if isinstance(user, int):
            user_id = user
        else:
            user_id = user.id
        super().__init__()
        self.custom_id = ButtonCustomId.delete
        permissions = disnake.Permissions()
        if allow_manage_message:
            permissions.manage_messages = True
        self.custom_id += f"{permissions.value}:{user_id}:"

        if initial_message:
            if isinstance(initial_message, disnake.Message):
                initial_message = initial_message.id
            self.custom_id += str(initial_message)

        if not style:
            if initial_message:
                self.style = disnake.ButtonStyle.danger
            else:
                self.style = disnake.ButtonStyle.secondary
        else:
            self.style = style

        if not emoji:
            if self.style == disnake.ButtonStyle.danger:
                self.emoji = ":bomb:"
            else:
                self.emoji = ":wastebasket:"
        else:
            self.emoji = emoji
