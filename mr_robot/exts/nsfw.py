import logging
import random
from textwrap import shorten
from typing import Literal, Set

import disnake
from disnake.ext import commands

from mr_robot.bot import MrRobot
from mr_robot.constants import Client
from mr_robot.utils.helpers import Embeds

logger = logging.getLogger(__name__)
nsfw_api = Client.nsfw_api


class Fun(commands.Cog):
    def __init__(self, client: MrRobot):
        self.bot = client

    @commands.slash_command(name="nsfw", nsfw=True, dm_permission=False)
    @commands.cooldown(1, 10, commands.cooldowns.BucketType.user)
    async def slash_nsfw(
        self,
        interaction,
    ) -> None:
        """
        Shows You Nsfw Content
        """
        if not nsfw_api:
            raise ValueError("Nsfw api is not being initialised")
        await interaction.response.defer()

    async def send_nsfw(
        self,
        interaction: disnake.CommandInteraction,
        platform: Literal["xnxx", "xvideos"],
        search: str,
        amount: int,
    ) -> None:
        """Generic command to fetch content from nsfw_api"""
        try:
            await interaction.send(
                embed=Embeds.emb(
                    Embeds.blue,
                    f"Searching {search}",
                    "Please wait while we search for your content",
                )
            )
            data = await self.bot._request(f"{nsfw_api}/{platform}/{amount}/{search}")
            data = data.get("data")
            for vid in data:
                await interaction.channel.send(
                    embed=(
                        Embeds.emb(
                            Embeds.blue,
                            value=f"""
                            **Name:** {shorten(vid.get("name"), 35, placeholder="...").strip()}
                            **Description:** {shorten(vid.get("description"), 70, placeholder="...").strip()}
                            **Upload Date:** {vid.get("upload_date")}
                            """,
                        )
                    ).set_image(url=vid.get("thumbnail")),
                    components=[
                        disnake.ui.Button(
                            url=vid.get("content_url"),
                            label="Watch Now",
                            emoji="📺",
                            style=disnake.ButtonStyle.link,
                        ),
                    ],
                )
            await interaction.edit_original_response(
                embed=Embeds.emb(
                    Embeds.green,
                    "Search Completed",
                    f"Showing {len(data)} results for `{search}`",
                )
            )
        except Exception:
            logger.error(f"Error in {platform.capitalize()}", exc_info=True)
            raise commands.CommandError("Api Error")

    @commands.is_nsfw()
    @slash_nsfw.sub_command(name="xnxx")
    async def xnxx(
        self,
        interaction: disnake.CommandInteraction,
        search: str = "nsfw",
        amount: commands.Range[int, 1, 5] = 1,
    ):
        """
        Loads content from xnxx.com

        Parameters
        ----------
        search: What to search?
        amount: How much?
        """
        await self.send_nsfw(interaction, "xnxx", search, amount)

    @xnxx.autocomplete("search")
    async def xnxx_autocomplete(
        self, interaction: disnake.GuildCommandInteraction, name: str
    ):
        data = await self.bot._request(f"{nsfw_api}/suggestion/xnxx/{name or "nsfw"}")
        return {keywords for keywords in data.get("data", [])}

    @commands.is_nsfw()
    @slash_nsfw.sub_command(name="xvideos")
    async def xvideos(
        self,
        interaction: disnake.CommandInteraction,
        search: str = "nsfw",
        amount: commands.Range[int, 1, 5] = 1,
    ):
        """
        Loads content from xvideos.com

        Parameters
        ----------
        search: What to search?
        amount: How much?
        """
        await self.send_nsfw(interaction, "xvideos", search, amount)

    @xvideos.autocomplete("search")
    async def xvideos_autocomplete(self, _, name: str):
        data = await self.bot._request(
            f"{nsfw_api}/suggestion/xvideos/{name or "nsfw"}"
        )
        return {keywords for keywords in data.get("data", [])}

    @slash_nsfw.sub_command(name="redtube")
    async def redtube(
        self,
        interaction: disnake.CommandInteraction,
        search: str = "nsfw",
        amount: commands.Range[int, 1, 5] = 1,
    ):
        """
        Loads content from redtube.com

        Parameters
        ----------
        search: What to search?
        amount: How much?
        """
        try:
            await interaction.send(
                embed=Embeds.emb(
                    Embeds.red,
                    f"Searching {search}",
                    "Please wait while we search for your content",
                )
            )
            data = await self.bot._request(f"{nsfw_api}/redtube/{amount}/{search}")
            data = data.get("data")
            for vid in data:
                await interaction.channel.send(
                    embed=(
                        Embeds.emb(
                            Embeds.blue,
                            value=f"""
                            **Name:** {shorten(vid.get("title"), 35, placeholder="...").strip()}
                            **Duration:** {vid.get("duration")}
                            """,
                        )
                    ).set_image(url=vid.get("default_thumb")),
                    components=[
                        disnake.ui.Button(
                            url=vid.get("url"),
                            label="Watch Now",
                            emoji="📺",
                            style=disnake.ButtonStyle.link,
                        ),
                    ],
                )
            await interaction.edit_original_response(
                embed=Embeds.emb(
                    Embeds.green,
                    "Search Completed",
                    f"Showing {len(data)} results for `{search}`",
                )
            )
        except Exception:
            logger.error("Error in Redtube", exc_info=True)
            raise commands.CommandError("Api Error")

    @slash_nsfw.sub_command(name="reddit")
    async def reddit(
        self,
        interaction: disnake.CommandInteraction,
        search: str,
        amount: commands.Range[int, 1, 5] = 1,
    ) -> None:
        """
        Loads content from reddit.com

        Parameters
        ----------
        search: What to search?
        amount: How much?
        """
        try:
            await interaction.send(
                embed=Embeds.emb(
                    Embeds.blue,
                    f"Searching {search}",
                    "Please wait while we search for your content",
                )
            )
            URL = (
                f"https://www.reddit.com/r/{search}.json?raw_json=1&limit=100&"
                f"include_over_18=True&type=link"
            )
            if search not in (await self.reddit_autocomp(interaction, name=search)):
                URL = (
                    "https://www.reddit.com/r/memes/search.json"
                    "?raw_json=1&limit=100&include_over_18=True&type=link"
                    f"&q={search}"
                )
            data = await self.bot._request(URL)
            links_list = data["data"]["children"]
            if not links_list:
                await interaction.send(
                    "No Results Found, Try something else :face_holding_back_tears:",
                    ephemeral=True,
                )
            random.shuffle(links_list)
            urls = set()
            for count, data in enumerate(links_list):
                if count >= amount:
                    break

                elif data["data"]["is_video"]:
                    url = data["data"]["media"]["reddit_video"]["fallback_url"].replace(
                        "?source=fallback", ""
                    )

                elif data["data"].get("is_gallery"):
                    url = str(
                        "\n".join({data for data in data["data"]["media_metadata"]})
                    )

                elif "redgifs.com" in data["data"]["url"]:
                    url = data["data"]["url_overridden_by_dest"]

                elif data["data"]["url"].endswith(
                    (
                        ".gifv",
                        ".mp4",
                        ".webm",
                        ".gif",
                        ".png",
                        ".jpg",
                        ".jpeg",
                        ".mov",
                        ".mkv",
                        "?source=fallback",
                    )
                ):
                    url = data["data"]["url_overridden_by_dest"].replace(
                        "?source=fallback", ""
                    )
                else:
                    amount += 1
                    continue

                if not url.startswith("http"):
                    amount += 1
                    continue

                urls.add(url)
            if not urls:
                await interaction.edit_original_response(
                    embed=Embeds.emb(
                        Embeds.red,
                        f"No Result Found for `{search}`",
                        "Try something else :face_holding_back_tears:",
                    )
                )
            else:
                for url in urls:
                    await interaction.channel.send(url)
                await interaction.edit_original_response(
                    embed=Embeds.emb(
                        Embeds.green,
                        "Search Completed",
                        f"Showing {len(urls)} results for `{search}`",
                    )
                )
        except Exception:
            logger.error("Error in Reddit", exc_info=True)
            await interaction.edit_original_response(
                embed=Embeds.emb(
                    Embeds.red,
                    "Unable to find anything",
                    "Try searching someting else!",
                ),
            )

    @reddit.autocomplete("search")
    async def reddit_autocomp(self, _, name: str) -> Set[str] | None:
        name = name.lower()
        url = (
            "https://www.reddit.com/api/search_reddit_names.json?"
            f"query={name or "nsfw"}&include_over_18=True"
        )
        data = await self.bot._request(url)
        return set(name for name in data["names"])

    @commands.slash_command(name="meme", dm_permission=False)
    async def slash_meme(self, interaction, amount: int = 1):
        """
        Shows You Memes

        Parameters
        ----------
        amount: Amount of memes you want to see
        """
        await self.reddit(interaction, search="meme", amount=amount)


def setup(client: MrRobot):
    client.add_cog(Fun(client))
