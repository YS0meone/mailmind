from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from pydantic import BaseModel

class Base(DeclarativeBase):
    pass


class DbUser(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column()
    account_token: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(nullable=False, unique=True)
    last_delta_token: Mapped[str] = mapped_column(nullable=True)

    def __repr__(self):
        return f"<DbUser(id={self.id}, account_id={self.account_id}, email={self.email}, last_delta_token={self.last_delta_token})>"

class User(BaseModel):
    account_id: int
    account_token: str
    last_delta_token: str | None = None
    email: str

    def __repr__(self):
        return f"User(account_id={self.account_id}, email={self.email}, last_delta_token={self.last_delta_token})"
