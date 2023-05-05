from typing import Union

import disnake
from disnake.ext import commands
from easy_pil import Editor, Font, load_image_async

from utils import Embeds, db

WELCOME_IMG_URL = (
    "https://img.freepik.com/premium-vector/seamless-gold-"
    "hexagon-grid-pattern-black-background-vector_53876-166795.jpg"
)


class Greetings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    async def send_img(
        self,
        channel: disnake.TextChannel,
        member: disnake.Member,
        url: str,
        msg: Union[str, None] = None,
        font: int = 20,
        theme: str = "white",
    ):
        """Sends Manipulated Images"""
        bg_img = Editor(await load_image_async(url)).resize((625, 355), crop=True)
        width, height = bg_img.image.size  # type: ignore

        SIZE = (height // 3, height // 3)
        USER_COORDINATES = ((width // 2) - 50, height // 4)
        HEADING_COORDINATES = (width // 2, USER_COORDINATES[1] + 150)
        SUBTITLE_COORDINATE = (width // 2, HEADING_COORDINATES[1] + 50)
        FONT = font
        THEME = theme

        user_img = await load_image_async(str(member.display_avatar.url))

        user_img = Editor(user_img).resize(SIZE).circle_image()
        poppins = Font.poppins(size=FONT, variant="bold")

        poppins_small = Font.poppins(size=int(FONT) - 5, variant="light")

        bg_img.paste(user_img, USER_COORDINATES)
        bg_img.ellipse(
            USER_COORDINATES, SIZE[0], SIZE[1], outline="black", stroke_width=0
        )

        if msg is None:
            msg = f"Welcome To {member.guild.name}"

        bg_img.text(HEADING_COORDINATES, msg, color=THEME, font=poppins, align="center")
        bg_img.text(
            SUBTITLE_COORDINATE,
            f"{member.name}#{member.discriminator}",
            color=THEME,
            font=poppins_small,
            align="center",
        )

        file = disnake.File(fp=bg_img.image_bytes, filename=f"{member.guild.id}.jpg")

        await channel.send(file=file)
        await channel.send(member.mention, delete_after=3)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        result = db.traffic.find_one({"guild_id": member.guild.id})
        if result is not None:
            try:
                greet_channel_id = result["welcome_channel"]
            except KeyError:
                return
            member_channel = self.bot.get_channel(int(greet_channel_id))
            if member_channel is not None:
                await self.send_img(
                    channel=member_channel,
                    member=member,
                    url=result["welcome_img_url"],
                    theme=result["wlcm_img_txt_theme"],
                    font=result["wlcm_img_txt_font"],
                )

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        result = db.traffic.find_one({"guild_id": member.guild.id})
        if result is not None:
            try:
                member_channel = self.bot.get_channel(result["bye_channel"])
            except KeyError:
                return
            if member_channel is not None:
                await self.send_img(
                    channel=member_channel,
                    member=member,
                    url=result["bye_img_url"],
                    msg="Hoping To See You Soon!",
                    theme=result["bye_img_txt_theme"],
                    font=result["bye_img_txt_font"],
                )

    @commands.slash_command(name="greeter", dm_permission=False)
    async def greeter(self, interaction):
        """Greeter Settings"""
        ...

    @greeter.sub_command(name="plug")
    @commands.check_any(
        commands.is_owner(), commands.has_permissions(manage_guild=True)
    )
    async def slash_set(
        self,
        interaction,
        channel: disnake.TextChannel,
        feature: str = commands.Param(choices=["Welcome Channel", "Goodbye Channel"]),
        img_url: str = WELCOME_IMG_URL,
        font: int = 20,
        theme: str = commands.Param(
            choices=["red", "blue", "green", "black", "white", "yellow"]
        ),
    ):
        """
        Plugs greeter

        Parameters
        ----------
        channel: The channel where to plug greeter
        feature: The greeter to plug
        img_url: The url of the image to use
        font: The font size of the text
        theme: The theme of the text
        """
        await interaction.response.defer(ephemeral=True)
        if feature == "Welcome Channel":
            db.traffic.update_one(
                {"guild_id": interaction.guild.id},
                {
                    "$set": {
                        "guild_id": interaction.guild.id,
                        "guild_name": interaction.guild.name,
                        "welcome_channel": channel.id,
                        "welcome_img_url": img_url,
                        "wlcm_img_txt_font": font,
                        "wlcm_img_txt_theme": theme,
                    }
                },
                upsert=True,
            )
            await interaction.send(
                embed=Embeds.emb(
                    Embeds.green,
                    "Welcome Channel Set Successfully",
                    f"Channel: {channel}",
                ),
                ephemeral=True,
            )
        elif feature == "Goodbye Channel":
            db.traffic.update_one(
                {"guild_id": interaction.guild.id},
                {
                    "$set": {
                        "guild_id": interaction.guild.id,
                        "guild_name": interaction.guild.name,
                        "bye_channel": channel.id,
                        "bye_img_url": img_url,
                        "bye_img_txt_font": font,
                        "bye_img_txt_theme": theme,
                    }
                },
                upsert=True,
            )
            await interaction.send(
                embed=Embeds.emb(
                    Embeds.green,
                    "Goodbye Channel Set Successfully",
                    f"Channel: {channel}",
                ),
                ephemeral=True,
            )

    @greeter.sub_command(
        name="unplug",
        description="Unset's the features of channel in the server",
    )
    @commands.check_any(
        commands.is_owner(), commands.has_permissions(manage_guild=True)
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
            db.traffic.update_one(
                {"guild_id": interaction.guild.id},
                {"$unset": {"welcome_channel": "", "welcome_img_url": ""}},
                upsert=True,
            )
            await interaction.send(
                embed=Embeds.emb(Embeds.red, "Welcome Channel Unset Sucessfully"),
                ephemeral=True,
            )
        elif feature == "Goodbye Channel":
            db.traffic.update_one(
                {"guild_id": interaction.guild.id},
                {"$unset": {"bye_channel": "", "bye_img_url": ""}},
                upsert=True,
            )
            await interaction.send(
                embed=Embeds.emb(Embeds.red, "Goodbye Channel Unset Sucessfully"),
                ephemeral=True,
            )


def setup(client: commands.Bot):
    client.add_cog(Greetings(client))
