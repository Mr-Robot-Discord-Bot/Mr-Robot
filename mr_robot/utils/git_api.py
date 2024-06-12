import base64
from pathlib import Path
from typing import Dict

import aiofiles
import httpx


class NothingToUpdate(Exception):
    """Raised when the push file is same to source file"""


class Git:
    def __init__(
        self,
        token: str,
        owner: str,
        repo: str,
        username: str,
        email: str,
        client: httpx.AsyncClient,
    ):
        self.token = token
        self.owner = owner
        self.repo = repo
        self.username = username
        self.email = email
        self.base_url = (
            f"https://api.github.com/repos/{self.owner}/{self.repo}/contents"
        )
        self.client = client
        self.header = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def pull_data(self, path: str) -> Dict:
        url = f"{self.base_url}/{path}"
        r = await self.client.get(url, headers=self.header)
        r.raise_for_status()
        json = r.json()
        return json

    async def pull(self, path: str) -> None:
        url = f"{self.base_url}/{path}"
        r = await self.client.get(url, headers=self.header)
        r.raise_for_status()
        json = r.json()
        file = json.get("content")
        decoded_file = base64.b64decode(file)
        name = json.get("name")
        async with aiofiles.open(name, "wb") as f:
            await f.write(decoded_file)

    async def push(self, file: Path, commit_msg: str):
        url = f"{self.base_url}/{file.name}"
        async with aiofiles.open(file, "rb") as f:
            content = await f.read()
        encoded_content = base64.b64encode(content).decode()
        resp_json = await self.pull_data(file.name)
        sha = resp_json.get("sha")
        if encoded_content.replace("\n", "") == resp_json.get("content", "").replace(
            "\n", ""
        ):
            raise NothingToUpdate
        data = {
            "message": commit_msg,
            "committer": {"name": self.username, "email": self.email},
            "content": encoded_content,
            "sha": sha,
        }
        r = await self.client.put(url, json=data, headers=self.header)
        r.raise_for_status()


if __name__ == "__main__":
    import asyncio

    async def main():
        async with httpx.AsyncClient() as client:
            git = Git(
                token="GITHUB TOKEN",
                owner="OWNER",
                repo="REPO",
                username="test",
                email="test@test.com",
                client=client,
            )
            # r = await git.pull_data("test.txt")
            # print(r.get("content"))

            await git.push(
                file=Path("test.txt"),
                commit_msg="test",
            )

    asyncio.run(main())
