import uuid
from typing import Optional, List

from sqlmodel import Field, SQLModel, Relationship


class Quiz(SQLModel, table=True):

    __tablename__ = 'quiz'

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str
    description: Optional[str]

    # questions: List["Question"] = Relationship(back_populates="quizzes", link_model="QuizQuestion")
