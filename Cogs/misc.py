from typing import Union

import disnake
from disnake.ext import commands

from utils import DeleteButton, Embeds


class Misc(commands.Cog):
    def __init__(self, client):
        self.bot = client

    @commands.slash_command(name="embed")
    async def slash_embed(
        self,
        interaction,
        title,
        message,
        color: Union[disnake.Colour, None] = None,
        image=None,
    ):
        """
        Creates Embeds

        Parameters
        ----------
        title : Title of the embed
        message : Message of the embed
        color : Color of the embed
        image: Sets image of the embed
        """
        await interaction.send(
            embed=Embeds.emb(color, title, message.replace(";", "\n")).set_image(image)
        )

    @commands.slash_command(name="userinfo", dm_permission=False)
    async def slash_userinfo(
        self, interaction, member: Union[disnake.Member, None] = None
    ):
        """
        Shows user info

        Parameters
        ----------
        member : Member to show info
        """
        if member is None:
            member = interaction.author
        embed = Embeds.emb(member.color, f"{member} Information")
        try:
            embed.set_thumbnail(url=member.display_avatar.url)
        except Exception:
            embed.set_thumbnail(
                url="https://cdn.logojoy.com/wp-content/uploads/"
                "20210422095037/discord-mascot.png"
            )
        embed.add_field(name="Name", value=member.name, inline=False)
        embed.add_field(name="Nickname", value=member.nick, inline=False)
        embed.add_field(name="ID", value=member.id, inline=False)
        embed.add_field(
            name="Account Created",
            value=member.created_at.strftime("%a %#d %B %Y, %I:%M %p UTC"),
            inline=False,
        )
        embed.add_field(
            name="Joined",
            value=member.joined_at.strftime("%a %#d %B %Y, %I:%M %p UTC"),
            inline=False,
        )
        members = sorted(interaction.guild.members, key=lambda m: m.joined_at)
        embed.add_field(
            name="Join Position", value=str(members.index(member) + 1), inline=False
        )
        embed.add_field(name="Status", value=member.status, inline=False)
        embed.add_field(name="Activity: ", value=member.activity, inline=False)
        embed.add_field(
            name="Roles" if len(member.roles) > 1 else "Role",
            value=", ".join([role.mention for role in member.roles]),
            inline=False,
        )
        await interaction.send(
            embed=embed, view=DeleteButton(author=interaction.author)
        )


def setup(client: commands.Bot):
    client.add_cog(Misc(client))
