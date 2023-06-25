import logging
from enum import Enum
from typing import Optional, Union

import aiosqlite
import disnake
from aiosqlite import Connection
from disnake.ext import commands

from utils import Embeds, delete_button

logger = logging.getLogger(__name__)


class Configs(Enum):
    Slot_1 = 1
    Slot_2 = 2
    Slot_3 = 3
    Slot_4 = 4
    Slot_5 = 5


class Ticket(disnake.ui.Modal):
    def __init__(
        self,
        db: Connection,
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
        title_channel = interaction.text_values["title_channel"]
        description_channel = interaction.text_values["description_channel"]
        image_channel = interaction.text_values["image"]

        try:
            await self.db.execute(
                """
                    insert into tickets_config
                    (guild_id, color, ticket_config_id, user_or_role_id, category_id,
                     image, title, description)
                    values (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                (
                    interaction.guild.id,
                    self.color.value if self.color else None,
                    self.config,
                    self.user_or_role.id,
                    self.category.id,
                    image_channel,
                    title_channel,
                    description_channel,
                ),
            )
        except aiosqlite.IntegrityError:
            await self.db.execute(
                """
                update tickets_config set
                color = ?, user_or_role_id = ?, category_id = ?,
                image = ?, title = ?, description = ?
                where guild_id = ? and ticket_config_id = ?
                """,
                (
                    self.color.value if self.color else None,
                    self.user_or_role.id,
                    self.category.id,
                    image_channel,
                    title_channel,
                    description_channel,
                    interaction.guild.id,
                    self.config,
                ),
            )
        await self.db.commit()
        await interaction.send(
            embed=Embeds.emb(
                Embeds.green, f"{Configs(self.config).name} Config Created!"
            ),
            ephemeral=True,
            delete_after=2,
        )

    async def on_error(self, error: Exception, inter: disnake.ModalInteraction):
        logger.exception(error)
        await inter.response.send_message(
            embed=Embeds.emb(Embeds.red, "Oops! Something went wrong :cry:"),
            ephemeral=True,
        )


class TicketSystem(commands.Cog):
    def __init__(self, client):
        self.bot = client
        logger.info("TicketSystem Cog Loaded")

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.db.execute(
            """
                create table if not exists tickets_config
                (guild_id bigint, ticket_config_id bigint, user_or_role_id bigint,
                 category_id bigint, image text, color bigint,
                 title text, description text, primary key (guild_id, ticket_config_id))
                """
        )
        await self.bot.db.execute(
            """
                CREATE TABLE IF NOT EXISTS ticket_status
                (guild_id bigint, user_id bigint, ticket_config_id bigint,
                 channel_id bigint, primary key(guild_id, user_id, ticket_config_id))
                """
        )
        await self.bot.db.commit()

    @commands.slash_command(name="ticket", dm_permission=False)
    @commands.check_any(
        commands.is_owner(), commands.has_permissions(manage_guild=True)  # type: ignore
    )
    async def ticket(self, interaction: disnake.GuildCommandInteraction):
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
        result = await (
            await self.bot.db.execute(
                """
                select ticket_config_id from
                tickets_config where
                guild_id = ? and ticket_config_id = ?
                """,
                (interaction.guild.id, config),
            )
        ).fetchone()
        if not result:
            await interaction.send(
                embed=Embeds.emb(
                    Embeds.red,
                    f"{Configs(config).name} Was Empty!",
                    "Use `/ticket set_config` to create one",
                ),
                ephemeral=True,
            )
            return
        if self.bot.user.id != message_link_or_id.author.id:
            await interaction.send(
                embed=Embeds.emb(
                    Embeds.red,
                    "Message is not from the me!",
                    "Use `/embed` to create one",
                )
            )
            return
        await message_link_or_id.edit(
            components=[
                disnake.ui.Button(
                    emoji="🎫",
                    style=disnake.ButtonStyle.blurple,
                    custom_id=f"ticket-{config}",
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
        result = await (
            await self.bot.db.execute(
                """
            select ticket_config_id, color, user_or_role_id, category_id,
            image, title, description from tickets_config where
            guild_id = ?
            """,
                (interaction.guild.id,),
            )
        ).fetchall()
        if not result:
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
        for (
            config,
            color,
            user_or_role_id,
            category_id,
            image,
            title,
            description,
        ) in result:
            embeds.append(
                Embeds.emb(
                    color,
                    Configs(config).name,
                    f"""
                        **Title:** {title}
                        **Description:** {description}
                        **Color:** {disnake.Color(color) if color else "None"}
                        **User/Role:** {interaction.guild.get_role(user_or_role_id) or interaction.guild.get_member(user_or_role_id)}
                        **Category:** {interaction.guild.get_channel(category_id)}
                        **Image:** {f"[Click To See]({image})" if image else "None"}
                        """,
                )
            )
        await interaction.send(embeds=embeds, components=[delete_button])

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
            modal=Ticket(
                db=self.bot.db,
                category=category,
                config=config,
                user_or_role=user_or_role,
                color=color,
            )
        )

    @commands.Cog.listener()
    async def on_member_remove(self, member: disnake.Member):
        result = await (
            await self.bot.db.execute(
                """
                                            select channel_id from ticket_status
                                            where guild_id = ? and user_id = ?
                                            """,
                (member.guild.id, member.id),
            )
        ).fetchone()
        logger.info(f"Result: {result}")
        if result:
            (channel_id,) = result
            logger.info(f"Deleting channel {channel_id}")
            channel = member.guild.get_channel(channel_id)
            if channel:
                await channel.delete()
                await self.bot.db.execute(
                    """
                                        delete from ticket_status where
                                        guild_id = ? and user_id = ? and channel_id = ?
                                        """,
                    (member.guild.id, member.id, channel_id),
                )
                await self.bot.db.commit()

    @commands.Cog.listener()
    async def on_button_click(self, interaction: disnake.MessageInteraction):
        if not interaction.guild or not interaction.component.custom_id:
            return
        elif interaction.component.custom_id.startswith("delete_channel"):
            user_id = int(interaction.component.custom_id.split("-")[-1])
            await self.bot.db.execute(
                """
                    delete from ticket_status where
                    guild_id = ? and user_id = ? and channel_id = ?
                    """,
                (interaction.guild.id, user_id, interaction.channel.id),
            )
            await self.bot.db.commit()
            await interaction.channel.delete()  # type: ignore

        elif interaction.component.custom_id.startswith("ticket"):
            ticket_config_id = interaction.component.custom_id.split("-")[-1]
            result = await (
                await self.bot.db.execute(
                    """
                    select user_or_role_id, color,
                    category_id, image, title, description
                    from tickets_config where guild_id = ? and ticket_config_id = ?
                    """,
                    (interaction.guild.id, ticket_config_id),
                )
            ).fetchone()  # type: ignore
            if result:
                (
                    user_or_role_id,
                    color,
                    category_id,
                    image,
                    title,
                    description,
                ) = result
                try:
                    await self.bot.db.execute(
                        "insert into ticket_status (guild_id, user_id, ticket_config_id) values (?, ?, ?)",
                        (interaction.guild.id, interaction.author.id, ticket_config_id),
                    )
                except aiosqlite.IntegrityError:
                    await interaction.send(
                        embed=Embeds.emb(
                            Embeds.red,
                            "You already have a ticket open!",
                            "Please close the previous ticket to open a new one!",
                        ),
                        ephemeral=True,
                    )
                    return
                category = interaction.guild.get_channel(category_id)
                if not category:
                    return
                user_or_role = interaction.guild.get_role(user_or_role_id)
                if not user_or_role:
                    user_or_role = interaction.guild.get_member(user_or_role_id)
                channel = await interaction.guild.create_text_channel(
                    interaction.author.name,
                    category=category,  # type: ignore
                    overwrites={  # type: ignore
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
                await self.bot.db.execute(
                    """
                    update ticket_status set channel_id = ? where guild_id = ? and user_id = ? and ticket_config_id = ?
                    """,
                    (
                        channel.id,
                        interaction.guild.id,
                        interaction.author.id,
                        ticket_config_id,
                    ),
                )
                await channel.send(
                    embed=Embeds.emb(
                        disnake.Color(color) if color else None,
                        title,
                        description.replace("%user%", interaction.author.mention),
                    )
                    .set_image(image)
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
                    embed=Embeds.emb(
                        Embeds.green, "Ticket Created!", f"### {channel.mention}"
                    ),
                    ephemeral=True,
                )
                await self.bot.db.commit()


def setup(client: commands.Bot):
    client.add_cog(TicketSystem(client))
