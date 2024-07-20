import sqlalchemy
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .guild import Guild


class TicketConfig(Base):
    __tablename__ = "ticket_configs"

    id: Mapped[int] = mapped_column(sqlalchemy.Integer, primary_key=True)
    guild_id: Mapped[int] = mapped_column(
        sqlalchemy.ForeignKey("guilds.id", ondelete="CASCADE"), index=True
    )
    config_id: Mapped[int] = mapped_column(sqlalchemy.BigInteger, index=True)
    user_or_role_id: Mapped[int] = mapped_column(sqlalchemy.BigInteger)
    category_id: Mapped[int] = mapped_column(sqlalchemy.BigInteger)
    image: Mapped[str] = mapped_column(sqlalchemy.Text)
    color: Mapped[int] = mapped_column(sqlalchemy.Integer)
    title: Mapped[str] = mapped_column(sqlalchemy.String)
    description: Mapped[str] = mapped_column(sqlalchemy.Text)

    # Relationship
    guild: Mapped[Guild] = relationship("Guild", passive_deletes=True)


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(sqlalchemy.Integer, primary_key=True)
    guild_id: Mapped[int] = mapped_column(
        sqlalchemy.ForeignKey("guilds.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[int] = mapped_column(sqlalchemy.BigInteger, index=True)
    config_id: Mapped[int] = mapped_column(sqlalchemy.BigInteger, index=True)
    channel_id: Mapped[int] = mapped_column(sqlalchemy.BigInteger)

    __table_args__ = (sqlalchemy.UniqueConstraint("guild_id", "user_id"),)

    # Relationship
    guild: Mapped[Guild] = relationship("Guild", passive_deletes=True)
