import asyncio
import functools
import logging
from enum import Enum
from io import BytesIO
from typing import Optional

import disnake
from aiocache import cached
from disnake.ext import commands
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError

from mr_robot.bot import MrRobot
from mr_robot.utils.helpers import Embeds, delete_button

WELCOME_IMG_URL = (
    "https://upload.wikimedia.org/wikipedia/commons/8/89/HD_transparent_picture.png"
)

logger = logging.getLogger(__name__)


class FontDir(Enum):
    """Font Directory"""

    Branda = "../fonts/Branda.ttf"
    ChrustyRock = "../fonts/ChrustyRock.ttf"
    Debrosee = "../fonts/Debrosee.ttf"
    ShortBaby = "../fonts/ShortBaby.ttf"


class Greetings(commands.Cog):
    def __init__(self, bot: MrRobot):
        self.bot = bot
        self.loop = asyncio.get_running_loop()

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        await self.bot.db.execute(
            """
                CREATE TABLE IF NOT EXISTS greeter (
                    guild_id bigint primary key,
                    wlcm_channel bigint,
                    wlcm_img text,
                    wlcm_theme text,
                    wlcm_font_style text,
                    wlcm_outline tinyint,
                    wlcm_message text,
                    bye_channel bigint,
                    bye_img text,
                    bye_theme text,
                    bye_font_style text,
                    bye_outline tinyint,
                    bye_message text
                    )
                """
        )
        await self.bot.db.commit()

    @cached(60 * 60 * 24)
    async def __request_bg(self, url: str) -> BytesIO:
        buffer = BytesIO()
        async with self.bot.session.stream("GET", url=url) as resp:
            logger.info(f"Requesting background: {url}")
            async for data in resp.aiter_bytes():
                buffer.write(data)
        return buffer

    async def __request_usr(self, url: str):
        buffer = BytesIO()
        async with self.bot.session.stream("GET", url=url) as resp:
            logger.info(f"Requesting background: {url}")
            async for data in resp.aiter_bytes():
                buffer.write(data)
        return buffer

    def send_img(
        self,
        member: disnake.Member,
        message: Optional[str],
        font_style: FontDir,
        theme: str,
        outline: int,
        usr_img: BytesIO,
        bg_img: BytesIO,
        welcome: bool = True,
    ) -> disnake.File:
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
        bg = Image.open(bg_img).convert("RGBA")
        usr = Image.open(usr_img).convert("RGBA")
        usr = usr.resize((128, 128), Image.Resampling.LANCZOS)
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
        font = ImageFont.truetype(font_style, 40)
        txt = "Welcome" if welcome else "Goodbye"
        w, h = draw.textlength(txt, font=font, direction="ltr")
        draw.text(
            ((width - w) / 2 + 10, (height - h) // 2 + 100 - 50),
            txt,
            font=font,
            fill=theme,
            align="center",
        )
        txt = member.name
        w, h = draw.textlength(txt, font=font, direction="ltr")
        draw.text(
            ((width - w) / 2 + 10, (height - h) // 2 + 100 - 10),
            txt,
            font=font,
            fill=theme,
            align="center",
        )
        if message:
            font = ImageFont.truetype(font_style, 22)
            w, h = draw.textlength(message, font=font, direction="ltr")
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
        return disnake.File(fp=file, filename="image.png")

    @commands.Cog.listener()
    async def on_member_join(self, member):
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
                bg_img = await self.__request_bg(wlcm_img)
                usr_img = await self.__request_usr(
                    member.display_avatar.with_size(128).url
                )
                gen_img = functools.partial(
                    self.send_img,
                    member=member,
                    usr_img=usr_img,
                    bg_img=bg_img,
                    message=wlcm_message,
                    font_style=wlcm_font_style,
                    theme=wlcm_theme,
                    outline=wlcm_outline,
                )
                img_file = await self.loop.run_in_executor(None, gen_img)
                await member_channel.send(file=img_file)  # type: ignore[reportAttributeAccessIssue]
                await member_channel.send(member.mention, delete_after=3)  # type: ignore[reportAttributeAccessIssue]

    @commands.Cog.listener()
    async def on_member_remove(self, member):
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
                bg_img = await self.__request_bg(bye_img)
                usr_img = await self.__request_usr(
                    member.display_avatar.with_size(128).url
                )
                gen_img = functools.partial(
                    self.send_img,
                    member=member,
                    usr_img=usr_img,
                    bg_img=bg_img,
                    message=bye_message,
                    font_style=bye_font_style,
                    theme=bye_theme,
                    outline=bye_outline,
                )
                img_file = await self.loop.run_in_executor(None, gen_img)
                await member_channel.send(file=img_file)  # type: ignore[reportAttributeAccessIssue]

    @commands.slash_command(name="greeter", dm_permission=False)
    async def greeter(self, interaction):
        """Greeter Settings"""
        ...

    @greeter.sub_command(name="plug")
    @commands.check_any(
        commands.is_owner(), commands.has_permissions(manage_guild=True)  # type: ignore[reportArgumentType]
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
        outline: commands.Range[int, 0, 5] = 4,
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
        try:
            bg_img = await self.__request_bg(img_url)
            usr_img = await self.__request_usr(
                interaction.author.display_avatar.with_size(128).url
            )
            gen_img = functools.partial(
                self.send_img,
                member=interaction.author,
                usr_img=usr_img,
                bg_img=bg_img,
                message=message,
                font_style=font_style,
                theme=theme,
                outline=outline,
            )
            img_file = await self.loop.run_in_executor(None, gen_img)
            await interaction.send(
                "This is how it will look like:",
                file=img_file,
                components=[delete_button],
            )

        except UnidentifiedImageError:
            raise commands.BadArgument("Invalid Image URL")
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
                    f"Channel: {channel.mention}",
                ),
                ephemeral=True,
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
                    f"Channel: {channel.mention}",
                ),
                ephemeral=True,
            )
        await self.bot.db.commit()

    @greeter.sub_command(
        name="unplug",
        description="Unset's the features of channel in the server",
    )
    @commands.check_any(
        commands.is_owner(), commands.has_permissions(manage_guild=True)  # type: ignore[reportArgumentType]
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


def setup(client: MrRobot):
    client.add_cog(Greetings(client))
