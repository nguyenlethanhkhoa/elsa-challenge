import os

from shared.event.manager import EventManager, Event
from shared.model import Leaderboard, CorrectAnswer
from sqlalchemy import create_engine
from sqlmodel import select, Session

SERVICE_NAME = os.environ.get('SERVICE_NAME', 'data_saver')

event_manager = EventManager()

engine = create_engine("postgresql://{}:{}@{}:{}/{}".format(
    os.environ.get('DB_USER', 'research'),
    os.environ.get('DB_PASSWORD', 'research'),
    os.environ.get('DB_HOST', 'localhost'),
    os.environ.get('DB_PORT', '5432'),
    os.environ.get('DB_NAME', 'leaderboard')
))


def on_answer_submitted(message):
    question_id = message.value.get('question_id')
    answer_id = message.value.get('answer_id')
    quiz_id = message.value.get('quiz_id')
    user_id = message.value.get('user_id')

    if (
        not question_id or
        not answer_id or
        not quiz_id or
        not user_id
    ):
        # TODO: Log as critical error
        return

    with Session(engine) as session:
        stm = select(CorrectAnswer).where(CorrectAnswer.question_id == question_id)
        correct_answer = session.exec(stm).first()

        stm = select(Leaderboard)\
            .where(Leaderboard.quiz_id == quiz_id)\
            .where(Leaderboard.user_id == user_id)

        leaderboard = session.exec(stm).first()
        if not leaderboard:
            leaderboard = Leaderboard()
            leaderboard.user_id = user_id
            leaderboard.quiz_id = quiz_id
            leaderboard.score = 0

        leaderboard.score += 1 if correct_answer.answer_id == answer_id else 0

        # TODO: Save user's answer into database

        session.add(leaderboard)
        session.commit()


def on_user_joined_quiz(message):
    user_id = message.value.get('user_id')
    quiz_id = message.value.get("quiz_id")

    with Session(engine) as session:
        stm = select(Leaderboard)\
            .where(Leaderboard.quiz_id == quiz_id)\
            .where(Leaderboard.user_id == user_id)

        leaderboard_item = session.exec(stm).first()

        if leaderboard_item:
            return

        leaderboard_item = Leaderboard()
        leaderboard_item.quiz_id = quiz_id
        leaderboard_item.user_id = user_id
        leaderboard_item.score = 0

        session.add(leaderboard_item)
        session.commit()


if __name__ == "__main__":
    event_manager.listen_on(Event.ANSWER_SUBMITTED, on_answer_submitted)
    event_manager.listen_on(Event.USER_JOINED_QUIZ, on_user_joined_quiz)

    event_manager.consume(SERVICE_NAME)
