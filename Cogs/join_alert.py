import logging
import os

import disnake
from disnake.ext import commands

from utils import Embeds, send_webhook

logger = logging.getLogger(__name__)


class Joinalert(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        logger.info("Joinalert Cog Loaded")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """Webhook get's triggered on joining any guild"""

        await self.bot.change_presence(
            activity=disnake.Streaming(
                name=f"In {len(self.bot.guilds)} Servers",
                url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            )
        )

        embed = Embeds.emb(
            Embeds.green,
            guild.name,
            f"""
                Guild Id: {guild.id}
                Owner Id: {guild.owner_id}
                Vanity Invite Link: {guild.vanity_url_code}
                Members Count: {guild.member_count}
                """,
        )

        await self.bot.db.execute(
            "insert into guilds values (?, ?)", (guild.id, guild.name)
        )
        await self.bot.db.commit()
        await send_webhook(
            embed=embed,
            webhook_url=os.getenv("whtraffic"),
            username="Guild Join Logger",
            avatar_url="https://cdn.discordapp.com/avatars"
            "/1087375480304451727/f780c7c8c052c66c89f9270"
            "aebd63bc2.png?size=1024",
        )

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        if not guild.members:
            return

        await self.bot.change_presence(
            activity=disnake.Streaming(
                name=f"In {len(self.bot.guilds)} Servers",
                url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            )
        )

        embed = Embeds.emb(
            Embeds.red,
            guild.name,
            f"""
                Guild Id: {guild.id}
                Owner Id: {guild.owner_id}
                Vanity Invite Link: {guild.vanity_url_code}
                Members Count: {guild.member_count}
                """,
        )
        tables = await (
            await self.bot.db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        ).fetchall()
        for (table,) in tables:
            await self.bot.db.execute(
                f"delete from {table} where guild_id = ?", (guild.id,)
            )
        await self.bot.db.commit()
        await send_webhook(
            embed=embed,
            webhook_url=os.getenv("whtraffic"),
            username="Guild Leave Logger",
            avatar_url="https://cdn.discordapp.com/avatars/10"
            "87375480304451727/f780c7c8c052c66c89f9270aebd63b"
            "c2.png?size=1024",
        )


def setup(client: commands.Bot):
    client.add_cog(Joinalert(client))
