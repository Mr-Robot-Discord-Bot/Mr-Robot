import datetime
import logging
from typing import Optional, Union

import disnake
from disnake.ext import commands, tasks

from utils import Embeds, delete_button, parse_time

MISSING = "MISSING"
logger = logging.getLogger(__name__)


class Moderation(commands.Cog):
    def __init__(self, client):
        self.bot = client
        logger.info("Moderation Cog Loaded")

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.db.execute(
            """
                CREATE TABLE IF NOT EXISTS temprole (
                    guild_id bigint, user_id bigint, role_id bigint, expiration decimal
                    )
                """
        )
        await self.bot.db.commit()
        self.check_temprole.start()

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

    @user.sub_command(name="temprole")
    @commands.check_any(
        commands.is_owner(), commands.has_permissions(manage_roles=True)  # type: ignore
    )
    async def slash_temprole(
        self,
        interaction: disnake.GuildCommandInteraction,
        user: disnake.Member,
        role: disnake.Role,
        duration: str,
    ):
        """
        Assign the roles for a specific duration

        Parameters
        ----------
        user : User to add role
        role : Role to add
        duration: Duration for which role will be assigned
        """
        try:
            tenure = datetime.datetime.utcnow() + parse_time(duration)
        except ValueError:
            raise commands.BadArgument(
                "Invalid Duration, try eg: `3 week`, `9 day`, `27 hour`, `1 year`"
            )
        expiry = tenure.timestamp()
        await user.add_roles(role)
        if await (
            await self.bot.db.execute(
                """
                SELECT * FROM temprole WHERE guild_id = ? AND user_id = ? AND role_id = ?
                """,
                (interaction.guild.id, user.id, role.id),
            )
        ).fetchone():
            await self.bot.db.execute(
                """
                UPDATE temprole SET expiration = ? WHERE guild_id = ? AND user_id = ? AND role_id = ?
                """,
                (expiry, interaction.guild.id, user.id, role.id),
            )
        else:
            await self.bot.db.execute(
                """
                INSERT INTO temprole (guild_id, user_id, role_id, expiration) VALUES (?, ?, ?, ?)
                """,
                (interaction.guild.id, user.id, role.id, expiry),
            )
        await self.bot.db.commit()
        await interaction.send(
            components=[delete_button],
            embed=Embeds.emb(
                Embeds.green,
                "Temporarily Role Assigned",
                f"🎊 {user.mention} got {role.mention} for `{duration}` 🎊",
            ),
        )
        try:
            await user.send(
                embed=Embeds.emb(
                    Embeds.green,
                    "Temporarily Role Assigned",
                    f"You Have Got  `{role}` Role For `{duration}` In {interaction.guild.name}!",
                )
            )
        except (disnake.Forbidden, disnake.errors.HTTPException, AttributeError):
            ...

    @tasks.loop()
    async def check_temprole(self):
        rows = await (
            await self.bot.db.execute(
                """
            SELECT guild_id, user_id, role_id, expiration FROM temprole
            """
            )
        ).fetchall()
        for row in rows:
            (guild_id, user_id, role_id, expiration) = row
            expiration = datetime.datetime.fromtimestamp(expiration)
            guild = self.bot.get_guild(guild_id)
            user = guild.get_member(user_id)
            role = disnake.utils.get(guild.roles, id=role_id)
            if not guild or not role:
                continue
            elif not user:
                logger.info(f"User not found {user_id} Deleting it!")
                await self.bot.db.execute(
                    """
                    DELETE FROM temprole WHERE guild_id = ? AND user_id = ?
                    """,
                    (guild_id, user_id),
                )
                await self.bot.db.commit()
                continue
            if expiration <= datetime.datetime.utcnow():
                logger.info(f"Removing {role} from {user}")
                await user.remove_roles(role)
                await self.bot.db.execute(
                    """
                    DELETE FROM temprole WHERE guild_id = ? AND user_id = ? AND role_id = ?
                    """,
                    (guild_id, user_id, role_id),
                )
                await self.bot.db.commit()
                try:
                    await user.send(
                        embed=Embeds.emb(
                            Embeds.red,
                            "Role Expired",
                            f"Your `{role}` Role Has Expired In `{guild.name}`!",
                        )
                    )
                except (
                    disnake.Forbidden,
                    disnake.errors.HTTPException,
                    AttributeError,
                ):
                    ...

    @user.sub_command(name="addrole")
    @commands.check_any(
        commands.is_owner(), commands.has_permissions(manage_roles=True)  # type: ignore
    )
    async def slash_addrole(
        self,
        interaction: disnake.GuildCommandInteraction,
        user: disnake.Member,
        role: disnake.Role,
    ):
        """
        Assign the roles

        Parameters
        ----------
        user : User to add role
        role : Role to add
        """
        role = disnake.utils.get(user.guild.roles, name=str(role))  # type: ignore
        await user.add_roles(role)
        await interaction.send(
            components=[delete_button],
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
        commands.is_owner(), commands.has_permissions(manage_roles=True)  # type: ignore
    )
    async def slash_rmrole(self, interaction, user: disnake.Member, role: disnake.Role):
        """
        Removes the roles

        Parameters
        ----------
        user : User to remove role
        role : Role to remove
        """
        role = disnake.utils.get(user.guild.roles, name=str(role))  # type: ignore
        await user.remove_roles(role)
        await interaction.send(
            components=[delete_button],
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
    @commands.check_any(commands.is_owner(), commands.has_permissions(ban_members=True))  # type: ignore
    async def slash_unban(
        self, interaction: disnake.GuildCommandInteraction, member: str
    ):
        """
        Unbans the member

        Parameters
        ----------
        member : Member to unban
        """
        try:
            await interaction.guild.unban(disnake.Object(int(member)))
            await interaction.send(
                components=[delete_button],
                embed=Embeds.emb(Embeds.green, "Unbanned", f"Unbanned: <@{member}>"),
            )
        except Exception:
            raise commands.BadArgument(
                ":cry: No Such User Found, Select from the suggestion shown!"
            )

    @slash_unban.autocomplete("member")
    async def unban_autocomplete(
        self, interaction: disnake.GuildCommandInteraction, name
    ):
        members = {
            ban.user.name: str(ban.user.id) async for ban in interaction.guild.bans()
        }
        sorted_dict = {}
        matching_items = {}

        for key, value in members.items():
            if name in key:
                matching_items[key] = value

        sorted_items = sorted(matching_items.items(), key=lambda x: x[0].index(name))
        sorted_dict = dict(sorted_items)

        return sorted_dict

    @user.sub_command(name="ban")
    @commands.check_any(commands.is_owner(), commands.has_permissions(ban_members=True))  # type: ignore
    async def slash_ban(
        self,
        interaction: disnake.GuildCommandInteraction,
        member: disnake.Member,
        reason=None,
    ):
        """
        Bans the member

        Parameters
        ----------
        member : Member to ban
        reason : Reason for ban
        """
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
            components=[delete_button],
            embed=Embeds.emb(
                Embeds.red, "Banned", f"Banned: {member.mention} Reason: {reason}"
            ),
        )
        await member.ban(clean_history_duration=604800, reason=reason)

    @user.sub_command(name="timeout")
    @commands.check_any(
        commands.is_owner(), commands.has_permissions(moderate_members=True)  # type: ignore
    )
    async def slash_edit(
        self,
        interaction,
        member: disnake.Member,
        duration: str,
        reason: Union[None, str] = None,
    ):
        """
        Temporarily mutes the member

        Parameters
        ----------
        member : Member To Mute
        duration : Duration Of Mute
        reason : Reason For Mute
        """
        try:
            tenure = parse_time(duration)
        except ValueError:
            raise commands.BadArgument("Invalid duration, try eg: `1 hour`, `2 days`")
        await interaction.response.defer()
        try:
            await member.edit(timeout=tenure, reason=reason)
        except disnake.errors.HTTPException:
            raise commands.BadArgument("Duration upto 28 days are supported")
        try:
            await member.send(
                embed=Embeds.emb(
                    Embeds.red,
                    "You are Temporarily Muted "
                    f"in the {interaction.guild.name} server",
                    f"Reason: {reason}",
                )
            )
        except (disnake.Forbidden, disnake.errors.HTTPException):
            ...
        await interaction.send(
            components=[delete_button],
            embed=Embeds.emb(
                Embeds.red,
                "Temporarily Muted",
                f"{member.mention} is muted " f"for {duration}" f"\n Reason: {reason}",
            ),
        )

    @user.sub_command(name="kick")
    @commands.check_any(
        commands.is_owner(), commands.has_permissions(kick_members=True)  # type: ignore
    )
    async def slash_kick(self, interaction, member: disnake.Member, reason=None):
        """
        Kicks the member

        Parameters
        ----------
        member : Member to kick
        reason : Reason for kick
        """

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
            components=[delete_button],
            embed=Embeds.emb(
                Embeds.red, "Kicked", f"Kicked: {member.mention} Reason: {reason}"
            ),
        )
        await member.kick(reason=reason)

    @user.sub_command(name="dm")
    @commands.check_any(
        commands.is_owner(), commands.has_permissions(moderate_members=True)  # type: ignore
    )
    async def slash_dm_custom(
        self, interaction, member: disnake.Member, title: str, message: str
    ):
        """
        Dm's the user

        Parameters
        ----------
        member : Member To Dm
        title : Title Of Dm
        message : Message To Send. Use ; for newline
        """
        try:
            await member.send(
                embed=Embeds.emb(Embeds.yellow, title, message.replace(";", "\n"))
            )
            await interaction.send(
                embed=Embeds.emb(Embeds.yellow, title, message.replace(";", "\n")),
                ephemeral=True,
            )
        except disnake.Forbidden:
            await interaction.send(
                embed=Embeds.emb(Embeds.red, "Dm not sent"), ephemeral=True
            )

    @user.sub_command(name="warn")
    @commands.check_any(
        commands.is_owner(), commands.has_permissions(moderate_members=True)  # type: ignore
    )
    async def slash_warn(self, interaction, member: disnake.Member, message: str):
        """
        Warns the user

        Parameters
        ----------
        member : Member To Warn
        message : Message To Send. Use ; for newline
        """
        await interaction.send(
            components=[delete_button],
            embed=Embeds.emb(
                Embeds.red,
                f"WARNING {member}",
                f"{member.mention} --> " + message.replace(";", "\n"),
            ),
        )
        try:
            await member.send(
                embed=Embeds.emb(Embeds.red, "WARNING", message.replace(";", "\n"))
            )
        except Exception:
            ...

    @user.sub_command(name="roleall")
    @commands.check_any(
        commands.is_owner(), commands.has_permissions(manage_guild=True)  # type: ignore
    )
    async def roleall(
        self,
        interaction: disnake.GuildCommandInteraction,
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
            components=[delete_button],
        )
        try:
            for member in interaction.guild.members:
                if action == "add":
                    await member.add_roles(role)
                elif action == "remove":
                    await member.remove_roles(role)
            await interaction.send(
                components=[delete_button],
                embed=Embeds.emb(
                    Embeds.green,
                    "Roleall",
                    f"{role.mention} has been {'added to' if action == 'add' else 'removed from'} all members",
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
        commands.is_owner(), commands.has_permissions(manage_messages=True)  # type: ignore
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
        commands.is_owner(), commands.has_permissions(manage_channels=True)  # type: ignore
    )
    async def lock(
        self,
        interaction: disnake.GuildCommandInteraction,
        channel: disnake.TextChannel,
        role: Optional[disnake.Role] = None,
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
            components=[delete_button],
        )

    @server.sub_command(name="unlock")
    @commands.check_any(
        commands.is_owner(), commands.has_permissions(manage_channels=True)  # type: ignore
    )
    async def unlock(
        self,
        interaction: disnake.GuildCommandInteraction,
        channel: disnake.TextChannel,
        role: Optional[disnake.Role] = None,
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
            components=[delete_button],
        )

    @server.sub_command(name="hide")
    @commands.check_any(
        commands.is_owner(), commands.has_permissions(manage_channels=True)  # type: ignore
    )
    async def hide(
        self,
        interaction: disnake.GuildCommandInteraction,
        channel: disnake.TextChannel,
        role: Optional[disnake.Role] = None,
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
            components=[delete_button],
        )

    @server.sub_command(name="unhide")
    @commands.check_any(
        commands.is_owner(), commands.has_permissions(manage_channels=True)  # type: ignore
    )
    async def unhide(
        self,
        interaction: disnake.GuildCommandInteraction,
        channel: disnake.TextChannel,
        role: Optional[disnake.Role] = None,
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
            components=[delete_button],
        )

    @server.sub_command(name="nuke")
    @commands.check_any(
        commands.is_owner(), commands.has_permissions(manage_channels=True)  # type: ignore
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
                components=[delete_button],
            )
            new_channel = await channel.clone()
            await channel.delete()
            await new_channel.send(
                embed=Embeds.emb(Embeds.green, "Nuked", "This channel has been nuked!"),
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

    @server.sub_command(name="delete")
    @commands.check_any(
        commands.is_owner(), commands.has_permissions(manage_channels=True)  # type: ignore
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
        try:
            await channel.delete()
            await interaction.send(
                embed=Embeds.emb(
                    Embeds.green, "Deleted", f"{channel.name} has been deleted!"
                ),
                components=[delete_button],
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

    @server.sub_command(name="clone")
    @commands.check_any(
        commands.is_owner(), commands.has_permissions(manage_channels=True)  # type: ignore
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
                components=[delete_button],
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
