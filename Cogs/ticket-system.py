import logging
from typing import Optional, Union

import aiosqlite
import disnake
from aiosqlite import Connection
from disnake.ext import commands

from utils import Embeds

logger = logging.getLogger(__name__)
delete_channel_button: disnake.ui.Button = disnake.ui.Button(
    emoji="🗑️",
    style=disnake.ButtonStyle.red,
    custom_id="delete_channel",
    label="Close Ticket",
)


class Ticket(disnake.ui.Modal):
    def __init__(
        self,
        db: Connection,
        category: Optional[disnake.CategoryChannel],
        color=None,
        user_or_role: Optional[Union[disnake.Role, disnake.Member]] = None,
        images_url: Optional[str] = None,
    ):
        self.color = color
        _image_url = images_url.split(" ") if images_url else [None, None]
        self.image_creator = _image_url[0] if len(_image_url) > 0 else None
        self.image_channel = _image_url[1] if len(_image_url) > 1 else None
        self.db = db
        self.category = category
        self.user_or_role = user_or_role

        components = [
            disnake.ui.TextInput(
                label="Title for Ticket Creator",
                placeholder="Enter title here",
                custom_id="title_creator",
                style=disnake.TextInputStyle.short,
            ),
            disnake.ui.TextInput(
                label="Description for Ticket Creator",
                placeholder="Tips:<@Member_Id> for mention, <#Channel_Id> for tagging the channel",
                custom_id="description_creator",
                style=disnake.TextInputStyle.paragraph,
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
        title_creator = interaction.text_values["title_creator"]
        title_channel = interaction.text_values["title_channel"]
        description_creator = interaction.text_values["description_creator"]
        description_channel = interaction.text_values["description_channel"]
        image_creator = self.image_creator
        image_channel = self.image_channel

        embed = Embeds.emb(self.color, title_creator, description_creator)
        embed.set_image(image_creator)
        embed.set_footer(text=interaction.guild.name, icon_url=interaction.guild.icon)
        result = await (
            await self.db.execute(
                """
                                            select ticket_config_id from tickets_config
                                            where guild_id = ? order by ticket_config_id desc limit 1
                                            """,
                (interaction.guild.id,),
            )
        ).fetchone()
        logger.info(f"{result} was retrieved ticket_config_id")
        if result:
            ticket_config_id = result[0] + 1
        else:
            ticket_config_id = 0
        new_ticket_button: disnake.ui.Button = disnake.ui.Button(
            emoji="🎫",
            style=disnake.ButtonStyle.blurple,
            custom_id=f"ticket-{ticket_config_id}",
        )
        await self.db.execute(
            """
                insert into tickets_config
                (guild_id, ticket_config_id, user_or_role_id, category_id,
                 image, title, description)
                values (?, ?, ?, ?, ?, ?, ?)
                """,
            (
                interaction.guild.id,
                ticket_config_id,
                self.user_or_role.id,
                self.category.id,
                image_channel,
                title_channel,
                description_channel,
            ),
        )
        await self.db.commit()
        await interaction.send(
            embed=Embeds.emb(Embeds.green, "Ticket Setup Complete!"),
            ephemeral=True,
            delete_after=5,
        )
        await interaction.channel.send(embed=embed, components=[new_ticket_button])

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
                 category_id bigint, image text,
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

    @ticket.sub_command(name="setup")
    async def setup(
        self,
        interaction: disnake.GuildCommandInteraction,
        category: disnake.CategoryChannel,
        user_or_role: Union[disnake.Role, disnake.Member],
        color: Optional[disnake.Color] = None,
        images_url: Optional[str] = None,
    ):
        """
        Setup Ticket System

        Parameters
        ----------
        category : CategoryChannel where the ticket channel will be created
        user_or_role : Role or Member who can see the ticket channel
        color : Color of the embed
        images_url : Input <Ticket_creator_img_url> then <Ticket_channel_img_url> with space
        """
        await interaction.response.send_modal(
            modal=Ticket(
                db=self.bot.db,
                category=category,
                user_or_role=user_or_role,
                color=color,
                images_url=images_url,
            )
        )

    @commands.Cog.listener()
    async def on_button_click(self, interaction: disnake.MessageInteraction):
        if not interaction.guild or not interaction.component.custom_id:
            return
        elif interaction.component.custom_id == "delete_channel":
            await self.bot.db.execute(
                """
                    delete from ticket_status where
                    guild_id = ? and user_id = ? and channel_id = ?
                    """,
                (interaction.guild.id, interaction.author.id, interaction.channel.id),
            )
            await self.bot.db.commit()
            await interaction.channel.delete()  # type: ignore

        elif interaction.component.custom_id.startswith("ticket"):
            ticket_config_id = interaction.component.custom_id.split("-")[-1]
            logger.info(f"ticket_config_id: {ticket_config_id}")
            result = await (
                await self.bot.db.execute(
                    """
                    select user_or_role_id,
                    category_id, image, title, description
                    from tickets_config where guild_id = ? and ticket_config_id = ?
                    """,
                    (interaction.guild.id, ticket_config_id),
                )
            ).fetchone()  # type: ignore
            logger.info(f"{result} was retrieved from tickets_config")
            if result:
                (user_or_role_id, category_id, image, title, description) = result
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
                logger.info(f"{category} was retrieved from guild")
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
                        Embeds.green,
                        title,
                        description.replace("%user%", interaction.author.mention),
                    )
                    .set_image(image)
                    .set_footer(
                        text=interaction.guild.name, icon_url=interaction.guild.icon
                    ),
                    components=[delete_channel_button],
                )
                await interaction.send(
                    f"Ticket has been created {channel.mention}", ephemeral=True
                )
                await self.bot.db.commit()


def setup(client: commands.Bot):
    client.add_cog(TicketSystem(client))
