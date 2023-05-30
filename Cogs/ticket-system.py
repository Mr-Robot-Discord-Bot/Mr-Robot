import logging
from typing import Optional, Union

import disnake
from aiosqlite import Connection
from disnake.ext import commands

from utils import Embeds

logger = logging.getLogger(__name__)
new_ticket_button: disnake.ui.Button = disnake.ui.Button(
    emoji="🎫",
    style=disnake.ButtonStyle.blurple,
    custom_id="new_ticket",
)
delete_channel_button: disnake.ui.Button = disnake.ui.Button(
    emoji="🗑️",
    style=disnake.ButtonStyle.red,
    custom_id="delete_channel",
    label="Close Ticket",
)


class Ticket(disnake.ui.Modal):
    def __init__(
        self,
        color=None,
        db: Optional[Connection] = None,
        category: Optional[disnake.CategoryChannel] = None,
        user_or_role: Optional[Union[disnake.Role, disnake.Member]] = None,
    ):
        self.color = color
        self.db = db
        self.category = category
        self.user_or_role = user_or_role

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
                label="Body",
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
        if not self.db:
            await interaction.send(
                "Ticket Interface Generated", ephemeral=True, delete_after=1
            )
            await interaction.channel.send(embed=embed, components=[new_ticket_button])
            return
        if not self.category or not self.user_or_role:
            return
        if await (
            await self.db.execute(
                """
                    select guild_id from tickets where
                    guild_id = ?
                    """,
                (interaction.guild.id,),
            )
        ).fetchone():
            await self.db.execute(
                """
                    update tickets set
                    guild_id = ?, user_or_role_id = ?,
                    category_id = ?, image = ?, title = ?,
                    description = ? where guild_id = ?
                    """,
                (
                    interaction.guild.id,
                    self.user_or_role.id,
                    self.category.id,
                    image,
                    title,
                    content,
                    interaction.guild.id,
                ),
            )
        else:
            await self.db.execute(
                """
                    insert into tickets
                    (guild_id, user_or_role_id, category_id,
                     image, title, description)
                    values (?, ?, ?, ?, ?, ?)
                    """,
                (
                    interaction.guild.id,
                    self.user_or_role.id,
                    self.category.id,
                    image,
                    title,
                    content,
                ),
            )
        await self.db.commit()
        await interaction.send("Ticket Setup Complete", ephemeral=True)

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

    @commands.slash_command(name="ticket", dm_permission=False)
    async def ticket(self, interaction: disnake.GuildCommandInteraction):
        """Ticket System"""

    @ticket.sub_command(name="interface")
    async def interface(
        self,
        interaction: disnake.GuildCommandInteraction,
        color: Optional[disnake.Color] = None,
    ):
        """Ticket Interface"""
        await interaction.response.send_modal(modal=Ticket(color))

    @ticket.sub_command(name="setup")
    async def setup(
        self,
        interaction: disnake.GuildCommandInteraction,
        category: disnake.CategoryChannel,
        user_or_role: Union[disnake.Role, disnake.Member],
    ):
        """Setup the ticket system"""
        await self.bot.db.execute(
            """
                create table if not exists tickets
                ('guild_id' int, 'user_or_role_id' int,
                 'category_id' int, 'image' string,
                 'title' string, 'description' string)
                """
        )
        await interaction.response.send_modal(
            modal=Ticket(
                db=self.bot.db,
                category=category,
                user_or_role=user_or_role,
            )
        )

    @commands.Cog.listener()
    async def on_button_click(self, interaction: disnake.MessageInteraction):
        if not interaction.guild:
            return
        elif interaction.component.custom_id == "delete_channel":
            await interaction.channel.delete()  # type: ignore
        elif interaction.component.custom_id == "new_ticket":
            result = await (
                await self.bot.db.execute(
                    """
                    select guild_id, user_or_role_id,
                    category_id, image, title, description
                    from tickets where guild_id = ?
                    """,
                    (interaction.guild.id,),
                )
            ).fetchone()  # type: ignore
            if result:
                (_, user_or_role_id, category_id, image, title, description) = result
                category = interaction.guild.get_channel(category_id)
                if not category:
                    return
                channels = {c.name for c in interaction.guild.get_channel(category_id).text_channels}  # type: ignore
                if f"{interaction.user.name}-{interaction.user.id}".lower() in channels:
                    await interaction.send(
                        embed=Embeds.emb(
                            Embeds.red,
                            "You already have a ticket open!",
                            "Please close the previous ticket to open a new one!",
                        ),
                        ephemeral=True,
                    )
                    return
                channel = await interaction.guild.create_text_channel(
                    f"{interaction.user.name}-{interaction.user.id}",
                    category=category,  # type: ignore
                    overwrites={  # type: ignore
                        interaction.guild.default_role: disnake.PermissionOverwrite(
                            read_messages=False
                        ),
                        interaction.user: disnake.PermissionOverwrite(
                            read_messages=True
                        ),
                        interaction.guild.get_role(
                            user_or_role_id
                        ): disnake.PermissionOverwrite(read_messages=True),
                        interaction.guild.me: disnake.PermissionOverwrite(
                            read_messages=True
                        ),
                    },
                )
                await channel.send(
                    embed=Embeds.emb(Embeds.green, title, description)
                    .set_image(image)
                    .set_footer(
                        text=interaction.guild.name, icon_url=interaction.guild.icon
                    ),
                    components=[delete_channel_button],
                )
                await interaction.send(
                    f"Ticket has been created {channel.mention}", ephemeral=True
                )


def setup(client: commands.Bot):
    client.add_cog(TicketSystem(client))
