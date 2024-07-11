import asyncio
import functools
import logging
from enum import Enum
from io import BytesIO
from typing import Optional

import disnake
import sqlalchemy
from aiocache import cached
from disnake.ext import commands
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError

from mr_robot.bot import MrRobot
from mr_robot.database.greeter import Greeter
from mr_robot.utils.helpers import Embeds
from mr_robot.utils.messages import DeleteButton

WELCOME_IMG_URL = (
    "https://upload.wikimedia.org/wikipedia/commons/8/89/HD_transparent_picture.png"
)
WELCOME = "Welcome"
GOODBYE = "Goodbye"

logger = logging.getLogger(__name__)


class FontDir(Enum):
    """Font Directory"""

    Branda = "mr_robot/fonts/Branda.ttf"
    ChrustyRock = "mr_robot/fonts/ChrustyRock.ttf"
    Debrosee = "mr_robot/fonts/Debrosee.ttf"
    ShortBaby = "mr_robot/fonts/ShortBaby.ttf"


class Greetings(commands.Cog):
    def __init__(self, bot: MrRobot):
        self.bot = bot
        self.loop = asyncio.get_running_loop()

    @cached(60 * 60 * 24)
    async def __request_bg(self, url: str) -> BytesIO:
        buffer = BytesIO()
        async with self.bot.http_session.stream("GET", url=url) as resp:
            logger.debug(f"Requesting background: {url}")
            async for data in resp.aiter_bytes():
                buffer.write(data)
        return buffer

    async def __request_usr(self, url: str):
        buffer = BytesIO()
        async with self.bot.http_session.stream("GET", url=url) as resp:
            logger.debug(f"Requesting background: {url}")
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
        member : Member who joined/left
        message : Message to send
        font_style : Font style
        theme : Theme color
        outline : Outline width
        usr_img : URL of user image
        bg_img : URL of background image
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
        font = ImageFont.truetype(font_style.value, 40)
        txt = "Welcome" if welcome else "Goodbye"
        draw.text(
            (width / 2 + 10, height // 2 + 100 - 50),
            txt,
            font=font,
            fill=theme,
            align="center",
            anchor="mm",
        )
        txt = member.name
        draw.text(
            (width / 2 + 10, height // 2 + 100 - 10),
            txt,
            font=font,
            fill=theme,
            align="center",
            anchor="mm",
        )
        if message:
            font = ImageFont.truetype(font_style.value, 22)
            draw.text(
                (width / 2 + 10, height // 2 + 140),
                message,
                font=font,
                fill=theme,
                align="center",
                anchor="mm",
            )

        file = BytesIO()
        bg.save(file, "png")
        file.seek(0)
        return disnake.File(fp=file, filename="image.png")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        async with self.bot.db.begin() as session:
            result = await session.scalars(
                sqlalchemy.select(Greeter).where(Greeter.guild_id == member.guild.id)
            )
            greeter_db = result.one_or_none()

        if (
            greeter_db
            and greeter_db.wlcm_channel
            and (member_channel := self.bot.get_channel(greeter_db.wlcm_channel))
        ):
            bg_img = await self.__request_bg(greeter_db.wlcm_image)
            usr_img = await self.__request_usr(member.display_avatar.with_size(128).url)
            gen_img = functools.partial(
                self.send_img,
                member=member,
                usr_img=usr_img,
                bg_img=bg_img,
                message=greeter_db.wlcm_msg,
                font_style=FontDir(greeter_db.wlcm_fontstyle),
                theme=greeter_db.wlcm_theme or "",
                outline=greeter_db.wlcm_outline or 0,
            )
            img_file = await self.loop.run_in_executor(None, gen_img)
            await member_channel.send(file=img_file)  # type: ignore[reportAttributeAccessIssue]
            await member_channel.send(member.mention, delete_after=3)  # type: ignore[reportAttributeAccessIssue]

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        async with self.bot.db.begin() as session:
            result = await session.scalars(
                sqlalchemy.select(Greeter).where(Greeter.guild_id == member.guild.id)
            )
            greeter_db = result.one_or_none()

        if (
            greeter_db
            and greeter_db.bye_channel
            and (member_channel := self.bot.get_channel(greeter_db.bye_channel))
        ):
            bg_img = await self.__request_bg(greeter_db.bye_image)
            usr_img = await self.__request_usr(member.display_avatar.with_size(128).url)
            gen_img = functools.partial(
                self.send_img,
                member=member,
                usr_img=usr_img,
                bg_img=bg_img,
                message=greeter_db.bye_msg,
                font_style=FontDir(greeter_db.bye_fontstyle),
                theme=greeter_db.bye_theme or "",
                outline=greeter_db.bye_outline or 0,
                welcome=False,
            )
            img_file = await self.loop.run_in_executor(None, gen_img)
            await member_channel.send(file=img_file)  # type: ignore[reportAttributeAccessIssue]

    @commands.slash_command(name="greeter", dm_permission=False)
    async def greeter(self, _):
        """Greeter Settings"""
        ...

    @greeter.sub_command(name="plug")
    @commands.has_permissions(manage_guild=True)
    async def slash_set(
        self,
        interaction: disnake.GuildCommandInteraction,
        channel: disnake.TextChannel,
        font_style: FontDir = FontDir.ShortBaby,
        greeter_type: str = commands.Param(choices=[WELCOME, GOODBYE]),
        img_url: str = WELCOME_IMG_URL,
        theme: str = commands.Param(
            default="white",
            choices=["red", "blue", "green", "black", "white", "yellow"],
        ),
        outline: commands.Range[int, 0, 5] = 4,
        message: Optional[str] = None,
    ):
        """
        Plugs greeter

        Parameters
        ----------
        channel: The channel where to plug greeter
        greeter_type: The greeter type to plug
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
                welcome=(False if greeter_type == GOODBYE else True),
            )
            img_file = await self.loop.run_in_executor(None, gen_img)
            await interaction.send(
                "This is how it will look like:",
                file=img_file,
                components=[DeleteButton(interaction.author)],
            )

        except UnidentifiedImageError:
            raise commands.BadArgument("Invalid Image URL")
        if greeter_type == WELCOME:
            sql_query = Greeter(
                id=interaction.guild.id,
                guild_id=interaction.guild.id,
                wlcm_channel=channel.id,
                wlcm_image=img_url,
                wlcm_fontstyle=font_style.value,
                wlcm_outline=outline,
                wlcm_msg=message,
                wlcm_theme=theme,
            )

        elif greeter_type == GOODBYE:
            sql_query = Greeter(
                id=interaction.guild.id,
                guild_id=interaction.guild.id,
                bye_channel=channel.id,
                bye_image=img_url,
                bye_fontstyle=font_style.value,
                bye_outline=outline,
                bye_msg=message,
                bye_theme=theme,
            )
        else:
            raise commands.CommandError("This should never reach here")

        async with self.bot.db.begin() as session:
            await session.merge(sql_query)
            await session.commit()

        await interaction.followup.send(
            embed=Embeds.emb(
                Embeds.green,
                (
                    "Goodbye channel set successfully"
                    if greeter_type == GOODBYE
                    else "Welcome channel set successfully"
                ),
                f"Channel: {channel.mention}",
            ),
            ephemeral=True,
        )

    @greeter.sub_command(
        name="unplug",
        description="Unset's the greeter of channel in the server",
    )
    @commands.has_permissions(manage_guild=True)
    async def slash_unset(
        self,
        interaction,
        greeter_type: str = commands.Param(choices=[WELCOME, GOODBYE]),
    ):
        """
        Unplugs greeter

        Parameters
        ----------
        greeter_type: Greeter type to unplug
        """
        await interaction.response.defer(ephemeral=True)
        if greeter_type == WELCOME:
            sql_query = Greeter(
                id=interaction.guild.id,
                guild_id=interaction.guild.id,
                wlcm_channel=None,
                wlcm_image=None,
                wlcm_fontstyle=None,
                wlcm_outline=None,
                wlcm_msg=None,
                wlcm_theme=None,
            )

        elif greeter_type == GOODBYE:
            sql_query = Greeter(
                id=interaction.guild.id,
                guild_id=interaction.guild.id,
                bye_channel=None,
                bye_image=None,
                bye_fontstyle=None,
                bye_outline=None,
                bye_msg=None,
                bye_theme=None,
            )
        else:
            raise commands.CommandError("This should never reach here")

        async with self.bot.db.begin() as session:
            await session.merge(sql_query)
            await session.commit()

        await interaction.followup.send(
            embed=Embeds.emb(
                Embeds.green,
                (
                    "Goodbye channel unset successfully"
                    if greeter_type == GOODBYE
                    else "Welcome channel unset successfully"
                ),
                f"Channel: {interaction.channel.mention}",
            ),
            ephemeral=True,
        )


def setup(client: MrRobot):
    client.add_cog(Greetings(client))
