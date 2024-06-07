import logging
from typing import cast

import disnake
import mafic
from disnake.ext import commands

from mr_robot.bot import MrRobot
from mr_robot.constants import Colors
from mr_robot.utils.helpers import Embeds
from mr_robot.utils.messages import DeleteButton

logger = logging.getLogger(__name__)


class Music(commands.Cog):
    def __init__(self, bot: MrRobot):
        self.bot = bot

    @commands.slash_command(name="music", dm_permission=False)
    async def music(self, _):
        """Music Commands"""
        ...

    async def ensure_voice(self, interaction: disnake.GuildCommandInteraction) -> None:
        """Ensures voice client"""
        player = cast(mafic.Player, interaction.guild.voice_client)
        if player is interaction.guild.voice_client:
            logger.debug("Initializing voice client!")
            if interaction.author.voice and interaction.author.voice.channel:
                await interaction.author.voice.channel.connect(cls=mafic.Player)

            else:
                raise commands.CommandError("User isn't connected to a voice channel.")
        elif player.current is not None:
            await player.stop()

    @music.sub_command(name="play")
    async def slash_play(
        self, interaction: disnake.GuildCommandInteraction, search: str
    ) -> None:
        """
        Plays music

        Parameters
        ----------
        search: Search for music
        """

        await self.ensure_voice(interaction)

        await interaction.response.defer()

        tracks = None
        player = cast(mafic.Player, interaction.guild.voice_client)

        while True:
            try:
                tracks = await player.fetch_tracks(search)
                break
            except mafic.TrackLoadException as e:
                logger.error("Fails to load track!", exc_info=e)
                continue

        if not tracks:
            embed = Embeds.emb(
                Embeds.blue,
                "No Tracks Found",
                "Please Try Searching Something else.",
            )
            return await interaction.send(embed=embed, ephemeral=True)

        if isinstance(tracks, mafic.Playlist):
            track = tracks.tracks[0]
        else:
            track = tracks[0]

        await player.play(track)
        embed = Embeds.emb(
            Embeds.blue,
            "Now Playing",
            f"Name: [{track.title}]({track.uri})\n"
            f"Author: {track.author}\n"
            f"Source: {str(track.source).capitalize()}\n"
            f"Requested by: {interaction.author.mention}",
        )

        await interaction.send(
            embed=embed, components=[DeleteButton(interaction.author)]
        )

    @music.sub_command(name="disconnect")
    async def slash_stop(self, interaction: disnake.GuildCommandInteraction) -> None:
        """Disconnects the bot from voice channel"""

        player = cast(mafic.Player, interaction.guild.voice_client)
        embed = Embeds.emb(Embeds.blue, "Music Player Disconnected")
        if interaction.guild.voice_client is not None:
            if interaction.guild.voice_client is None:
                embed = disnake.Embed(color=Colors.blue, title="Unactive Music Player")
            else:
                await player.stop()
                await player.disconnect()

        await interaction.send(embed=embed, ephemeral=True, delete_after=5)


def setup(client: MrRobot):
    client.add_cog(Music(client))
