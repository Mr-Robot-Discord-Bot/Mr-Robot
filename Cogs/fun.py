import logging
import os
import random
from textwrap import shorten
from typing import Set, Union

import disnake
from disnake.ext import commands

from bot import MrRobot
from utils import Embeds, url_button_builder

logger = logging.getLogger(__name__)
nsfw_api = os.getenv("NSFW_API")


# class AdultScrapper:
#     """
#     Scraps Adult Content from Xnxx and Xvideos
#     """

#     def __init__(self, base_url: str, session: httpx.AsyncClient):
#         self.session = session
#         self.base_url = base_url

#     @cached(ttl=60 * 60 * 12)
#     async def _get_html(self, url: str) -> HTMLParser:
#         resp = await self.session.get(url, headers={"User-Agent": "Magic Browser"})
#         return HTMLParser(resp.text)

#     @cached(ttl=60 * 60 * 12)
#     async def extract_videos(self, url: str) -> Dict:
#         """
#         Extracts Video Data from Xnxx and Xvideos

#         Parameters
#         ----------
#         url: Url of the video
#         """
#         dom = await self._get_html(url=url)
#         data = dom.css_first('script[type="application/ld+json"]').text()
#         data = dict(eval(data))
#         parsed_date = datetime.strptime(
#             data.get("uploadDate", "0000-00-00T00:00:00+00:00"), "%Y-%m-%dT%H:%M:%S%z"
#         )
#         payload = {
#             "thumbnail": data.get("thumbnailUrl", [])[0],
#             "upload_date": parsed_date.strftime("%Y-%m-%d %H:%M:%S"),
#             "name": data.get("name"),
#             "description": data.get("description", "").strip(),
#             "content_url": data.get("contentUrl"),
#         }
#         return payload

#     async def get_link(self, search: str, amount: int, xvideos: bool) -> Set[str]:
#         """
#         Gets the link of the video

#         Parameters
#         ----------
#         search: What to search?
#         xvideos: Search on xvideos or xnxx?
#         """
#         search_payload = (
#             f"https://www.xvideos.com/?k={search}&top"
#             if xvideos
#             else f"https://www.xnxx.tv/search/{search}?top"
#         )
#         dom = await self._get_html(url=search_payload)
#         dom = dom.css_first("div.mozaique.cust-nb-cols").css("div.thumb")
#         random.shuffle(dom)
#         data: Generator = (
#             f'{self.base_url}{link.css_first("a").attrs.get("href")}' for link in dom
#         )
#         return {next(data) for _ in range(amount)}

#     async def send_video(self, search: str, amount: int, xvideos: bool = False) -> List:
#         """
#         Sends the video

#         Parameters
#         ----------
#         search: What to search?
#         amount: How much?
#         xvideos: Search on xvideos or xnxx?
#         """
#         links = await self.get_link(search=search, amount=amount, xvideos=xvideos)
#         return [await self.extract_videos(url=link) for link in links]


class Fun(commands.Cog):
    def __init__(self, client: MrRobot):
        self.bot = client
        logger.info("Fun Cog Loaded")

    @commands.slash_command(name="nsfw", nsfw=True, dm_permission=False)
    async def slash_nsfw(
        self,
        interaction,
    ):
        """
        Shows You Nsfw Content
        """
        await interaction.response.defer()

    @commands.is_nsfw()
    @slash_nsfw.sub_command(name="xnxx")
    async def xnxx(
        self,
        interaction: disnake.CommandInteraction,
        search: str = "porn",
        amount: commands.Range[1, 10] = 1,  # type: ignore
    ):
        """
        Loads content from xnxx.com

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
            data = await self.bot._request(f"{nsfw_api}/xnxx/{amount}/{search}")
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
                        url_button_builder(
                            url=vid.get("content_url"), label="Watch Now", emoji="📺"
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
            logger.error("Error in Xnxx", exc_info=True)
            await interaction.edit_original_response(
                embed=Embeds.emb(
                    Embeds.red,
                    "Api Error",
                    "Please try again later :slight_frown:",
                ),
            )

    @xnxx.autocomplete("search")
    async def xnxx_autocomplete(
        self, interaction: disnake.GuildCommandInteraction, name: str
    ):
        data = await self.bot._request(f"{nsfw_api}/suggestion/xnxx/{name or 'porn'}")
        return {keywords for keywords in data.json().get("data", [])}

    @commands.is_nsfw()
    @slash_nsfw.sub_command(name="xvideos")
    async def xvideos(
        self,
        interaction: disnake.CommandInteraction,
        search: str = "porn",
        amount: commands.Range[1, 10] = 1,  # type: ignore
    ):
        """
        Loads content from xvideos.com

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
            data = await self.bot._request(f"{nsfw_api}/xvideos/{amount}/{search}")
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
                        url_button_builder(
                            url=vid.get("content_url"), label="Watch Now", emoji="📺"
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
            logger.error("Error in Xvideos", exc_info=True)
            await interaction.edit_original_response(
                embed=Embeds.emb(
                    Embeds.red,
                    "Api Error",
                    "Please try again later :slight_frown:",
                ),
            )

    @xvideos.autocomplete("search")
    async def xvideos_autocomplete(
        self, interaction: disnake.GuildCommandInteraction, name: str
    ):
        data = await self.bot._request(
            f"{nsfw_api}/suggestion/xvideos/{name or 'porn'}"
        )
        return {keywords for keywords in data.get("data", [])}

    @slash_nsfw.sub_command(name="redtube")
    async def redtube(
        self,
        interaction: disnake.CommandInteraction,
        search: str = "porn",
        amount: commands.Range[1, 10] = 1,  # type: ignore
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
                    Embeds.blue,
                    f"Searching {search}",
                    "Please wait while we search for your content",
                )
            )
            URL = (
                "https://api.redtube.com/?data=redtube.Videos.searchVideos"
                f"&output=json&search={search}&thumbsize=all&page=1&sort=new"
            )
            data = await self.bot._request(URL)
            random.shuffle(data["videos"])
            for count, content in enumerate(data["videos"]):
                if count >= amount:  # type: ignore
                    break
                else:
                    count = count + 1
                embed = Embeds.emb(
                    Embeds.red,
                    "Showing Results for:" f" {search}",
                    f"""
                     **Title**: {content["video"]["title"]}
                     **Duration**: {content["video"]["duration"]}
                                    """,
                )
                embed.set_thumbnail(url=content["video"]["default_thumb"])
                await interaction.channel.send(
                    components=[
                        url_button_builder(
                            url=content["video"]["url"], label="Watch Now", emoji="📺"
                        ),
                    ],
                    embed=embed,
                )
                await interaction.edit_original_response(
                    embed=Embeds.emb(
                        Embeds.green,
                        "Search Completed",
                        f"Showing {amount} results for `{search}`",
                    )
                )
        except Exception:
            await interaction.edit_original_response(
                embed=Embeds.emb(
                    Embeds.red,
                    "Api Error",
                    "Please try again later :slight_frown:",
                ),
            )

    @slash_nsfw.sub_command()
    async def reddit(
        self,
        interaction: disnake.CommandInteraction,
        search: str,
        amount: commands.Range[1, 10] = 1,  # type: ignore
    ):
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
                    "https://www.reddit.com/r/porn_gifs/search.json"
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
                if count >= amount:  # type: ignore
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
                    amount += 1  # type: ignore
                    continue

                if not url.startswith("http"):
                    amount += 1  # type: ignore
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
                return
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
    async def reddit_autocomp(self, interaction, name: str) -> Union[Set[str], None]:
        name = name.lower()
        url = (
            "https://www.reddit.com/api/search_reddit_names.json?"
            f"query={name or 'porn'}&include_over_18=True"
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
