from typing import Optional

import sqlalchemy
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .guild import Guild


class Greeter(Base):
    __tablename__ = "greeters"

    id: Mapped[int] = mapped_column(
        sqlalchemy.Integer, primary_key=True, autoincrement=False, index=True
    )
    guild_id: Mapped[int] = mapped_column(
        sqlalchemy.ForeignKey("guilds.id", ondelete="CASCADE"), index=True
    )
    wlcm_channel: Mapped[Optional[int]] = mapped_column(
        sqlalchemy.BigInteger, nullable=True
    )
    wlcm_image: Mapped[Optional[str]] = mapped_column(sqlalchemy.String, nullable=True)
    wlcm_theme: Mapped[Optional[str]] = mapped_column(sqlalchemy.String, nullable=True)
    wlcm_fontstyle: Mapped[Optional[str]] = mapped_column(
        sqlalchemy.String, nullable=True
    )
    wlcm_outline: Mapped[Optional[int]] = mapped_column(
        sqlalchemy.Integer, nullable=True
    )
    wlcm_msg: Mapped[Optional[str]] = mapped_column(sqlalchemy.String, nullable=True)
    bye_channel: Mapped[Optional[int]] = mapped_column(
        sqlalchemy.BigInteger, nullable=True
    )
    bye_image: Mapped[Optional[str]] = mapped_column(sqlalchemy.String, nullable=True)
    bye_theme: Mapped[Optional[str]] = mapped_column(sqlalchemy.String, nullable=True)
    bye_fontstyle: Mapped[Optional[str]] = mapped_column(
        sqlalchemy.String, nullable=True
    )
    bye_outline: Mapped[Optional[int]] = mapped_column(
        sqlalchemy.Integer, nullable=True
    )
    bye_msg: Mapped[Optional[str]] = mapped_column(sqlalchemy.String, nullable=True)

    guild: Mapped[Guild] = relationship("Guild", passive_deletes=True)
