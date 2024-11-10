import uuid
from typing import Optional

from sqlmodel import SQLModel, Field


class QuizQuestion(SQLModel, table=True):
    __tablename__ = 'quiz_question'

    quiz_id: uuid.UUID = Field(foreign_key="quiz.id", primary_key=True)
    question_id: uuid.UUID = Field(foreign_key="question.id", primary_key=True)

    order: Optional[int] = Field(default=None, description="Order of question in the quiz")