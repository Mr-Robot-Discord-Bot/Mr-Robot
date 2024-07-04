from typing import List

import disnake


class Paginator(disnake.ui.View):
    def __init__(self, embeds: List[disnake.Embed]) -> None:
        super().__init__(timeout=60 * 10)
        self.embeds = embeds
        self.index = 0
        self._update()

        # Index all embeds
        for idx, embed in enumerate(self.embeds):
            embed.set_footer(text=f"Page {idx + 1} of {len(self.embeds)}")

    def _update(self) -> None:
        """Updates state of buttons disabled or not"""
        self.first_page.disabled = self.prev_page.disabled = self.index == 0
        self.last_page.disabled = self.next_page.disabled = (
            self.index == len(self.embeds) - 1
        )

    @disnake.ui.button(emoji="⏪", style=disnake.ButtonStyle.blurple)
    async def first_page(self, _, interaction: disnake.MessageInteraction) -> None:
        """Goes to first embed"""
        self.index = 0
        self._update()

        await interaction.response.edit_message(
            embed=self.embeds[self.index], view=self
        )

    @disnake.ui.button(emoji="◀", style=disnake.ButtonStyle.secondary)
    async def prev_page(self, _, interaction: disnake.MessageInteraction) -> None:
        """Goes to previous embed"""
        self.index -= 1
        self._update()

        await interaction.response.edit_message(
            embed=self.embeds[self.index], view=self
        )

    @disnake.ui.button(emoji="🗑️", style=disnake.ButtonStyle.red)
    async def remove(self, _, interaction: disnake.MessageInteraction):
        """Delete Button"""
        await interaction.response.defer()
        await interaction.delete_original_response()

    @disnake.ui.button(emoji="▶", style=disnake.ButtonStyle.secondary)
    async def next_page(self, _, interaction: disnake.MessageInteraction) -> None:
        """Goes to next embed"""
        self.index += 1
        self._update()

        await interaction.response.edit_message(
            embed=self.embeds[self.index], view=self
        )

    @disnake.ui.button(emoji="⏩", style=disnake.ButtonStyle.blurple)
    async def last_page(self, _, interaction: disnake.MessageInteraction) -> None:
        """Goes to last embed"""
        self.index = len(self.embeds) - 1
        self._update()

        await interaction.response.edit_message(
            embed=self.embeds[self.index], view=self
        )
