import datetime
from typing import Union

import disnake
from disnake.ext import commands

from utils import DeleteButton, Embeds

MISSING = "MISSING"


class Moderation(commands.Cog):
    def __init__(self, client):
        self.bot = client

    @commands.slash_command(name="mod", dm_permission=False)
    async def mod(self, interaction: disnake.CommandInteraction):
        """Moderation Commands"""

        ...

    @mod.sub_command_group(name="server")
    async def server(self, interaction):
        """Commands for server"""
        ...

    @mod.sub_command_group(name="user")
    async def user(self, interaction):
        """Commands for user"""
        ...

    @user.sub_command(name="addrole")
    @commands.check_any(
        commands.is_owner(), commands.has_permissions(manage_roles=True)
    )
    async def slash_addrole(
        self, interaction, user: disnake.Member, role: disnake.Role
    ):
        """
        Assign the roles

        Parameters
        ----------
        user : User to add role
        role : Role to add
        """
        role = disnake.utils.get(user.guild.roles, name=str(role))
        await user.add_roles(role)
        await interaction.send(
            view=DeleteButton(author=interaction.author),
            embed=Embeds.emb(
                Embeds.green,
                "Role Assigned",
                f"{user.mention} Has Got  `{role}`  Role !",
            ),
        )
        try:
            await user.send(
                embed=Embeds.emb(
                    Embeds.green,
                    "Role Assigned",
                    f" You got `{role}` Role In {interaction.guild.name} !",
                )
            )
        except Exception:
            ...

    @user.sub_command(name="removerole")
    @commands.check_any(
        commands.is_owner(), commands.has_permissions(manage_roles=True)
    )
    async def slash_rmrole(self, interaction, user: disnake.Member, role: disnake.Role):
        """
        Removes the roles

        Parameters
        ----------
        user : User to remove role
        role : Role to remove
        """
        role = disnake.utils.get(user.guild.roles, name=str(role))
        await user.remove_roles(role)
        await interaction.send(
            view=DeleteButton(author=interaction.author),
            embed=Embeds.emb(
                Embeds.red,
                "Role Removed",
                f"{user.mention} Was Removed  `{role}` Role !",
            ),
        )
        try:
            await user.send(
                embed=Embeds.emb(
                    Embeds.red,
                    "Role Removed",
                    "You got removed from "
                    f"`{role}` Role In {interaction.guild.name}!",
                )
            )
        except disnake.Forbidden:
            ...

    @user.sub_command(name="unban")
    @commands.check_any(commands.is_owner(), commands.has_permissions(ban_members=True))
    async def self_unban(self, interaction, member):
        """
        Unbans the member

        Parameters
        ----------
        member : Member to unban
        """
        banned_users = await interaction.guild.bans()
        member_name, member_discriminator = member.split("#")
        for ban_entry in banned_users:
            user = ban_entry.user
            if (user.name, user.discriminator) == (member_name, member_discriminator):
                await interaction.guild.unban(user)
                await interaction.send(
                    view=DeleteButton(author=interaction.author),
                    embed=Embeds.emb(Embeds.green, "Unbanned", f"Unbanned: {user}"),
                )
                try:
                    await member.send(
                        embed=Embeds.emb(
                            name="You Were Unbanned From "
                            f"{interaction.guild.name} Server!"
                        )
                    )
                except disnake.Forbidden:
                    pass

                return

    @user.sub_command(name="ban")
    @commands.check_any(commands.is_owner(), commands.has_permissions(ban_members=True))
    async def slash_ban(self, interaction, member: disnake.Member, reason=None):
        """
        Bans the member

        Parameters
        ----------
        member : Member to ban
        reason : Reason for ban
        """
        await member.ban(reason=reason)
        try:
            await member.send(
                embed=Embeds.emb(
                    Embeds.red,
                    "You Were Banned From " f"{interaction.guild.name} Server!",
                    f"Reason: {reason}",
                )
            )
        except disnake.Forbidden:
            pass
        await interaction.send(
            view=DeleteButton(author=interaction.author),
            embed=Embeds.emb(
                Embeds.red, "Banned", f"Banned: {member} Reason: {reason}"
            ),
        )

    @user.sub_command(name="timeout")
    @commands.check_any(
        commands.is_owner(), commands.has_permissions(moderate_members=True)
    )
    async def slash_edit(
        self,
        interaction,
        member: disnake.Member,
        hours: int = 1,
        days: int = 0,
        reason: Union[None, str] = None,
    ):
        """
        Temporarily mutes the member

        Parameters
        ----------
        member : Member To Mute
        hours : Hours To Mute
        days : Days To Mute
        reason : Reason For Mute
        """
        if days == 0 and hours == 0:
            await interaction.send(
                embed=Embeds.emb(
                    Embeds.red, "Error", "User can't be muted for 0 minutes"
                ),
                ephemeral=True,
            )
        else:
            await member.edit(
                timeout=datetime.timedelta(days=days, hours=hours).total_seconds()
            )
            try:
                await member.send(
                    embed=Embeds.emb(
                        Embeds.red,
                        "You are Temporarily Muted "
                        f"in the {interaction.guild.name} server",
                        f"Reason: {reason}",
                    )
                )
            except disnake.Forbidden:
                pass
            await interaction.send(
                view=DeleteButton(author=interaction.author),
                embed=Embeds.emb(
                    Embeds.red,
                    "Temporarily Muted",
                    f"{member.mention} is muted "
                    f"for {datetime.timedelta(days=days,hours=hours)}",
                ),
            )

    @user.sub_command(name="kick")
    @commands.check_any(
        commands.is_owner(), commands.has_permissions(kick_members=True)
    )
    async def slash_kick(self, interaction, member: disnake.Member, reason=None):
        """
        Kicks the member

        Parameters
        ----------
        member : Member to kick
        reason : Reason for kick
        """
        await member.kick(reason=reason)

        try:
            await member.send(
                embed=Embeds.emb(
                    Embeds.red,
                    f"You Were Kicked From {interaction.guild.name} Server!",
                    f"Reason: {reason}",
                )
            )
        except Exception:
            ...
        await interaction.send(
            view=DeleteButton(author=interaction.author),
            embed=Embeds.emb(
                Embeds.red, "Kicked", f"Kicked: {member} Reason: {reason}"
            ),
        )

    @user.sub_command(name="dm")
    @commands.check_any(
        commands.is_owner(), commands.has_permissions(moderate_members=True)
    )
    async def slash_dm_custom(
        self, interaction, member: disnake.Member, title: str, msg: str
    ):
        """
        Dm's the user

        Parameters
        ----------
        member : Member To Dm
        title : Title Of Dm
        msg : Message To Send
        """
        try:
            await member.send(embed=Embeds.emb(Embeds.yellow, title, msg))
            await interaction.send(
                embed=Embeds.emb(Embeds.yellow, title, msg.replace(";", "\n")),
                ephemeral=True,
            )
        except disnake.Forbidden:
            await interaction.send(
                embed=Embeds.emb(Embeds.red, "Dm not sent"), ephemeral=True
            )

    @user.sub_command(name="warn")
    @commands.check_any(
        commands.is_owner(), commands.has_permissions(moderate_members=True)
    )
    async def slash_warn(self, interaction, member: disnake.Member, msg: str):
        """
        Warns the user

        Parameters
        ----------
        member : Member To Warn
        msg : Message To Send
        """
        await interaction.send(
            view=DeleteButton(author=interaction.author),
            embed=Embeds.emb(
                Embeds.red,
                f"WARNING {member}",
                f"{member.mention} --> " + msg.replace(";", "\n"),
            ),
        )
        try:
            await member.send(
                embed=Embeds.emb(Embeds.red, "WARNING", msg.replace(";", "\n"))
            )
        except Exception:
            ...

    @user.sub_command(name="roleall")
    @commands.check_any(
        commands.is_owner(), commands.has_permissions(manage_guild=True)
    )
    async def roleall(
        self,
        interaction: disnake.CommandInteraction,
        role: disnake.Role,
        action: str = commands.Param(choices=["add", "remove"]),
    ):
        """
        Adds or Removes a role to all members in the server

        Parameters
        ----------
        role: Choose role
        action: Action to take
        """
        await interaction.send(
            embed=Embeds.emb(
                Embeds.yellow,
                "Roleall",
                f"""
                Roleall initiated for {role}!
                Kindly be patient until you get next notification as this is time taking process
                """,
            ),
            ephemeral=True,
        )
        try:
            for member in interaction.guild.members:
                if action == "add":
                    await member.add_roles(role)
                elif action == "remove":
                    await member.remove_roles(role)
            await interaction.send(
                view=DeleteButton(author=interaction.author),
                embed=Embeds.emb(
                    Embeds.green,
                    "Roleall",
                    f"{role.mention} has been {'added' if action == 'add' else 'removed'} to all members",
                ),
            )
        except disnake.Forbidden:
            await interaction.send(
                embed=Embeds.emb(
                    Embeds.red,
                    "Insufficient Permissions",
                    f"I don't have enough permissions to role {role.mention} :cry:",
                ),
                ephemeral=True,
            )

    @server.sub_command(name="clear")
    @commands.check_any(
        commands.is_owner(), commands.has_permissions(manage_messages=True)
    )
    async def slash_clear(self, interaction, amount=1):
        """
        Deletes the messages

        Parameters
        ----------
        amount : Amount of messages to delete
        """
        await interaction.channel.purge(limit=int(amount))
        await interaction.send(
            embed=Embeds.emb(Embeds.yellow, f"{amount} message deleted"),
            ephemeral=True,
        )

    @server.sub_command(name="lock")
    @commands.check_any(
        commands.is_owner(), commands.has_permissions(manage_channels=True)
    )
    async def lock(
        self,
        interaction: disnake.CommandInteraction,
        channel: disnake.TextChannel,
        role: disnake.Role = None,
    ):
        """
        Locks out the channel from messaging

        Parameters
        ----------
        channel: Channel to lock
        role: Lock channel for role
        """
        await channel.set_permissions(
            role or interaction.guild.default_role, send_messages=False
        )
        await interaction.send(
            embed=Embeds.emb(
                Embeds.red, "Locked", f"{channel.mention} has been locked!"
            ),
            ephemeral=True,
        )

    @server.sub_command(name="unlock")
    @commands.check_any(
        commands.is_owner(), commands.has_permissions(manage_channels=True)
    )
    async def unlock(
        self,
        interaction: disnake.CommandInteraction,
        channel: disnake.TextChannel,
        role: disnake.Role = None,
    ):
        """
        Unlocks out the channel from messaging

        Parameters
        ----------
        channel: Channel to unlock
        role: Unlock channel for role
        """
        await channel.set_permissions(
            role or interaction.guild.default_role, send_messages=True
        )
        await interaction.send(
            embed=Embeds.emb(
                Embeds.green, "Unlocked", f"{channel.mention} has been unlocked!"
            ),
            ephemeral=True,
        )

    @server.sub_command(name="hide")
    @commands.check_any(
        commands.is_owner(), commands.has_permissions(manage_channels=True)
    )
    async def hide(
        self,
        interaction: disnake.CommandInteraction,
        channel: disnake.TextChannel,
        role: disnake.Role = None,
    ):
        """
        Hides the channel

        Parameters
        ----------
        channel: Channel to hide
        role: Hide channel for role
        """
        await channel.set_permissions(
            role or interaction.guild.default_role, view_channel=False
        )
        await interaction.send(
            embed=Embeds.emb(
                Embeds.red, "Hidden", f"{channel.mention} has been hidden!"
            ),
            ephemeral=True,
        )

    @server.sub_command(name="unhide")
    @commands.check_any(
        commands.is_owner(), commands.has_permissions(manage_channels=True)
    )
    async def unhide(
        self,
        interaction: disnake.CommandInteraction,
        channel: disnake.TextChannel,
        role: disnake.Role = None,
    ):
        """
        Unhides the channel

        Parameters
        ----------
        channel: Channel to unhide
        role: Unhide channel for role
        """
        await channel.set_permissions(
            role or interaction.guild.default_role, view_channel=True
        )
        await interaction.send(
            embed=Embeds.emb(
                Embeds.green, "Unhidden", f"{channel.mention} has been unhidden!"
            ),
            ephemeral=True,
        )

    @server.sub_command(name="nuke")
    @commands.check_any(
        commands.is_owner(), commands.has_permissions(manage_channels=True)
    )
    async def nuke(
        self, interaction: disnake.CommandInteraction, channel: disnake.TextChannel
    ):
        """
        Deletes and recreates the current or specified channel

        Parameters
        ----------
        channel: Channel to nuke
        """
        try:
            await interaction.send(
                embed=Embeds.emb(
                    Embeds.yellow, "Nuke", f"Nuke for {channel.mention} initiated!"
                ),
                ephemeral=True,
            )
            new_channel = await channel.clone()
            await channel.delete()
            await new_channel.send(
                embed=Embeds.emb(Embeds.green, "Nuked", "This channel has been nuked!"),
                delete_after=10,
            )
        except disnake.errors.Forbidden:
            await interaction.send(
                view=DeleteButton(author=interaction.author),
                embed=Embeds.emb(
                    Embeds.yellow,
                    "Missing Access",
                    "I don't have sufficient access to perform this task :cry:",
                ),
                ephemeral=True,
            )

    @server.sub_command(name="delete")
    @commands.check_any(
        commands.is_owner(), commands.has_permissions(manage_channels=True)
    )
    async def delete(
        self, interaction: disnake.CommandInteraction, channel: disnake.TextChannel
    ):
        """
        Deletes channel

        Parameters
        ----------
        channel: Channel to delete
        """
        await channel.delete()
        await interaction.send(
            embed=Embeds.emb(
                Embeds.green, "Deleted", f"{channel.mention} has been deleted!"
            ),
            ephemeral=True,
        )

    @server.sub_command(name="clone")
    @commands.check_any(
        commands.is_owner(), commands.has_permissions(manage_channels=True)
    )
    async def clone(
        self, interaction: disnake.CommandInteraction, channel: disnake.TextChannel
    ):
        """
        Clones channel

        Parameters
        ----------
        channel: Channel to clone
        """
        try:
            await interaction.send(
                embed=Embeds.emb(
                    Embeds.yellow, "Clone", f"Clone for {channel.mention} initiated!"
                ),
                ephemeral=True,
            )
            new_channel = await channel.clone()
            await new_channel.send(
                embed=Embeds.emb(Embeds.green, "Cloned", "Cloning Done!"),
                delete_after=10,
            )
        except disnake.errors.Forbidden:
            await interaction.send(
                embed=Embeds.emb(
                    Embeds.yellow,
                    "Missing Access",
                    "I don't have sufficient access to perform this task :cry:",
                ),
                ephemeral=True,
            )


def setup(client: commands.Bot):
    client.add_cog(Moderation(client))
