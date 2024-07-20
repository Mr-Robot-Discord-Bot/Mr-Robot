from typing import List, Literal

import mafic

from mr_robot.bot import MrRobot

NONE = "NONE"
PLAYLIST = "PLAYLIST"
TRACK = "TRACK"


class Player(mafic.Player[MrRobot]):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.queue: List[mafic.Track] = list()
        self.loop: Literal["NONE", "PLAYLIST", "TRACK"] = NONE

    async def destroy(self) -> None:
        self.queue.clear()
        self.loop = NONE

        await super().stop()
