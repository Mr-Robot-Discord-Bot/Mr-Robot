import sqlalchemy
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .guild import Guild


class TempRole(Base):
    __tablename__ = "temprole"

    id: Mapped[int] = mapped_column(sqlalchemy.Integer, primary_key=True, index=True)
    guild_id: Mapped[int] = mapped_column(
        sqlalchemy.ForeignKey("guilds.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[int] = mapped_column(sqlalchemy.BigInteger, index=True)
    role_id: Mapped[int] = mapped_column(sqlalchemy.BigInteger)
    expiration: Mapped[str] = mapped_column(sqlalchemy.Text)

    # Relationship
    guild: Mapped[Guild] = relationship("Guild", passive_deletes=True)
