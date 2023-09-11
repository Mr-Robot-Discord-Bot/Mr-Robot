import base64
from pathlib import Path

import aiofiles
import httpx


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
        self.client.headers.update({"Authorization": f"Bearer {self.token}"})
        self.client.headers.update({"Accept": "application/vnd.github+json"})
        self.client.headers.update({"X-GitHub-Api-Version": "2022-11-28"})

    async def pull_data(self, path: str) -> str:
        url = f"{self.base_url}/{path}"
        r = await self.client.get(url)
        r.raise_for_status()
        json = r.json()
        return json.get("sha")

    async def pull(self, path: str) -> None:
        url = f"{self.base_url}/{path}"
        r = await self.client.get(url)
        r.raise_for_status()
        json = await r.json()
        file = json.get("content")
        decoded_file = base64.b64decode(file)
        name = json.get("name")
        async with aiofiles.open(name, "wb") as f:
            await f.write(decoded_file)

    async def push(self, file: Path, commit_msg: str):
        url = f"{self.base_url}/{file.name}"
        async with aiofiles.open(file, "rb") as f:
            content = await f.read()
        encoded_content = base64.b64encode(content).decode("utf-8")
        try:
            sha = await self.pull_data(file.name)
        except httpx.HTTPError:
            sha = None
        data = {
            "message": commit_msg,
            "committer": {"name": self.username, "email": self.email},
            "content": encoded_content,
            "sha": sha,
        }
        r = await self.client.put(url, json=data)
        r.raise_for_status()


if __name__ == "__main__":
    import asyncio

    async def main():
        async with httpx.AsyncClient() as client:
            git = Git(
                token="TOKEN",
                owner="OWNER",
                repo="REPO",
                username="etest",
                email="test@test.com",
                client=client,
            )
            # await git.pull("test.txt")

            await git.push(
                file=Path("test.txt"),
                commit_msg="test",
            )

    asyncio.run(main())
