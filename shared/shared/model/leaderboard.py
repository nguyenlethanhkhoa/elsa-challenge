import uuid
from typing import Optional

from sqlmodel import Field, SQLModel


class Leaderboard(SQLModel, table=True):

    __tablename__ = 'leaderboard'

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID
    score: int
