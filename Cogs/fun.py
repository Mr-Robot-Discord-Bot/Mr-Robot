import json
import os
import random
from typing import List, Union

import aiohttp
import disnake
from bs4 import BeautifulSoup
from disnake.ext import commands
from disnake.ui import Button

from utils import DeleteButton, Embeds, send_webhook

WEBHOOK_URL = os.getenv("whcontent")


async def reddit_autocomp(interaction, name: str) -> Union[List[str], None]:
    name = name.lower()
    url = (
        "https://www.reddit.com/api/search_reddit_names.json?"
        f"query={name or 'porn'}&include_over_18=True"
    )
    header = {"User-Agent": "Magic Browser"}
    async with aiohttp.request("GET", url, headers=header) as resp:
        if resp.status == 200:
            data = await resp.json()
            return [name for name in data["names"]]


def extract_video_link(soup: BeautifulSoup) -> dict:
    link = soup.find("script", type="application/ld+json")
    if not link:
        raise Exception("Please Try Again Later!")
    link = json.loads(link.string)
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


async def get(url: str) -> BeautifulSoup:
    while True:
        try:
            async with aiohttp.ClientSession(trust_env=True) as session:
                async with session.get(url, ssl=False, timeout=7) as response:
                    htmlcontent = await response.text()
                    break
        except Exception:
            continue
    soup = BeautifulSoup(htmlcontent, "html.parser")
    return soup


button: Button = Button(label=":bomb:", style=disnake.ButtonStyle.red)


class Fun(commands.Cog):
    def __init__(self, client):
        self.bot = client

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
        amount: commands.Range[1, 3] = 1,
    ):
        """
        Loads content from xnxx.com

        Parameters
        ----------
        search: What to search?
        amount: How much?
        """
        ufrm_term = search
        term = search.replace(" ", "+")
        term_url = "https://www.xnxx.com/search/" + str(term)
        search_term = await get(term_url)
        items = random.sample(
            list(search_term.find("div", class_="mozaique cust-nb-cols").find_all("a")),
            k=amount,
        )
        for i in items:
            link = i.get("href")
            page = await get("https://www.xnxx.com" + link)
            vid_dict = extract_video_link(page)
            await interaction.send(
                view=DeleteButton(author=interaction.author),
                embed=(
                    Embeds.emb(
                        Embeds.blue,
                        f"Showing Result for: {ufrm_term}",
                        f"""
                    Name: {vid_dict['name']}
                    Description: {vid_dict['description']}
                    Video: [Watch Now]({vid_dict['url']})
                    """,
                    )
                ).set_image(url=vid_dict["thumbnailUrl"]),
                delete_after=60 * 60,
            )
            await send_webhook(
                username="Content Logger",
                webhook_url=WEBHOOK_URL,
                embed=(
                    Embeds.emb(
                        Embeds.blue,
                        (interaction.guild.name if interaction.guild else ""),
                        f"""
                        Guild Id: {interaction.guild.id}
                        Channel Id: {interaction.channel.id}
                        Channel Name: {interaction.
                                       channel.name}
                        User Id: {interaction.author.id}
                        User Name: {interaction.author.name}
                        Search Term: {ufrm_term}
                        Name: {vid_dict['name']}
                        Description: {vid_dict['description']}
                        Video: [Watch Now]({vid_dict['url']})
                                   """,
                    )
                ).set_image(url=vid_dict["thumbnailUrl"]),
            )

    @slash_nsfw.sub_command(name="redtube")
    async def redtube(
        self,
        interaction: disnake.CommandInteraction,
        search: str = "porn",
        amount: commands.Range[1, 10] = 1,
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
        async with aiohttp.request("GET", URL) as resp:
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
                async with aiohttp.request("GET", URL) as resp:
                    if resp.status == 200:
                        random.shuffle(data["videos"])
                        for content in data["videos"]:
                            if count >= amount:
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
                                view=DeleteButton(author=interaction.author),
                                embed=embed,
                            )
                            embed = Embeds.emb(
                                Embeds.red,
                                (interaction.guild.name if interaction.guild else ""),
                                f"""
       Guild Id: {interaction.guild.id if interaction.guild else ""}
       Channel Id: {interaction.channel.id}
       Channel Name: {interaction.channel.name}
       User Id: {interaction.author.id}
       User Name: {interaction.author.name}
       Content: [{content["video"]["title"]}]({content["video"]["url"]})
       Rating: {content["video"]["ratings"]}
       Views: {content["video"]["views"]}
                                               """,
                            )
                            embed.set_thumbnail(url=content["video"]["default_thumb"])
                            await send_webhook(
                                username="Content Logger",
                                embed=embed,
                                webhook_url=WEBHOOK_URL,
                            )

            else:
                raise Exception("API Error")

    @slash_nsfw.sub_command()
    async def reddit(
        self,
        interaction: disnake.CommandInteraction,
        search: str = commands.Param(autocomplete=reddit_autocomp),
        amount: commands.Range[1, 10] = 1,
    ):
        """
        Loads content from reddit.com

        Parameters
        ----------
        search: What to search?
        amount: How much?
        """
        header = {"User-Agent": "Magic Browser"}
        URL = (
            f"https://www.reddit.com/r/{search}.json?"
            "raw_json=1&limit=100&"
            f"include_over_18=True"
            "&type=link"
        )
        async with aiohttp.request("GET", URL, headers=header) as resp:
            if resp.status == 200:
                data = await resp.json()
                count = 0
                links = []
                for d in random.sample(
                    data["data"]["children"], min(amount, len(data["data"]["children"]))
                ):
                    if d["kind"] != "t3" or d["data"]["url"] in links:
                        continue
                    elif d["data"]["url"] not in links:
                        links.append(d["data"]["url"])

                    if d["data"]["is_video"]:
                        await interaction.send(
                            d["data"]["media"]["reddit_video"]["fallback_url"],
                            view=DeleteButton(author=interaction.author),
                        )
                        await send_webhook(
                            username="Content Logger",
                            webhook_url=WEBHOOK_URL,
                            embed=(
                                Embeds.emb(
                                    Embeds.orange,
                                    (
                                        interaction.guild.name
                                        if interaction.guild
                                        else ""
                                    ),
                                    f"""
            Guild Id: {interaction.guild.id if interaction.guild else ""}
            Channel Id: {interaction.channel.id}
            Channel Name: {interaction.channel.name}
            User Id: {interaction.author.id}
            User Name: {interaction.author.name}
            Content: {d["data"]["media"]["reddit_video"]["fallback_url"]}
                                                            """,
                                )
                            ).set_image(
                                d["data"]["media"]["reddit_video"]["fallback_url"]
                            ),
                        )

                    elif d["data"].get("is_gallery"):
                        embed = Embeds.emb(
                            Embeds.orange,
                            (interaction.guild.name if interaction.guild else ""),
                            f"""
                                    Guild Id: {interaction.guild.id
                                               if interaction.guild else ""}
                                    Channel Id: {interaction.channel.id}
                                    Channel Name: {interaction.channel.name}
                                    User Id: {interaction.author.id}
                                    User Name: {interaction.author.name}
                                    Content: {d["data"]["url"]}
                                    """,
                        )
                        await send_webhook(
                            username="Content Logger",
                            webhook_url=WEBHOOK_URL,
                            embed=embed,
                        )
                        for _, value in d["data"]["media_metadata"].items():
                            if count > amount:
                                break
                            await interaction.send(
                                value["s"]["u"],
                                view=DeleteButton(author=interaction.author),
                            )
                            count = count + 1

                    elif "redgifs.com" in d["data"]["url"]:
                        await interaction.send(
                            d["data"]["url_overridden_by_dest"],
                            view=DeleteButton(author=interaction.author),
                        )
                        await send_webhook(
                            username="Content Logger",
                            embed=(
                                Embeds.emb(
                                    Embeds.orange,
                                    (
                                        interaction.guild.name
                                        if interaction.guild
                                        else ""
                                    ),
                                    f"""
                            Guild Id: {interaction.guild.id
                                       if interaction.guild else ""}
                            Channel Id: {interaction.channel.id}
                            Channel Name: {interaction.channel.name}
                            User Id: {interaction.author.id}
                            User Name: {interaction.author.name}
                            Content: {d["data"]["url_overridden_by_dest"]}
                                                            """,
                                )
                            ),
                            webhook_url=WEBHOOK_URL,
                        )

                    elif d["data"]["url"].endswith(
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
                        await interaction.send(
                            d["data"]["url_overridden_by_dest"],
                            view=DeleteButton(author=interaction.author),
                        )
                        await send_webhook(
                            username="Content Logger",
                            embed=(
                                Embeds.emb(
                                    Embeds.orange,
                                    (
                                        interaction.guild.name
                                        if interaction.guild
                                        else ""
                                    ),
                                    f"""
                            Guild Id: {interaction.guild.id}
                            Channel Id: {interaction.channel.id}
                            Channel Name: {interaction.channel.name}
                            User Id: {interaction.author.id}
                            User Name: {interaction.author.name}
                            Content: {d["data"]["url_overridden_by_dest"]}
                                                            """,
                                )
                            ).set_image(d["data"]["url_overridden_by_dest"]),
                            webhook_url=WEBHOOK_URL,
                        )

                    else:
                        await interaction.send(
                            d["data"]["thumbnail"],
                            view=DeleteButton(author=interaction.author),
                        )
                        await send_webhook(
                            username="Content Logger",
                            embed=(
                                Embeds.emb(
                                    Embeds.orange,
                                    (
                                        interaction.guild.name
                                        if interaction.guild
                                        else ""
                                    ),
                                    f"""
                                Guild Id: {interaction.guild.id}
                                Channel Id: {interaction.channel.id}
                                Channel Name: {interaction.channel.name}
                                User Id: {interaction.author.id}
                                User Name: {interaction.author.name}
                                Content: {d["data"]["thumbnail"]}
                                                            """,
                                )
                            ).set_image(d["data"]["thumbnail"]),
                            webhook_url=WEBHOOK_URL,
                        )
                    if count <= amount:
                        count = count + 1
                    else:
                        break

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
