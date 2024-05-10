import logging

import mafic
from disnake.ext import commands
from utils import Embeds, delete_button

from mr_robot.bot import MrRobot

logger = logging.getLogger(__name__)


class Music(commands.Cog):
    def __init__(self, bot: MrRobot):
        self.bot = bot
        logger.info("Music Cog Loaded")

    @commands.slash_command(name="music", dm_permission=False)
    async def music(self, interaction):
        """Music Commands"""
        ...

    @music.sub_command(name="play")
    async def slash_play(self, interaction, search: str) -> None:
        """
        Plays music

        Parameters
        ----------
        search: Search for music
        """

        if interaction.guild.voice_client is None:
            if interaction.author.voice:
                await interaction.response.defer()
                await interaction.author.voice.channel.connect(cls=mafic.Player)

            else:
                embed = Embeds.emb(
                    Embeds.red,
                    "Your aren't connected to voice Channel",
                    "Connect to voice channel",
                )
                await interaction.send(embed=embed, ephemeral=True)
        if not interaction.guild.voice_client:
            player = await interaction.user.voice.channel.connect(cls=mafic.Player)
        else:
            player = interaction.guild.voice_client

        tracks = None
        while True:
            try:
                tracks = await player.fetch_tracks(search)
                break
            except mafic.TrackLoadException:
                continue

        if not tracks:
            embed = Embeds.emb(
                Embeds.red,
                "No Tracks Found",
                "Please Try Searching Something else.",
            )
            return await interaction.send(embed=embed, ephemeral=True)

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

        await interaction.send(embed=embed, components=[delete_button])

    @music.sub_command(name="disconnect")
    async def slash_stop(self, interaction) -> None:
        """Disconnects the bot from voice channel"""
        embed = Embeds.emb(Embeds.red, "Voice Channel Disconnected")
        await interaction.send(embed=embed, ephemeral=True)
        if interaction.guild.voice_client is not None:
            await interaction.guild.voice_client.stop()
            await interaction.guild.voice_client.disconnect()


def setup(client: MrRobot):
    client.add_cog(Music(client))
