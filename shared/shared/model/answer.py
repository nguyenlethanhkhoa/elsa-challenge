import uuid
from typing import Optional

from sqlmodel import Field, SQLModel


class Answer(SQLModel, table=True):

    __tablename__ = 'answer'

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    question_id: uuid.UUID
    title: str
    description: Optional[str]

    is_correct: bool = Field(default=False)
