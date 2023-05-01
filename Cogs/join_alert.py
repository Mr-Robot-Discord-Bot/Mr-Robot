import os

from disnake.ext import commands

from utils import Embeds, db, send_webhook


class Joinalert(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """Webhook get's triggered on joining any guild"""

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

        data = {"$set": {"guild_id": guild.id, "guild_name": guild.name}}
        db.config.update_one({"guild_id": guild.id}, data, upsert=True)
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
        db.config.delete_one({"guild_id": guild.id})
        db.traffic.delete_one({"guild_id": guild.id})
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
