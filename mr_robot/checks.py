from typing import Callable

import disnake
from disnake.ext import commands


def ensure_voice_connect() -> Callable:
    def predicate(interaction: disnake.GuildCommandInteraction) -> bool:
        if not interaction.author.voice:
            raise commands.CommandError("You aren't connected to voice channel")
        return True

    return commands.check(predicate)  # type: ignore[reportArgumentType]


def ensure_voice_player() -> Callable:
    def predicate(interaction: disnake.GuildCommandInteraction) -> bool:
        if not interaction.author.voice:
            raise commands.CommandError("You aren't connected to voice channel.")
        elif not interaction.author.voice.channel:
            raise commands.CommandError("You aren't connected to voice channel.")
        elif not interaction.guild.voice_client:
            raise commands.CommandError("Player isn't connected to any voice channel.")
        elif (
            interaction.guild.voice_client.channel.id
            != interaction.author.voice.channel.id
        ):
            raise commands.CommandError("You must be in the same voice channel.")
        return True

    return commands.check(predicate)  # type: ignore[reportArgumentType]
