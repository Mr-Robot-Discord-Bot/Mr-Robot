import logging
from enum import Enum
from io import BytesIO
from typing import Optional

import disnake
from aiocache import cached
from disnake.ext import commands
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError

from utils import Embeds, delete_button

WELCOME_IMG_URL = (
    "https://upload.wikimedia.org/wikipedia/commons/8/89/HD_transparent_picture.png"
)

logger = logging.getLogger(__name__)


class FontDir(Enum):
    """Font Directory"""

    Branda = "fonts/Branda.ttf"
    ChrustyRock = "fonts/ChrustyRock.ttf"
    Debrosee = "fonts/Debrosee.ttf"
    ShortBaby = "fonts/ShortBaby.ttf"


class Greetings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        logger.info("Greetings Cog Loaded")

    async def db_init(self) -> None:
        """Initializes the database"""
        await self.bot.db.execute(
            """
                CREATE TABLE IF NOT EXISTS greeter (
                    guild_id int,
                    wlcm_channel int,
                    wlcm_img string,
                    wlcm_theme string,
                    wlcm_font_style string,
                    wlcm_outline int,
                    wlcm_message string,
                    bye_channel int,
                    bye_img string,
                    bye_theme string,
                    bye_font_style string,
                    bye_outline int,
                    bye_message string
                )
                """
        )
        await self.bot.db.commit()

    async def send_img(
        self,
        channel: disnake.TextChannel,
        member: disnake.Member,
        img_url: str,
        message: Optional[str],
        font_style: FontDir,
        theme: str,
        outline: int,
        welcome: bool = True,
    ):
        """
        Sends a welcome/goodbye image to the channel

        Parameters
        ----------
        channel : Channel to send the image
        member : Member who joined/left
        img_url : URL of the image
        message : Message to send
        font_style : Font style
        theme : Theme color
        outline : Outline width
        welcome : Whether to send welcome or goodbye image
        """
        async with self.bot.session.get(
            url=member.display_avatar.with_size(128).url
        ) as resp:
            usr_img = BytesIO(await resp.read())

        @cached(60 * 60 * 24)
        async def __request(url: str):
            async with self.bot.session.get(url=url) as resp:
                return BytesIO(await resp.read())

        bg = Image.open(await __request(img_url)).convert("RGBA")
        usr = Image.open(usr_img).convert("RGBA")
        usr = usr.resize((128, 128), Image.ANTIALIAS)
        background = Image.new("RGBA", size=usr.size, color=(255, 255, 255, 0))
        holder = Image.new("RGBA", size=usr.size, color=(255, 255, 255, 0))
        mask = Image.new("RGBA", size=usr.size, color=(255, 255, 255, 0))
        mask_draw = ImageDraw.Draw(mask)
        ellipse_size = tuple(i - 1 for i in usr.size)
        mask_draw.ellipse((0, 0) + ellipse_size, fill=theme)
        holder.paste(usr, (0, 0))
        usr = Image.composite(holder, background, mask)

        bg = bg.crop((0, 0, 625, 355))
        width, height = bg.size
        bg.paste(usr, ((width // 2) - 50, height // 4 - 25), usr)

        draw = ImageDraw.Draw(bg)
        draw.ellipse(
            (
                width // 2 - 50,
                height // 4 - 25,
                width // 2 + 78,
                height // 4 - 25 + 128,
            ),
            outline=theme,
            width=outline,
        )
        font = ImageFont.truetype(font_style, 40)  # type: ignore
        txt = "Welcome" if welcome else "Goodbye"
        w, h = draw.textsize(txt, font=font, direction="ltr")
        draw.text(
            ((width - w) / 2 + 10, (height - h) // 2 + 100 - 50),
            txt,
            font=font,
            fill=theme,
            align="center",
        )
        txt = member.name
        w, h = draw.textsize(txt, font=font, direction="ltr")
        draw.text(
            ((width - w) / 2 + 10, (height - h) // 2 + 100 - 10),
            txt,
            font=font,
            fill=theme,
            align="center",
        )
        if message:
            font = ImageFont.truetype(font_style, 22)  # type: ignore
            w, h = draw.textsize(message, font=font, direction="ltr")
            draw.text(
                ((width - w) / 2 + 10, (height - h) // 2 + 140),
                message,
                font=font,
                fill=theme,
                align="center",
            )

        file = BytesIO()
        bg.save(file, "png")
        file.seek(0)
        file = disnake.File(fp=file, filename="image.png")
        await channel.send(file=file)
        await channel.send(member.mention, delete_after=3)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        await self.db_init()
        result = await (
            await self.bot.db.execute(
                """
            SELECT wlcm_img, wlcm_theme, wlcm_font_style,
            wlcm_outline, wlcm_message, wlcm_channel
            FROM greeter WHERE guild_id = ?
            """,
                (member.guild.id,),
            )
        ).fetchone()
        if result:
            (
                wlcm_img,
                wlcm_theme,
                wlcm_font_style,
                wlcm_outline,
                wlcm_message,
                wlcm_channel,
            ) = result
            if not wlcm_channel:
                return
            member_channel = self.bot.get_channel(wlcm_channel)
            if member_channel:
                await self.send_img(
                    channel=member_channel,
                    member=member,
                    img_url=wlcm_img,
                    message=wlcm_message,
                    font_style=wlcm_font_style,
                    theme=wlcm_theme,
                    outline=wlcm_outline,
                )

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        await self.db_init()
        result = await (
            await self.bot.db.execute(
                """
            SELECT bye_img, bye_theme, bye_font_style,
            bye_outline, bye_message, bye_channel
            FROM greeter WHERE guild_id = ?
            """,
                (member.guild.id,),
            )
        ).fetchone()
        if result:
            (
                bye_img,
                bye_theme,
                bye_font_style,
                bye_outline,
                bye_message,
                bye_channel,
            ) = result
            if not bye_channel:
                return
            member_channel = self.bot.get_channel(bye_channel)
            if member_channel:
                await self.send_img(
                    channel=member_channel,
                    member=member,
                    img_url=bye_img,
                    message=bye_message,
                    font_style=bye_font_style,
                    theme=bye_theme,
                    outline=bye_outline,
                    welcome=False,
                )

    @commands.slash_command(name="greeter", dm_permission=False)
    async def greeter(self, interaction):
        """Greeter Settings"""
        ...

    @greeter.sub_command(name="plug")
    @commands.check_any(
        commands.is_owner(), commands.has_permissions(manage_guild=True)  # type: ignore
    )
    async def slash_set(
        self,
        interaction: disnake.GuildCommandInteraction,
        channel: disnake.TextChannel,
        font_style: FontDir,
        feature: str = commands.Param(choices=["Welcome Channel", "Goodbye Channel"]),
        img_url: str = WELCOME_IMG_URL,
        theme: str = commands.Param(
            choices=["red", "blue", "green", "black", "white", "yellow"]
        ),
        outline: commands.Range[0, 5] = 4,  # type: ignore
        message: Optional[str] = None,
    ):
        """
        Plugs greeter

        Parameters
        ----------
        channel: The channel where to plug greeter
        feature: The greeter to plug
        img_url: The url of the image to use
        font_style: The font style to use
        theme: The theme of the text
        outline: The outline of the text
        message: The message to send
        """
        await self.db_init()
        try:
            await interaction.send("This is how it will look like:")
            await self.send_img(
                channel=interaction.channel,  # type: ignore
                member=interaction.author,
                img_url=img_url,
                message=message,
                font_style=font_style,  # type: ignore
                theme=theme,
                outline=outline,  # type: ignore
                welcome=feature == "Welcome Channel",
            )
        except UnidentifiedImageError:
            await interaction.send(content="Invalid Image URL")
            return
        if feature == "Welcome Channel":
            if await (
                await self.bot.db.execute(
                    "SELECT wlcm_channel FROM greeter WHERE guild_id = ?",
                    (interaction.guild.id,),
                )
            ).fetchone():
                await self.bot.db.execute(
                    """
                        UPDATE greeter SET wlcm_channel = ?,
                        wlcm_img = ?, wlcm_font_style = ?,
                        wlcm_outline = ?, wlcm_message = ?,
                        wlcm_theme = ? WHERE guild_id = ?
                        """,
                    (
                        channel.id,
                        img_url,
                        font_style,
                        outline,
                        message,
                        theme,
                        interaction.guild.id,
                    ),
                )
            else:
                await self.bot.db.execute(
                    """
                    INSERT INTO greeter (guild_id, wlcm_channel,
                    wlcm_img, wlcm_font_style, wlcm_outline,
                    wlcm_message, wlcm_theme)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        interaction.guild.id,
                        channel.id,
                        img_url,
                        font_style,
                        outline,
                        message,
                        theme,
                    ),
                )

            await interaction.followup.send(
                embed=Embeds.emb(
                    Embeds.green,
                    "Welcome Channel Set Successfully",
                    f"Channel: {channel}",
                ),
                components=[delete_button],
            )
        elif feature == "Goodbye Channel":
            if await (
                await self.bot.db.execute(
                    "SELECT wlcm_channel FROM greeter WHERE guild_id = ?",
                    (interaction.guild.id,),
                )
            ).fetchone():
                await self.bot.db.execute(
                    """
                        UPDATE greeter SET bye_channel = ?,
                        bye_img = ?, bye_font_style = ?,
                        bye_outline = ?, bye_message = ?,
                        bye_theme = ? WHERE guild_id = ?
                        """,
                    (
                        channel.id,
                        img_url,
                        font_style,
                        outline,
                        message,
                        theme,
                        interaction.guild.id,
                    ),
                )
            else:
                await self.bot.db.execute(
                    """
                    INSERT INTO greeter (guild_id, bye_channel,
                    bye_img, bye_font_style, bye_outline,
                    bye_message, bye_theme)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        interaction.guild.id,
                        channel.id,
                        img_url,
                        font_style,
                        outline,
                        message,
                        theme,
                    ),
                )

            await interaction.followup.send(
                embed=Embeds.emb(
                    Embeds.green,
                    "Goodbye Channel Set Successfully",
                    f"Channel: {channel}",
                ),
                components=[delete_button],
            )
        await self.bot.db.commit()

    @greeter.sub_command(
        name="unplug",
        description="Unset's the features of channel in the server",
    )
    @commands.check_any(
        commands.is_owner(), commands.has_permissions(manage_guild=True)  # type: ignore
    )
    async def slash_unset(
        self,
        interaction,
        feature: str = commands.Param(choices=["Welcome Channel", "Goodbye Channel"]),
    ):
        """
        Unplugs greeter

        Parameters
        ----------
        greeter: Greeter to unplug
        """
        await self.db_init()
        await interaction.response.defer(ephemeral=True)
        if feature == "Welcome Channel":
            if await (
                await self.bot.db.execute(
                    "SELECT wlcm_channel FROM greeter WHERE guild_id = ?",
                    (interaction.guild.id,),
                )
            ).fetchone():
                await self.bot.db.execute(
                    "UPDATE greeter SET wlcm_channel = NULL WHERE guild_id = ?",
                    (interaction.guild.id,),
                )

            await interaction.send(
                embed=Embeds.emb(Embeds.red, "Welcome Channel Unset Sucessfully"),
                ephemeral=True,
            )
        elif feature == "Goodbye Channel":
            if await (
                await self.bot.db.execute(
                    "SELECT bye_channel FROM greeter WHERE guild_id = ?",
                    (interaction.guild.id,),
                )
            ).fetchone():
                await self.bot.db.execute(
                    "UPDATE greeter SET bye_channel = NULL WHERE guild_id = ?",
                    (interaction.guild.id,),
                )

            await interaction.send(
                embed=Embeds.emb(Embeds.red, "Goodbye Channel Unset Sucessfully"),
                ephemeral=True,
            )
        await self.bot.db.commit()


def setup(client: commands.Bot):
    client.add_cog(Greetings(client))
