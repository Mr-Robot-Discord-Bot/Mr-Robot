import logging
import random
from typing import cast

import disnake
import mafic
from aiosqlite import IntegrityError
from disnake.abc import Connectable
from disnake.ext import commands
from mafic.track import Track

from mr_robot.bot import MrRobot
from mr_robot.checks import ensure_voice_connect, ensure_voice_player
from mr_robot.constants import Colors
from mr_robot.utils.helpers import Embeds
from mr_robot.utils.messages import DeleteButton

logger = logging.getLogger(__name__)

SQL_CREATE_PLAYLISTS_TABLE = """
create table if not exists playlists (
        id integer primary key autoincrement,
        name text,
        user bigint,
        last_accessed timestamp default current_timestamp,
        unique(user, name)
        )
"""
SQL_CREATE_TRACKS_TABLE = """
create table if not exists tracks (
        id integer,
        track text,
        foreign key (id) references playlists (id)
        )
"""


class MyPlayer(mafic.Player[MrRobot]):
    def __init__(self, client: MrRobot, channel: Connectable) -> None:
        super().__init__(client, channel)

        self.queue: list[Track] = []


class Music(commands.Cog):
    def __init__(self, bot: MrRobot):
        self.bot = bot
        self.max_playlist_limit = 5

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        await self.bot.db.execute(SQL_CREATE_PLAYLISTS_TABLE)
        await self.bot.db.commit()
        await self.bot.db.execute(SQL_CREATE_TRACKS_TABLE)
        await self.bot.db.commit()

    async def connect(self, interaction: disnake.GuildCommandInteraction) -> None:
        """Connects to voice channel"""
        if not hasattr(interaction.guild, "voice_client"):
            raise commands.CommandError(
                "Seems like i don't have enough perms to play music!"
            )
        elif interaction.guild.voice_client is None:
            logger.debug(f"Initializing voice client in {interaction.guild.name}.")
            if interaction.author.voice and interaction.author.voice.channel:
                await interaction.author.voice.channel.connect(cls=MyPlayer)  # type: ignore[reportArgumentType]

    @commands.slash_command(name="music", dm_permission=False)
    async def music(self, _):
        """Music Commands"""
        ...

    async def search_play(
        self,
        interaction: disnake.GuildCommandInteraction,
        search: str,
    ) -> Track:
        player = cast(MyPlayer, interaction.guild.voice_client)

        while True:
            try:
                tracks = await player.fetch_tracks(search)
                break
            except mafic.TrackLoadException as e:
                logger.error("Fails to load track!", exc_info=e)
                continue

        if not tracks:
            raise commands.CommandError("No track found, try searching something else.")

        if isinstance(tracks, mafic.Playlist):
            tracks = tracks.tracks
            if len(tracks) > 1:
                player.queue.extend(tracks[1:])
        return tracks[0]

    async def playlist_play(
        self, interaction: disnake.GuildCommandInteraction, playlist_name: str
    ) -> Track:
        playlists = await self.bot.db.execute(
            "select id from playlists where name = ? and user = ?",
            (playlist_name, interaction.author.id),
        )
        playlists = await playlists.fetchone()
        if playlists is None:
            raise commands.CommandError("No such playlist found!")
        tracks = await self.bot.db.execute(
            "select track from tracks where id = ?", (playlists[0],)
        )
        if not (tracks := set(await tracks.fetchall())):
            raise commands.CommandError("No tracks found in the playlist!")
        player = cast(MyPlayer, interaction.guild.voice_client)
        tracks = [await player.node.decode_track(track[0]) for track in tracks]

        if len(tracks) > 1:
            player.queue.extend(tracks[1:])
        return tracks[0]

    @music.sub_command(name="play")
    @ensure_voice_connect()
    async def slash_play(
        self,
        interaction: disnake.GuildCommandInteraction,
        search: str | None = None,
        playlist_name: str | None = None,
    ) -> None:
        """
        Plays music

        Parameters
        ----------
        search: Search for music
        playlist_name: Playlist name
        """
        if not search and not playlist_name:
            raise commands.CommandError(
                "You need to provide either `search` argument or your `playlist_name` !"
            )
        elif search and playlist_name:
            raise commands.CommandError("You can only provide one argument at a time.")

        await interaction.response.defer()

        await self.connect(interaction)

        player = cast(MyPlayer, interaction.guild.voice_client)
        player.queue.clear()

        if search:
            track = await self.search_play(interaction, search)
            embed = Embeds.emb(
                Colors.blue,
                "Now Playing",
                f"Name: [{track.title}]({track.uri})\n"
                f"Author: {track.author}\n"
                f"Platform: {str(track.source).capitalize()}\n"
                f"Played by: {interaction.author.mention}",
            )
            embed.set_image(track.artwork_url)

        elif playlist_name:
            track = await self.playlist_play(interaction, playlist_name)
            embed = Embeds.emb(Colors.blue, "Now Playing", f"Playlist: {playlist_name}")

        else:
            raise commands.CommandError("idk how this reached!")

        await player.play(track)

        await interaction.send(
            embed=embed, components=[DeleteButton(interaction.author)]
        )

    @music.sub_command(name="boost")
    @ensure_voice_player()
    async def boost(self, interaction: disnake.GuildCommandInteraction) -> None:
        """Boost the player"""
        player = cast(MyPlayer, interaction.guild.voice_client)
        bassboost_equalizer = mafic.Equalizer(
            [mafic.EQBand(idx, 0.30) for idx in range(15)]
        )

        bassboost_filter = mafic.Filter(equalizer=bassboost_equalizer)
        await player.add_filter(bassboost_filter, label="boost")

        embed = Embeds.emb(Colors.blue, "Player Boosted")
        await interaction.send(
            embed=embed, components=[DeleteButton(interaction.author)]
        )

    @music.sub_command(name="unboost")
    @ensure_voice_player()
    async def unboost(self, interaction: disnake.GuildCommandInteraction) -> None:
        """Unboost the player"""
        player = cast(MyPlayer, interaction.guild.voice_client)
        await player.remove_filter("boost")
        embed = Embeds.emb(Colors.blue, "Player Unboosted")
        await interaction.send(
            embed=embed, components=[DeleteButton(interaction.author)]
        )

    @music.sub_command(name="current")
    @ensure_voice_player()
    async def current(self, interaction: disnake.GuildCommandInteraction) -> None:
        """Show current playing track"""
        player = cast(MyPlayer, interaction.guild.voice_client)
        if player.current is None:
            embed = Embeds.emb(Colors.blue, "No Track Playing")
        else:
            track = player.current
            embed = Embeds.emb(
                Colors.blue,
                "Now Playing",
                f"Name: [{track.title}]({track.uri})\n"
                f"Author: {track.author}\n"
                f"Platform: {str(track.source).capitalize()}\n"
                f"Played by: {interaction.author.mention}",
            )
            embed.set_image(track.artwork_url)
        await interaction.send(
            embed=embed, components=[DeleteButton(interaction.author)]
        )

    @commands.Cog.listener()
    async def on_track_end(self, event: mafic.TrackEndEvent[MyPlayer]) -> None:
        if event.player.queue:
            if event.reason == mafic.EndReason.REPLACED:
                return
            track = event.player.queue.pop(0)
            await event.player.play(track)

    @music.sub_command(name="skip")
    @ensure_voice_player()
    async def skip(self, interaction: disnake.GuildCommandInteraction) -> None:
        """Skips the current track"""
        player = cast(MyPlayer, interaction.guild.voice_client)
        await player.stop()
        embed = Embeds.emb(Colors.blue, "Track Skipped")
        await interaction.send(
            embed=embed, components=[DeleteButton(interaction.author)]
        )

    @music.sub_command_group(name="queue")
    @ensure_voice_player()
    async def queue(self, _) -> None:
        """Queue subcommand group"""

    @queue.sub_command(name="clear")
    async def clear_queue(self, interaction: disnake.GuildCommandInteraction) -> None:
        """Clears music queue"""
        player = cast(MyPlayer, interaction.guild.voice_client)
        player.queue = []
        embed = Embeds.emb(Colors.blue, "Queue Cleared")
        await interaction.send(
            embed=embed, components=[DeleteButton(interaction.author)]
        )

    @queue.sub_command(name="list")
    async def list_queue(self, interaction: disnake.GuildCommandInteraction) -> None:
        """List first 20 tracks in queue"""
        player = cast(MyPlayer, interaction.guild.voice_client)
        if not player.queue:
            embed = Embeds.emb(Colors.blue, "Queue Empty")
        else:
            tracks = "\n".join(
                [
                    f"{idx+1}) [{track.title}]({track.uri})"
                    for idx, track in enumerate(player.queue[:20])
                ]
            )
            embed = Embeds.emb(Colors.blue, "Queue", tracks)
        await interaction.send(
            embed=embed, components=[DeleteButton(interaction.author)]
        )

    @queue.sub_command(name="remove")
    async def remove_queue(
        self, interaction: disnake.GuildCommandInteraction, index: int
    ) -> None:
        """Remove a track from queue"""
        player = cast(MyPlayer, interaction.guild.voice_client)
        if not player.queue:
            embed = Embeds.emb(Colors.blue, "Queue Empty")
        else:
            try:
                track = player.queue.pop(index - 1)
            except IndexError:
                raise commands.CommandError("Invalid index!")
            embed = Embeds.emb(
                Colors.blue,
                "Track Removed",
                f"Track [{track.title}] removed from queue",
            )
        await interaction.send(
            embed=embed, components=[DeleteButton(interaction.author)]
        )

    @queue.sub_command(name="shuffle")
    async def shuffle_queue(self, interaction: disnake.GuildCommandInteraction) -> None:
        """Shuffle the queue"""
        player = cast(MyPlayer, interaction.guild.voice_client)
        if not player.queue:
            embed = Embeds.emb(Colors.blue, "Queue Empty")
        else:
            random.shuffle(player.queue)
            embed = Embeds.emb(Colors.blue, "Queue Shuffled")
        await interaction.send(
            embed=embed, components=[DeleteButton(interaction.author)]
        )

    @queue.sub_command(name="add")
    async def add_queue(
        self, interaction: disnake.GuildCommandInteraction, search: str
    ) -> None:
        """Add a track to queue"""
        player = cast(MyPlayer, interaction.guild.voice_client)
        tracks = await player.fetch_tracks(search)
        if isinstance(tracks, mafic.Playlist):
            tracks = tracks.tracks
        elif tracks is None:
            raise commands.CommandError("No track found!")
        track = tracks[0]
        player.queue.append(track)
        embed = Embeds.emb(
            Colors.blue,
            "Track Added",
            f"Track [{track.title}]({track.uri}) added to queue",
        )
        embed.set_image(track.artwork_url)
        await interaction.send(
            embed=embed, components=[DeleteButton(interaction.author)]
        )

    @music.sub_command(name="disconnect")
    @ensure_voice_player()
    async def slash_stop(self, interaction: disnake.GuildCommandInteraction) -> None:
        """Disconnects the bot from voice channel"""

        player = cast(MyPlayer, interaction.guild.voice_client)
        embed = Embeds.emb(Embeds.blue, "Music Player Disconnected")
        if interaction.guild.voice_client is not None:
            if interaction.guild.voice_client is None:
                embed = Embeds.emb(Colors.blue, "Unactive Music Player")
            else:
                await player.stop()
                await player.disconnect()

        await interaction.send(embed=embed, ephemeral=True, delete_after=5)

    @music.sub_command(name="volume")
    @ensure_voice_player()
    async def slash_volume(
        self,
        interaction: disnake.GuildCommandInteraction,
        volume: commands.Range[int, 0, 100],
    ) -> None:
        """
        Set player's volume level

        Parameters
        ----------
        volume : Volume level
        """
        player = cast(MyPlayer, interaction.guild.voice_client)
        await player.set_volume(volume)
        embed = Embeds.emb(Colors.blue, f"Volume: {volume}%")
        await interaction.send(
            embed=embed, components=[DeleteButton(interaction.author)]
        )

    @music.sub_command(name="toggle_pause")
    @ensure_voice_player()
    async def slash_pause(
        self,
        interaction: disnake.GuildCommandInteraction,
        force_pause: bool | None = None,
    ) -> None:
        """
        Pause/Resume the player

        Parameters
        ----------
        force_pause : Force pause the player
        """
        player = cast(MyPlayer, interaction.guild.voice_client)
        if force_pause or not player.paused:
            await player.pause()
        else:
            await player.resume()
        embed = Embeds.emb(
            Colors.blue, "Player Paused" if player.paused else "Player Resumed"
        )
        await interaction.send(
            embed=embed, components=[DeleteButton(interaction.author)]
        )

    @music.sub_command_group(name="playlist")
    @ensure_voice_player()
    async def playlist(self, _) -> None:
        """Playlist subcommand group"""

    @playlist.sub_command(name="create")
    async def create(
        self, interaction: disnake.GuildCommandInteraction, name: str
    ) -> None:
        """
        Create a playlist

        Parameters
        ----------
        name : Name of the playlist
        """

        count = await self.bot.db.execute(
            "select count(*) from playlists where user = ?", (interaction.author.id,)
        )
        count = await count.fetchone()

        if count is None:
            raise commands.CommandError("Failed to fetch playlist count")

        if count[0] >= self.max_playlist_limit:
            embed = Embeds.emb(
                Colors.red,
                "Playlist Limit Exceeded",
                f"Max limit is {self.max_playlist_limit} !\n"
                " Please delete some playlists to create new ones.",
            )
            await interaction.send(
                embed=embed, components=[DeleteButton(interaction.author)]
            )
            return
        try:
            await self.bot.db.execute(
                "insert into playlists (name, user) values (?, ?)",
                (name, interaction.author.id),
            )
            await self.bot.db.commit()
        except IntegrityError:
            embed = Embeds.emb(
                Colors.red, "Playlist Exists", f"Playlist `{name}` already exists!"
            )
            await interaction.send(
                embed=embed, components=[DeleteButton(interaction.author)]
            )
            return

        embed = Embeds.emb(
            Colors.blue, "Playlist Created", f"Playlist `{name}` created successfully!"
        )
        await interaction.send(
            embed=embed, components=[DeleteButton(interaction.author)]
        )

    @playlist.sub_command(name="delete")
    async def delete(
        self, interaction: disnake.GuildCommandInteraction, name: str
    ) -> None:
        """
        Delete a playlist

        Parameters
        ----------
        name : Name of the playlist
        """
        playlist_id = await self.bot.db.execute(
            "select id from playlists where name = ? and user = ?",
            (name, interaction.author.id),
        )
        playlist_id = await playlist_id.fetchone()
        await self.bot.db.execute(
            "delete from playlists where name = ? and user = ?",
            (name, interaction.author.id),
        )
        if playlist_id is not None:
            await self.bot.db.execute(
                "delete from tracks where id = ?",
                (playlist_id[0],),
            )
        await self.bot.db.commit()
        embed = Embeds.emb(
            Colors.blue, "Playlist Deleted", f"Playlist `{name}` deleted successfully!"
        )
        await interaction.send(
            embed=embed, components=[DeleteButton(interaction.author)]
        )

    @playlist.sub_command(name="list")
    async def list(self, interaction: disnake.GuildCommandInteraction) -> None:
        """List all playlists"""
        playlists = await self.bot.db.execute(
            "select name from playlists where user = ?", (interaction.author.id,)
        )
        playlists = await playlists.fetchall()

        if not playlists:
            embed = Embeds.emb(
                Colors.blue, "No Playlists", "You don't have any playlists!"
            )
            await interaction.send(
                embed=embed, components=[DeleteButton(interaction.author)]
            )
            return

        embed = Embeds.emb(
            Colors.blue,
            "Playlists",
            f'```{"\n".join([f"{idx}) {playlist[0]}" for idx, playlist in enumerate(playlists, start=1)])}```',
        )
        await interaction.send(
            embed=embed, components=[DeleteButton(interaction.author)]
        )

    @playlist.sub_command(name="add_track")
    async def add_track(
        self,
        interaction: disnake.GuildCommandInteraction,
        playlist: str,
        track: str,
    ) -> None:
        """
        Add a track to playlist

        Parameters
        ----------
        playlist : Name of the playlist
        track : Track to add
        """
        await interaction.response.defer()
        player = cast(MyPlayer, interaction.guild.voice_client)
        tracks = await player.fetch_tracks(track)
        if isinstance(tracks, mafic.Playlist):
            tracks = tracks.tracks
        elif tracks is None:
            raise commands.CommandError("No track found!")
        trackk = tracks[0]
        playlist_id = await self.bot.db.execute(
            "select id from playlists where name = ? and user = ?",
            (playlist, interaction.author.id),
        )
        playlist_id = await playlist_id.fetchone()
        if playlist_id is None:
            raise commands.CommandError("No such playlist found!")

        await self.bot.db.execute(
            "insert into tracks (id, track) values (?, ?)",
            (playlist_id[0], trackk.id),
        )
        await self.bot.db.commit()
        embed = Embeds.emb(
            Colors.blue,
            "Track Added",
            f"Track [{trackk.title}]({trackk.uri}) added to playlist `{playlist}`",
        )
        embed.set_image(trackk.artwork_url)
        await interaction.send(
            embed=embed, components=[DeleteButton(interaction.author)]
        )

    @slash_play.autocomplete("playlist_name")
    @add_track.autocomplete("playlist")
    async def playlist_autocomp(self, interaction: disnake.GuildCommandInteraction, _):
        playlists = await self.bot.db.execute(
            "select name from playlists where user = ?", (interaction.author.id,)
        )
        playlists = await playlists.fetchall()
        playlists = {x[0] for x in playlists}
        return playlists


def setup(client: MrRobot):
    client.add_cog(Music(client))
