from __future__ import annotations

from typing import List

import sqlalchemy
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Playlists(Base):
    __tablename__ = "playlists"

    id: Mapped[int] = mapped_column(sqlalchemy.Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(sqlalchemy.String(length=50))
    user_id: Mapped[int] = mapped_column(sqlalchemy.BigInteger, index=True)
    tracks: Mapped[List[Tracks]] = relationship(
        "Tracks", back_populates="playlists", cascade="all, delete", lazy="selectin"
    )


class Tracks(Base):
    __tablename__ = "tracks"
    id: Mapped[int] = mapped_column(sqlalchemy.Integer, primary_key=True, index=True)

    playlist_id: Mapped[int] = mapped_column(
        sqlalchemy.ForeignKey("playlists.id", ondelete="CASCADE"), index=True
    )
    track: Mapped[str] = mapped_column(sqlalchemy.Text, index=True)

    playlists: Mapped[Playlists] = relationship(
        "Playlists", back_populates="tracks", passive_deletes=True, lazy="selectin"
    )
