import logging
from enum import Enum
from typing import Optional, Union

import aiosqlite
import disnake
import sqlalchemy
from aiosqlite import Connection
from disnake.ext import commands
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from mr_robot.bot import MrRobot
from mr_robot.database import Ticket, TicketConfig
from mr_robot.utils.helpers import Embeds
from mr_robot.utils.messages import DeleteButton

logger = logging.getLogger(__name__)


class Configs(Enum):
    Config_1 = 1
    Config_2 = 2
    Config_3 = 3
    Config_4 = 4
    Config_5 = 5


class TicketModal(disnake.ui.Modal):
    def __init__(
        self,
        db: async_sessionmaker[AsyncSession],
        category: Optional[disnake.CategoryChannel],
        color: Optional[disnake.Color],
        config: Configs,
        user_or_role: Optional[Union[disnake.Role, disnake.Member]] = None,
    ):
        self.color = color
        self.db = db
        self.category = category
        self.user_or_role = user_or_role
        self.config = config

        components = [
            disnake.ui.TextInput(
                label="Image url",
                placeholder="Image url here",
                custom_id="image",
                style=disnake.TextInputStyle.short,
                required=False,
            ),
            disnake.ui.TextInput(
                label="Title for Ticket Channel",
                placeholder="Enter title here",
                custom_id="title_channel",
                style=disnake.TextInputStyle.short,
            ),
            disnake.ui.TextInput(
                label="Description for Ticket Channel",
                placeholder="Tips:<@Member_Id> for mention, <#Channel_Id> for tagging the channel,  %user% for interaction author",
                custom_id="description_channel",
                style=disnake.TextInputStyle.paragraph,
            ),
        ]
        super().__init__(title="Ticket Setup", custom_id="setup", components=components)

    async def callback(self, interaction: disnake.ModalInteraction):
        if not interaction.guild or not self.category or not self.user_or_role:
            return
        await interaction.response.defer()
        title_channel = interaction.text_values["title_channel"]
        description_channel = interaction.text_values["description_channel"]
        image_channel = interaction.text_values["image"]

        async with self.db.begin() as session:
            # Not using session.merge as it requires a primary key
            sql_query = sqlalchemy.select(TicketConfig).where(
                TicketConfig.guild_id == interaction.guild.id,
                TicketConfig.config_id == self.config.value,
            )
            result = await session.scalars(sql_query)
            result = result.one_or_none()
        if not result:
            sql_query = TicketConfig(
                guild_id=interaction.guild.id,
                config_id=self.config.value,
                user_or_role_id=self.user_or_role.id,
                category_id=self.category.id,
                image=image_channel,
                title=title_channel,
                description=description_channel,
                color=self.color.value if self.color else None,
            )
            session.add(sql_query)
        else:
            result.user_or_role_id = self.user_or_role.id
            result.category_id = self.category.id
            result.image = image_channel
            result.title = title_channel
            result.description = description_channel
            result.color = self.color.value if self.color else 0000
        await session.commit()

        await interaction.send(
            embed=Embeds.emb(
                Embeds.green, f"`{Configs(self.config).name}` config created!"
            ),
            ephemeral=True,
            components=[DeleteButton(interaction.author)],
        )

    async def on_error(self, error: Exception, inter: disnake.ModalInteraction):  # type: ignore[reportIncompatibleMethodOverride]
        logger.exception(error)
        await inter.response.send_message(
            embed=Embeds.emb(Embeds.red, "Oops! Something went wrong :cry:"),
            ephemeral=True,
        )


class TicketSystem(commands.Cog):
    def __init__(self, client: MrRobot):
        self.bot = client

    @commands.slash_command(name="ticket", dm_permission=False)
    @commands.has_permissions(manage_guild=True)
    async def ticket(self, _):
        """Ticket System"""

    @ticket.sub_command(name="set_button")
    async def add_btn_msg(
        self,
        interaction: disnake.GuildCommandInteraction,
        message_link_or_id: disnake.Message,
        config: Configs,
    ):
        """
        Add a ticket button to a message

        Parameters
        ----------
        message_link_or_id : Bot Message Link or Message ID
        config : Choose a config
        """
        async with self.bot.db.begin() as session:
            sql_query = sqlalchemy.select(TicketConfig).where(
                TicketConfig.guild_id == interaction.guild.id,
                TicketConfig.config_id == config.value,
            )
            result = await session.scalars(sql_query)
            result = result.one_or_none()
        if result is None:
            await interaction.send(
                embed=Embeds.emb(
                    Embeds.red,
                    f"{Configs(config).name} Was Empty!",
                    "Use `/ticket set_config` to create one",
                ),
                ephemeral=True,
            )
            return
        elif self.bot.user.id != message_link_or_id.author.id:
            await interaction.send(
                embed=Embeds.emb(
                    Embeds.red,
                    "Message is not created by me!",
                    "Use `/embed` to create one",
                )
            )
            return
        await message_link_or_id.edit(
            components=[
                disnake.ui.Button(
                    emoji="🎫",
                    style=disnake.ButtonStyle.blurple,
                    custom_id=f"ticket-{config.value}",
                )
            ]
        )
        await interaction.send(
            embed=Embeds.emb(Embeds.green, "Ticket Button Added!"),
            ephemeral=True,
            delete_after=2,
        )

    @ticket.sub_command(name="list_config")
    async def list_config(self, interaction: disnake.GuildCommandInteraction):
        """List all the configs"""
        async with self.bot.db.begin() as session:
            sql_query = sqlalchemy.select(TicketConfig).where(
                TicketConfig.guild_id == interaction.guild.id
            )
            configs = await session.scalars(sql_query)
            configs = configs.all()
        if not configs:
            await interaction.send(
                embed=Embeds.emb(
                    Embeds.red,
                    "No Configs Found!",
                    "Use `/ticket set_config` to create one",
                ),
                ephemeral=True,
            )
            return
        embeds = list()
        for config in configs:
            embeds.append(
                Embeds.emb(
                    config.color,
                    Configs(config).name,
                    f"""
                    **Title:** {config.title}
                    **Description:** \n{config.description}\n
                    **Color:** {disnake.Color(config.color) if config.color else "None"}
                    **User/Role:** {interaction.guild.get_role(config.user_or_role_id) or interaction.guild.get_member(config.user_or_role_id)}
                    **Category:** {interaction.guild.get_channel(config.category_id)}
                    **Image:** {f"[Click To See]({config.image})" if config.image else "None"}
                    """,
                )
            )
        await interaction.send(
            embeds=embeds, components=[DeleteButton(interaction.author)]
        )

    @ticket.sub_command(name="set_config")
    async def setup(
        self,
        interaction: disnake.GuildCommandInteraction,
        category: disnake.CategoryChannel,
        user_or_role: Union[disnake.Role, disnake.Member],
        config: Configs,
        color: Optional[disnake.Color] = None,
    ):
        """
        Setup Ticket System

        Parameters
        ----------
        category : CategoryChannel where the ticket channel will be created
        user_or_role : Role or Member who can see the ticket channel
        config : Choose a slot to store your config
        color : Color of the embed
        """
        await interaction.response.send_modal(
            modal=TicketModal(
                db=self.bot.db,
                category=category,
                config=config,
                user_or_role=user_or_role,
                color=color,
            )
        )

    @commands.Cog.listener()
    async def on_member_remove(self, member: disnake.Member):
        async with self.bot.db.begin() as session:
            sql_query = sqlalchemy.select(Ticket).where(
                Ticket.guild_id == member.guild.id, Ticket.user_id == member.id
            )
            result = await session.scalars(sql_query)
            result = result.all()
            if not result:
                return
            channel_ids = [ticket.channel_id for ticket in result]

            async def delete(channel_id):
                channel = member.guild.get_channel(channel_id)
                if not channel:
                    return
                await channel.delete()

            for channel_id in channel_ids:
                await delete(channel_id)
            sql_query = sqlalchemy.delete(Ticket).where(
                Ticket.guild_id == member.guild.id, Ticket.user_id == member.id
            )
            delete_row = await session.execute(sql_query)
            await session.commit()
            logger.debug(f"Removed {delete_row.all()} from db.")

    @commands.Cog.listener()
    async def on_button_click(self, interaction: disnake.MessageInteraction):
        if not interaction.guild or not interaction.component.custom_id:
            return
        elif interaction.component.custom_id.startswith("delete_channel"):
            user_id = int(interaction.component.custom_id.split("-")[-1])
            async with self.bot.db.begin() as session:
                sql_query = sqlalchemy.delete(Ticket).where(
                    Ticket.guild_id == interaction.guild.id,
                    Ticket.user_id == user_id,
                    Ticket.channel_id == interaction.channel.id,
                )
                await session.execute(sql_query)
                await session.commit()
                logger.debug(
                    f"Removed {Ticket(guild_id=interaction.guild.id, user_id=user_id, channel_id=interaction.channel.id)} from db."
                )
            if not isinstance(interaction.channel, disnake.PartialMessageable):
                await interaction.channel.delete()
            else:
                logger.warning(
                    f"Fails to delete {interaction.channel} in {interaction.guild.name}"
                )

        # ticket button schema: ticket-{config_id}
        elif interaction.component.custom_id.startswith("ticket"):
            ticket_config_id = int(interaction.component.custom_id.split("-")[-1])
            async with self.bot.db.begin() as session:
                sql_query = Ticket(
                    guild_id=interaction.guild.id,
                    user_id=interaction.author.id,
                    config_id=ticket_config_id,
                )
            try:
                session.add(sql_query)
                await session.commit()
                logger.debug(f"Added {sql_query} to db.")
            except IntegrityError:
                await interaction.send(
                    embed=Embeds.emb(
                        Embeds.red,
                        "You already have a ticket open!",
                        "Please close the previous ticket to open a new one!",
                    ),
                    ephemeral=True,
                )
                return None
            async with self.bot.db.begin() as session:
                sql_query = sqlalchemy.select(TicketConfig).where(
                    TicketConfig.guild_id == interaction.guild.id,
                    TicketConfig.config_id == ticket_config_id,
                )
                config = await session.scalars(sql_query)
                config = config.one_or_none()
            if not config:
                return
            category = interaction.guild.get_channel(int(config.category_id))
            if not category:
                return
            user_or_role = interaction.guild.get_role(config.user_or_role_id)
            if not user_or_role:
                user_or_role = interaction.guild.get_member(config.user_or_role_id)
            channel = await interaction.guild.create_text_channel(
                interaction.author.name,
                category=category,  # type: ignore[reportArgumentType]
                overwrites={  # type: ignore[reportArgumentType]
                    interaction.guild.default_role: disnake.PermissionOverwrite(
                        read_messages=False
                    ),
                    interaction.user: disnake.PermissionOverwrite(
                        read_messages=True,
                        send_messages=True,
                        attach_files=True,
                    ),
                    user_or_role: disnake.PermissionOverwrite(
                        read_messages=True,
                        send_messages=True,
                        attach_files=True,
                    ),
                    interaction.guild.me: disnake.PermissionOverwrite(
                        read_messages=True,
                        send_messages=True,
                        attach_files=True,
                    ),
                },
            )
            async with self.bot.db.begin() as session:
                sql_query = sqlalchemy.select(Ticket).where(
                    Ticket.guild_id == interaction.guild.id,
                    Ticket.user_id == interaction.author.id,
                    Ticket.config_id == ticket_config_id,
                )
                result = await session.scalars(sql_query)
                result = result.one()
                result.channel_id = channel.id
                await session.commit()
            await channel.send(
                embed=Embeds.emb(
                    disnake.Color(config.color) if config.color else None,
                    config.title,
                    config.description.replace("%user%", interaction.author.mention),
                )
                .set_image(config.image)
                .set_footer(
                    text=interaction.guild.name, icon_url=interaction.guild.icon
                ),
                components=[
                    disnake.ui.Button(
                        emoji="🗑️",
                        style=disnake.ButtonStyle.red,
                        custom_id=f"delete_channel-{interaction.author.id}",
                        label="Close Ticket",
                    )
                ],
            )
            await interaction.send(
                embed=Embeds.emb(Embeds.green, "Ticket Created!"),
                ephemeral=True,
                components=[
                    disnake.ui.Button(
                        style=disnake.ButtonStyle.url,
                        label="Go to your ticket",
                        url=channel.jump_url,
                    )
                ],
            )


def setup(client: MrRobot):
    client.add_cog(TicketSystem(client))
