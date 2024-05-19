import logging
from datetime import datetime
from typing import Set, Union

import disnake
from disnake.ext import commands

from mr_robot.bot import MrRobot
from mr_robot.utils.helpers import Embeds, delete_button

logger = logging.getLogger(__name__)


class EmbedModal(disnake.ui.Modal):
    def __init__(self, color):
        self.color = color
        components = [
            disnake.ui.TextInput(
                label="Image url",
                placeholder="Enter image here",
                custom_id="image",
                style=disnake.TextInputStyle.short,
                required=False,
            ),
            disnake.ui.TextInput(
                label="Title",
                placeholder="Enter title here",
                custom_id="title",
                style=disnake.TextInputStyle.short,
            ),
            disnake.ui.TextInput(
                label="Description",
                placeholder="Suggestion: Use <@User_Id> for mention & <#Channel_Id> for tagging the channel!",
                custom_id="body",
                style=disnake.TextInputStyle.paragraph,
            ),
        ]
        super().__init__(
            title="Embed Generator", custom_id="embed_generator", components=components
        )

    async def callback(self, interaction: disnake.ModalInteraction):
        if not interaction.guild:
            return
        title = interaction.text_values["title"]
        content = interaction.text_values["body"]
        image = interaction.text_values["image"]

        embed = Embeds.emb(self.color, title, content)
        embed.set_image(image)
        embed.set_footer(text=interaction.guild.name, icon_url=interaction.guild.icon)
        await interaction.send(
            embed=Embeds.emb(Embeds.green, "Embed sent! :white_check_mark:"),
            ephemeral=True,
            delete_after=1,
        )
        await interaction.channel.send(embed=embed)

    async def on_error(self, error: Exception, inter: disnake.ModalInteraction):  # type: ignore[reportIncompatibleMethodOverride]
        await inter.response.send_message(
            embed=Embeds.emb(Embeds.red, "Oops! Something went wrong :cry:"),
            ephemeral=True,
        )


class Misc(commands.Cog):
    def __init__(self, client: MrRobot):
        self.bot = client

    @commands.slash_command(name="embed", dm_permission=False)
    async def slash_embed(
        self,
        interaction: disnake.CommandInteraction,
        color: Union[disnake.Color, None] = None,
    ):
        """
        Creates embed

        Parameters
        ----------
        color: Hex code or name of colour
        """
        await interaction.response.send_modal(modal=EmbedModal(color=color))

    @commands.slash_command(name="userinfo", dm_permission=False)
    async def slash_userinfo(
        self,
        interaction: disnake.GuildCommandInteraction,
        member: disnake.Member = commands.Param(lambda interaction: interaction.author),
    ):
        """
        Shows user info

        Parameters
        ----------
        member : Member to show info
        """
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
            value=(
                joined_at.strftime("%a %#d %B %Y, %I:%M %p UTC")
                if (joined_at := member.joined_at)
                else "Unknown"
            ),
            inline=False,
        )
        members = sorted(interaction.guild.members, key=lambda m: m.joined_at)  # type: ignore[reportCallIssue]
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
        user_temp_dat = await (
            await self.bot.db.execute(
                "select role_id, expiration from temprole where user_id = ? and guild_id = ?",
                (member.id, interaction.guild.id),
            )
        ).fetchall()
        roles: Set = set()
        for dat in user_temp_dat:
            roles.add(interaction.guild.get_role(dat[0]))
        if roles:
            embed.add_field(
                name="Temporary Roles" if len(user_temp_dat) > 1 else "Temporary Role",
                value="\n".join(
                    [
                        f"{role.mention if ( role := interaction.guild.get_role(dat[0])) else ''}:crossed_swords:{disnake.utils.format_dt(datetime.fromtimestamp(dat[1]))}"
                        for dat in user_temp_dat
                    ]
                ),
                inline=False,
            )
        await interaction.send(embed=embed, components=[delete_button])


def setup(client: MrRobot):
    client.add_cog(Misc(client))
