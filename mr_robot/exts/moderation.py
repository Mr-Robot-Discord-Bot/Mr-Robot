import datetime
import logging
from typing import Optional, Union

import disnake
import sqlalchemy
from disnake.ext import commands, tasks
from sqlalchemy.exc import IntegrityError

from mr_robot.bot import MrRobot
from mr_robot.database import TempRole
from mr_robot.utils.helpers import Embeds, parse_time
from mr_robot.utils.messages import DeleteButton

logger = logging.getLogger(__name__)


class Moderation(commands.Cog):
    def __init__(self, client: MrRobot):
        self.bot = client
        self.check_temprole.start()

    @commands.slash_command(name="mod", dm_permission=False)
    async def mod(self, _):
        """Moderation Commands"""

        ...

    @mod.sub_command_group(name="server")
    async def server(self, _):
        """Commands related to server"""
        ...

    @mod.sub_command_group(name="user")
    async def user(self, _):
        """Commands related to user"""
        ...

    @user.sub_command(name="temprole")
    @commands.has_permissions(manage_roles=True)
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
        expiry = str(tenure.timestamp())
        await user.add_roles(role)

        async with self.bot.db.begin() as session:
            # Could't use session.merge as it will require id argument too which is unkown here
            sql_query = sqlalchemy.select(TempRole).where(
                TempRole.guild_id == interaction.guild.id,
                TempRole.user_id == user.id,
                TempRole.role_id == role.id,
            )
            logger.info(
                f"Checking {interaction.guild.id=}, {user.id=}, {role.id=}, {expiry=}"
            )
            result = await session.scalars(sql_query)
            temprole = result.one_or_none()

            if temprole is None:
                sql_query = TempRole(
                    guild_id=interaction.guild.id,
                    user_id=user.id,
                    role_id=role.id,
                    expiration=expiry,
                )
                session.add(sql_query)
                logger.debug(f"Added {sql_query} in db.")
            else:
                logger.debug(f"Updating {temprole} in db.")
                temprole.expiration = expiry

            await session.commit()

        await interaction.send(
            components=[DeleteButton(interaction.author)],
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
        async with self.bot.db.begin() as session:
            sql_query = sqlalchemy.select(TempRole)
            result = await session.scalars(sql_query)
            result = result.all()
        for temprole in result:
            expiration = datetime.datetime.fromtimestamp(float(temprole.expiration))
            guild = self.bot.get_guild(temprole.guild_id)
            if not guild:
                continue
            user = guild.get_member(temprole.user_id)
            role = disnake.utils.get(guild.roles, id=temprole.role_id)
            if not guild or not role:
                continue
            elif not user:

                async with self.bot.db.begin() as session:
                    sql_query = sqlalchemy.delete(TempRole).where(
                        TempRole.guild_id == temprole.guild_id,
                        TempRole.user_id == temprole.user_id,
                    )
                    await session.execute(sql_query)
                    await session.commit()
                    logger.debug(f"User not found. Deleting {temprole}.")

                continue
            if expiration <= datetime.datetime.utcnow():
                logger.debug(f"Removing '{role}' role from {user}")
                await user.remove_roles(role)

                async with self.bot.db.begin() as session:
                    sql_query = sqlalchemy.delete(TempRole).where(
                        TempRole.guild_id == temprole.guild_id,
                        TempRole.user_id == temprole.user_id,
                    )
                    await session.execute(sql_query)
                    await session.commit()
                    logger.debug(f"Removing {temprole} from db.")

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
    @commands.has_permissions(manage_roles=True)
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
        get_role = disnake.utils.get(user.guild.roles, name=str(role))
        if get_role is None:
            raise commands.CommandError(f"{role.mention} not found")
        role = get_role
        await user.add_roles(role)
        await interaction.send(
            components=[DeleteButton(interaction.author)],
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
    @commands.has_permissions(manage_roles=True)
    async def slash_rmrole(self, interaction, user: disnake.Member, role: disnake.Role):
        """
        Removes the roles

        Parameters
        ----------
        user : User to remove role
        role : Role to remove
        """
        get_role = disnake.utils.get(user.guild.roles, name=str(role))
        if get_role is None:
            raise commands.CommandError(f"{role.mention} not found")
        role = get_role
        await user.remove_roles(role)
        await interaction.send(
            components=[DeleteButton(interaction.author)],
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
    @commands.has_permissions(ban_members=True)
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
                components=[DeleteButton(interaction.author)],
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
        matching_items = {}

        for key, value in members.items():
            if name in key:
                matching_items[key] = value

        sorted_items = sorted(matching_items.items(), key=lambda x: x[0].index(name))
        sorted_dict = dict(sorted_items)

        return sorted_dict

    @user.sub_command(name="ban")
    @commands.has_permissions(ban_members=True)
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
            components=[DeleteButton(interaction.author)],
            embed=Embeds.emb(
                Embeds.red, "Banned", f"Banned: {member.mention} Reason: {reason}"
            ),
        )
        await member.ban(clean_history_duration=604800, reason=reason)

    @user.sub_command(name="timeout")
    @commands.has_permissions(moderate_members=True)
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
            components=[DeleteButton(interaction.author)],
            embed=Embeds.emb(
                Embeds.red,
                "Temporarily Muted",
                f"{member.mention} is muted " f"for {duration}" f"\n Reason: {reason}",
            ),
        )

    @user.sub_command(name="kick")
    @commands.has_permissions(kick_members=True)
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
            components=[DeleteButton(interaction.author)],
            embed=Embeds.emb(
                Embeds.red, "Kicked", f"Kicked: {member.mention} Reason: {reason}"
            ),
        )
        await member.kick(reason=reason)

    @user.sub_command(name="dm")
    @commands.has_permissions(moderate_members=True)
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
    @commands.has_permissions(moderate_members=True)
    async def slash_warn(self, interaction, member: disnake.Member, message: str):
        """
        Warns the user

        Parameters
        ----------
        member : Member To Warn
        message : Message To Send. Use ; for newline
        """
        await interaction.send(
            components=[DeleteButton(interaction.author)],
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
    @commands.has_permissions(manage_guild=True)
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
            components=[DeleteButton(interaction.author)],
        )
        try:
            for member in interaction.guild.members:
                if action == "add":
                    await member.add_roles(role)
                elif action == "remove":
                    await member.remove_roles(role)
            await interaction.send(
                components=[DeleteButton(interaction.author)],
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
    @commands.has_permissions(manage_messages=True)
    async def slash_clear(
        self,
        interaction: disnake.GuildCommandInteraction,
        amount: int = 1,
        user: Optional[disnake.User] = None,
    ):
        """
        Deletes the messages

        Parameters
        ----------
        amount: Amount of messages to check for deletion
        user: User to delete messages from
        """
        await interaction.response.defer(ephemeral=True)
        if isinstance(interaction.channel, disnake.PartialMessageable):
            await interaction.send(
                embed=Embeds.emb(
                    Embeds.red,
                    "Missing Permissions",
                    "I don't have sufficient permissions to perform this task :cry:",
                ),
                ephemeral=True,
            )
            return
        deleted_msg = await interaction.channel.purge(
            limit=int(amount),
            check=(lambda u: u.author.id == user.id) if user else (lambda _: True),
            bulk=True,
        )
        await interaction.send(
            embed=Embeds.emb(Embeds.yellow, f"{len(deleted_msg)} message deleted"),
            ephemeral=True,
        )

    @server.sub_command(name="lock")
    @commands.has_permissions(manage_channels=True)
    async def lock(
        self,
        interaction: disnake.GuildCommandInteraction,
        channel: disnake.TextChannel,
        member_or_role: Optional[Union[disnake.Role, disnake.Member]] = None,
    ):
        """
        Locks out the channel from messaging

        Parameters
        ----------
        channel: Channel to lock
        member_or_role: Lock channel for role or member
        """
        await channel.set_permissions(
            member_or_role or interaction.guild.default_role, send_messages=False
        )
        msg = f"{channel.mention} has been locked !"
        if member_or_role:
            msg = f"{channel.mention} has been locked for {member_or_role.mention} !"
        await interaction.send(
            embed=Embeds.emb(Embeds.red, "Locked", msg),
            components=[DeleteButton(interaction.author)],
        )

    @server.sub_command(name="unlock")
    @commands.has_permissions(manage_channels=True)
    async def unlock(
        self,
        interaction: disnake.GuildCommandInteraction,
        channel: disnake.TextChannel,
        member_or_role: Optional[Union[disnake.Role, disnake.Member]] = None,
    ):
        """
        Unlocks out the channel from messaging

        Parameters
        ----------
        channel: Channel to unlock
        member_or_role: Unlock channel for role or member
        """
        await channel.set_permissions(
            member_or_role or interaction.guild.default_role, send_messages=True
        )
        msg = f"{channel.mention} has been unlocked !"
        if member_or_role:
            msg = f"{channel.mention} has been unlocked for {member_or_role.mention} !"
        await interaction.send(
            embed=Embeds.emb(Embeds.green, "Unlocked", msg),
            components=[DeleteButton(interaction.author)],
        )

    @server.sub_command(name="hide")
    @commands.has_permissions(manage_channels=True)
    async def hide(
        self,
        interaction: disnake.GuildCommandInteraction,
        channel: disnake.TextChannel,
        member_or_role: Optional[Union[disnake.Role, disnake.Member]] = None,
    ):
        """
        Hides the channel

        Parameters
        ----------
        channel: Channel to hide
        member_or_role: Hide channel for role or member
        """
        await channel.set_permissions(
            member_or_role or interaction.guild.default_role, view_channel=False
        )
        msg = f"{channel.mention} has been hidden !"
        if member_or_role:
            msg = f"{channel.mention} has been hidden for {member_or_role.mention} !"
        await interaction.send(
            embed=Embeds.emb(Embeds.red, "Hidden", msg),
            components=[DeleteButton(interaction.author)],
        )

    @server.sub_command(name="unhide")
    @commands.has_permissions(manage_channels=True)
    async def unhide(
        self,
        interaction: disnake.GuildCommandInteraction,
        channel: disnake.TextChannel,
        member_or_role: Optional[Union[disnake.Role, disnake.Member]] = None,
    ):
        """
        Unhides the channel

        Parameters
        ----------
        channel: Channel to unhide
        member_or_role: Unhide channel for role or member
        """
        await channel.set_permissions(
            member_or_role or interaction.guild.default_role, view_channel=True
        )
        msg = f"{channel.mention} has been unhidden !"
        if member_or_role:
            msg = f"{channel.mention} has been unhidden for {member_or_role.mention} !"

        await interaction.send(
            embed=Embeds.emb(Embeds.green, "Unhidden", msg),
            components=[DeleteButton(interaction.author)],
        )

    @server.sub_command(name="nuke")
    @commands.has_permissions(manage_channels=True)
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
                embed=Embeds.emb(Embeds.yellow, "Nuke", f"Nuking {channel.mention}!"),
                components=[DeleteButton(interaction.author)],
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
    @commands.has_permissions(manage_channels=True)
    async def delete(
        self,
        interaction: disnake.GuildCommandInteraction,
        channel_or_category: Union[disnake.TextChannel, disnake.CategoryChannel],
    ):
        """
        Deletes channel

        Parameters
        ----------
        channel_or_category: Channel or category to delete
        """
        if isinstance(channel_or_category, disnake.CategoryChannel):
            await self.delete_category(interaction, channel_or_category)
            return
        channel = channel_or_category

        try:
            await channel.delete()
            await interaction.send(
                embed=Embeds.emb(
                    Embeds.green, "Deleted", f"{channel.name} has been deleted!"
                ),
                components=[DeleteButton(interaction.author)],
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

    async def delete_category(
        self,
        interaction: disnake.GuildCommandInteraction,
        category: disnake.CategoryChannel,
    ):
        await interaction.send(
            embed=Embeds.emb(
                Embeds.yellow, "Delete Category", f"Deleting {category.mention}!"
            ),
            components=[DeleteButton(interaction.author)],
        )
        for channel in category.channels:
            await channel.delete()
        await category.delete()

    @server.sub_command(name="clone")
    @commands.has_permissions(manage_channels=True)
    async def clone(
        self,
        interaction: disnake.CommandInteraction,
        channel: disnake.TextChannel,
        new_channel_name: Optional[str] = None,
    ):
        """
        Clones channel

        Parameters
        ----------
        channel: Channel to clone
        new_channel_name: Clone channel name
        """
        try:
            new_channel = await channel.clone(name=new_channel_name)
            _text = f"Cloned {channel.mention} -> {new_channel.mention}!"
            await interaction.send(
                embed=Embeds.emb(Embeds.yellow, "Clone", _text),
                components=[
                    DeleteButton(interaction.author),
                    disnake.ui.Button(
                        style=disnake.ButtonStyle.url,
                        url=new_channel.jump_url,
                        label="Go to new channel",
                    ),
                ],
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

    @server.sub_command(name="transfer_ownership")
    @commands.has_permissions(manage_guild=True)
    async def transfer_ownership(
        self, interaction: disnake.GuildCommandInteraction, member: disnake.Member
    ):
        """
        Transfers Ownership

        Parameters
        ----------
        member: Transfer ownership to ?
        """
        await interaction.guild.edit(owner=member)
        await interaction.send(
            embed=Embeds.emb(
                Embeds.green,
                "Ownership Transferred",
                f"{member.mention} is the new owner of this server",
            )
        )

    @server.sub_command(name="nsfw_toggle")
    @commands.has_permissions(manage_guild=True)
    async def nsfw_toggle(
        self,
        interaction: disnake.GuildCommandInteraction,
        channel_or_category: Union[disnake.TextChannel, disnake.CategoryChannel],
        value: bool,
    ):
        """
        Nsfw Toggle

        Parameters
        ----------
        channel_or_category: Channel or Category
        value: Bool value to set nsfw
        """
        await interaction.response.defer()
        if isinstance(channel_or_category, disnake.CategoryChannel):
            for channel in channel_or_category.channels:
                await channel.edit(nsfw=value)
        else:
            await channel_or_category.edit(nsfw=value)
        await interaction.send(
            embed=Embeds.emb(
                Embeds.green,
                "Nsfw Toggle",
                f"{channel_or_category.mention} is now {'' if value else 'not'} age-restriced!",
            ),
            components=[DeleteButton(interaction.author)],
        )


def setup(client: MrRobot):
    client.add_cog(Moderation(client))
