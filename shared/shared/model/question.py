import uuid
from enum import Enum
from typing import Optional, List

from sqlmodel import Field, SQLModel, Relationship


class Question(SQLModel, table=True):

    __tablename__ = 'question'

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str
    description: Optional[str]

    # answers: List["Answer"] = Relationship(back_populates="question")
