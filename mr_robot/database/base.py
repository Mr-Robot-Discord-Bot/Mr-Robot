from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}({', '.join([f"{col}={getattr(self, col, None)}" for col in self.__table__.columns.keys()])})"
