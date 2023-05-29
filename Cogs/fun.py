import json
import logging
import random
from datetime import datetime
from typing import Dict, List, Set, Union

import aiohttp
import disnake
from aiocache import cached
from disnake.ext import commands
from selectolax.parser import HTMLParser

from utils import Embeds, delete_button

logger = logging.getLogger(__name__)


class AdultScrapper:
    """
    Scraps Adult Content from Xnxx and Xvideos
    """

    def __init__(self, base_url: str, session: aiohttp.ClientSession):
        self.session = session
        self.base_url = base_url

    @cached(ttl=60 * 60 * 12)
    async def _get_html(self, url: str) -> HTMLParser:
        async with self.session.get(
            url, headers={"User-Agent": "Magic Browser"}, ssl=False
        ) as resp:
            return HTMLParser(await resp.text())

    @cached(ttl=60 * 60 * 12)
    async def extract_videos(self, url: str) -> Dict:
        """
        Extracts Video Data from Xnxx and Xvideos

        Parameters
        ----------
        url: Url of the video
        """
        dom = await self._get_html(url=url)
        data = dom.css_first('script[type="application/ld+json"]').text()
        data = dict(eval(data))
        parsed_date = datetime.strptime(
            data.get("uploadDate", "0000-00-00T00:00:00+00:00"), "%Y-%m-%dT%H:%M:%S%z"
        )
        payload = {
            "thumbnail": data.get("thumbnailUrl", [])[0],
            "upload_date": parsed_date.strftime("%Y-%m-%d %H:%M:%S"),
            "name": data.get("name"),
            "description": data.get("description", "").strip(),
            "content_url": data.get("contentUrl"),
        }
        return payload

    @cached(ttl=60 * 60 * 12)
    async def get_link(self, search: str, xvideos: bool) -> Set[str]:
        """
        Gets the link of the video

        Parameters
        ----------
        search: What to search?
        xvideos: Search on xvideos or xnxx?
        """
        search.replace(" ", "+")
        search_payload = (
            f"https://www.xvideos.com/?k={search}&top"
            if xvideos
            else f"https://www.xnxx.tv/search/{search.replace(' ', '+')}?top"
        )
        dom = await self._get_html(url=search_payload)
        return {
            f'{self.base_url}{anchor.css_first("a").attrs.get("href")}'
            for anchor in dom.css_first("div.mozaique.cust-nb-cols").css("div.thumb")
        }

    async def send_video(
        self, search: str, amount: int = 1, xvideos: bool = False
    ) -> List[Dict]:
        """
        Sends the video

        Parameters
        ----------
        search: What to search?
        amount: How much?
        xvideos: Search on xvideos or xnxx?
        """
        links = list(await self.get_link(search=search, xvideos=xvideos))
        random.shuffle(links)
        data = []
        for index, link in enumerate(set(links)):
            if index > amount:
                break
            try:
                data.append(await self.extract_videos(url=link))
            except Exception:
                amount += 1
                continue
        return data


class Fun(commands.Cog):
    def __init__(self, client):
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
        amount: commands.Range[1, 3] = 1,  # type: ignore
    ):
        """
        Loads content from xnxx.com

        Parameters
        ----------
        search: What to search?
        amount: How much?
        """
        try:
            xnxx = AdultScrapper(
                base_url="https://www.xnxx.tv", session=self.bot.session
            )
            data = await xnxx.send_video(search=search, amount=amount, xvideos=False)  # type: ignore
            for vid in data:
                await interaction.send(
                    components=[delete_button],
                    embed=(
                        Embeds.emb(
                            Embeds.blue,
                            f"Showing Result for: {search}",
                            f"""
                        Name: {vid["name"]}
                        Description: {vid["description"]}
                        Video: [Watch Now]({vid["content_url"]})
                        Upload Date: {vid["upload_date"]}
                        """,
                        )
                    ).set_image(url=vid["thumbnail"]),
                )
        except Exception:
            logger.error("Error in Xnxx", exc_info=True)
            await interaction.send(
                embed=Embeds.emb(
                    Embeds.red,
                    "Api Error",
                    "Please try again later :slight_frown:",
                ),
                delete_after=5,
            )

    @commands.is_nsfw()
    @slash_nsfw.sub_command(name="xvideos")
    async def xvideos(
        self,
        interaction: disnake.CommandInteraction,
        search: str = "porn",
        amount: commands.Range[1, 3] = 1,  # type: ignore
    ):
        """
        Loads content from xvideos.com

        Parameters
        ----------
        search: What to search?
        amount: How much?
        """
        try:
            xnxx = AdultScrapper(
                base_url="https://www.xvideos.com", session=self.bot.session
            )
            data = await xnxx.send_video(search=search, amount=amount, xvideos=true)  # type: ignore
            for vid in data:
                await interaction.send(
                    components=[delete_button],
                    embed=(
                        Embeds.emb(
                            Embeds.blue,
                            f"Showing Result for: {search}",
                            f"""
                        Name: {vid["name"]}
                        Description: {vid["description"]}
                        Video: [Watch Now]({vid["content_url"]})
                        Upload Date: {vid["upload_date"]}
                        """,
                        )
                    ).set_image(url=vid["thumbnail"]),
                )
        except Exception:
            logger.error("Error in Xnxx", exc_info=True)
            await interaction.send(
                embed=Embeds.emb(
                    Embeds.red,
                    "Api Error",
                    "Please try again later :slight_frown:",
                ),
                delete_after=5,
            )

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
                 Title: {content["video"]["title"]}
                 Duration: {content["video"]["duration"]}
                 Views: {content["video"]["views"]}
                 Rating: {content["video"]["rating"]}
                 [Watch now]({content["video"]["url"]})
                                """,
            )
            embed.set_thumbnail(url=content["video"]["default_thumb"])
            await interaction.send(
                components=[delete_button],
                embed=embed,
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
                "No Results Found, Try something else :face_holding_back_tears:"
            )
        random.shuffle(links_list)
        for count, data in enumerate(links_list):
            if count >= amount:  # type: ignore
                break

            elif data["data"]["is_video"]:
                url = data["data"]["media"]["reddit_video"]["fallback_url"].replace(
                    "?source=fallback", ""
                )

            elif data["data"].get("is_gallery"):
                url = str("\n".join({data for data in data["data"]["media_metadata"]}))

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
                if count + 1 >= len(links_list):
                    await interaction.send(
                        "This search have only :poop:", delete_after=5
                    )
                    continue
                amount += 1  # type: ignore
                continue

            if not url.startswith("http"):
                amount += 1  # type: ignore
                continue

            await interaction.send(url, components=[delete_button])

    @reddit.autocomplete("search")
    async def reddit_autocomp(self, interaction, name: str) -> Union[Set[str], None]:
        name = name.lower()
        url = (
            "https://www.reddit.com/api/search_reddit_names.json?"
            f"query={name or 'porn'}&include_over_18=True"
        )
        data = await self.bot._request(url)
        return set(name for name in data["names"])

    @commands.slash_command(name="meme")
    async def slash_meme(self, interaction, amount: int = 1):
        """
        Shows You Memes

        Parameters
        ----------
        amount: Amount of memes you want to see
        """
        await self.reddit(interaction, search="meme", amount=amount)


def setup(client: commands.Bot):
    client.add_cog(Fun(client))
