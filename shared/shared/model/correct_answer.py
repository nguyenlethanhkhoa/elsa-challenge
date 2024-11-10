import uuid
from typing import Optional

from sqlmodel import Field, SQLModel


class CorrectAnswer(SQLModel, table=True):

    __tablename__ = 'correct_answer'

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    question_id: uuid.UUID
    answer_id: uuid.UUID
