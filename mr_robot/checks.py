from typing import Callable

import disnake
from disnake.ext import commands


def ensure_voice_connect() -> Callable:
    def predicate(interaction: disnake.GuildCommandInteraction) -> bool:
        if interaction.author.voice is None or interaction.author.voice.channel is None:
            raise commands.CommandError("You aren't connected to voice channel")
        elif (
            interaction.guild.voice_client is not None
            and interaction.author.voice.channel.id
            != interaction.guild.voice_client.channel.id
        ):
            raise commands.CommandError("You must be in the same voice channel.")
        return True

    return commands.check(predicate)  # type: ignore[reportArgumentType]


def ensure_voice_player() -> Callable:
    def predicate(interaction: disnake.GuildCommandInteraction) -> bool:
        if interaction.author.voice is None or interaction.author.voice.channel is None:
            raise commands.CommandError("You aren't connected to voice channel.")
        elif interaction.guild.voice_client is None:
            raise commands.CommandError("Player isn't connected to any voice channel.")
        elif (
            interaction.guild.voice_client.channel.id
            != interaction.author.voice.channel.id
        ):
            raise commands.CommandError("You must be in the same voice channel.")
        return True

    return commands.check(predicate)  # type: ignore[reportArgumentType]
