import json
import random
from typing import Any, Dict, Set, Union

import disnake
from bs4 import BeautifulSoup
from disnake.ext import commands

from utils import SESSION_CTX, Embeds, delete_button


def extract_video_link(soup: BeautifulSoup) -> Union[dict, None]:
    link = soup.find("script", type="application/ld+json")
    if not link:
        return
    link = json.loads(link.string)  # type: ignore
    name = link["name"]
    description = link["description"]
    thumbnailUrl = link["thumbnailUrl"][0]
    url = link["contentUrl"]
    return {
        "name": name,
        "description": description,
        "thumbnailUrl": thumbnailUrl,
        "url": url,
    }


class Fun(commands.Cog):
    def __init__(self, client):
        self.bot = client
        self.session = SESSION_CTX.get()

    @commands.slash_command(name="nsfw", nsfw=True, dm_permission=False)
    async def slash_nsfw(
        self,
        interaction,
    ):
        """
        Shows You Nsfw Content
        """
        await interaction.response.defer()

    async def get(self, url: str) -> BeautifulSoup:
        try:
            async with self.session.get(url, ssl=False, timeout=7) as response:
                htmlcontent = await response.text()
        except Exception:
            raise Exception("Web not responding")
        soup = BeautifulSoup(htmlcontent, "html.parser")
        return soup

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
            domain = "https://www.xnxx.tv"
            ufrm_term = search
            term = search.replace(" ", "+")
            term_url = domain + "/search/" + str(term)
            search_term = await self.get(term_url)
            page = search_term.find("div", class_="mozaique cust-nb-cols")
            if page is None:
                await self.xnxx(interaction, search, amount)  # type: ignore
            items = random.sample(
                list(page.find_all("a")),  # type: ignore
                k=amount,  # type: ignore
            )
            for i in items:
                link = i.get("href")
                page = await self.get(domain + link)
                vid_dict = extract_video_link(page)
                if vid_dict:
                    await interaction.send(
                        components=[delete_button],
                        embed=(
                            Embeds.emb(
                                Embeds.blue,
                                f"Showing Result for: {ufrm_term}",
                                f"""
                            Name: {vid_dict['name'][:20]}
                            Description: {vid_dict['description'][:100]}
                            Video: [Watch Now]({vid_dict['url']})
                            """,
                            )
                        ).set_image(url=vid_dict["thumbnailUrl"]),
                    )
                else:
                    await self.xnxx(interaction, search, amount)
        except Exception:
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
        async with self.session.get(URL) as resp:
            if resp.status == 200:
                data = await resp.json()
                total_pages = data["count"] // len(data["videos"])
                page = random.randint(1, total_pages)
                count = 0
                URL = (
                    "https://api.redtube.com/?"
                    "data=redtube.Videos.searchVideos&output=json&"
                    f"search={search}&thumbsize=all&page={page}&sort=new"
                )
                async with self.session.get(URL) as resp:
                    if resp.status == 200:
                        random.shuffle(data["videos"])
                        for content in data["videos"]:
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
            else:
                raise Exception("API Error")

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
            f"include_over_18=True"
            "&type=link"
        )

        async def _request(url: str) -> Dict[Any, Any]:
            async with self.session.get(
                url, headers={"User-Agent": "Magic Browser"}
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    raise Exception(f"Unexpected response code {resp.status}")

        data = await _request(URL)
        links_list = data["data"]["children"]
        random.shuffle(links_list)
        for count, data in enumerate(links_list):
            if count >= amount:  # type: ignore
                break

            elif data["data"]["is_video"]:
                url = data["data"]["media"]["reddit_video"]["fallback_url"]

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
                amount += 1  # type: ignore
                if count + 1 == len(links_list):
                    await interaction.send(
                        "This search have only :poop:", delete_after=5
                    )
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
        header = {"User-Agent": "Magic Browser"}
        async with self.session.get(url, headers=header) as resp:
            if resp.status == 200:
                data = await resp.json()
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
