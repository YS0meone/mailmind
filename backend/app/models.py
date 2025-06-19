from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from pydantic import BaseModel

class Base(DeclarativeBase):
    pass


class DbUser(Base):
    __tablename__ = 'users'
    account_id: Mapped[int] = mapped_column(primary_key=True)
    account_token: Mapped[str] = mapped_column(nullable=False)

class User(BaseModel):
    account_id: int
    account_token: str
