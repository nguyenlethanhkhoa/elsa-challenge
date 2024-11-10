import os
import json

import redis
from shared.event.manager import EventManager, Event
from shared.model import Leaderboard, CorrectAnswer
from sqlmodel import col, select, Session
from sqlalchemy import create_engine


SERVICE_NAME = os.environ.get('SERVICE_NAME', 'leaderboard_updater')

event_manager = EventManager()

redis_client = redis.Redis(
    host=os.environ.get('MSG_QUEUE_HOST', 'localhost'),
    port=os.environ.get('MSG_QUEUE_PORT', '6379')
)

engine = create_engine("postgresql://{}:{}@{}:{}/{}".format(
    os.environ.get('DB_USER', 'research'),
    os.environ.get('DB_PASSWORD', 'research'),
    os.environ.get('DB_HOST', 'localhost'),
    os.environ.get('DB_PORT', '5432'),
    os.environ.get('DB_NAME', 'leaderboard')
))


def on_answer_submitted(message):
    user_id = message.value.get('user_id')
    quiz_id = message.value.get("quiz_id")
    question_id = message.value.get('question_id')
    answer_id = message.value.get('answer_id')

    update_quiz_leaderboard(
        user_id,
        quiz_id,
        question_id,
        answer_id
    )


def on_user_joined_quiz(message):
    user_id = message.value.get('user_id')
    quiz_id = message.value.get("quiz_id")

    update_quiz_leaderboard(
        user_id,
        quiz_id
    )


def get_quiz_leaderboard(quiz_id):
    leaderboard = redis_client.get(f'quiz_leaderboard_{quiz_id}')
    if leaderboard:
        return json.loads(leaderboard)

    with Session(engine) as session:
        stm = select(Leaderboard).where(quiz_id == quiz_id).order_by(col(Leaderboard.score).desc())
        leaderboard_items = session.exec(stm).all()

    return {item.user_id: item.score for item in leaderboard_items}


def get_correct_answer_id(question_id):
    correct_answer_id = redis_client.get(f'correct_answer_{question_id}')
    if correct_answer_id:
        return correct_answer_id.decode('utf-8')

    with Session(engine) as session:
        stm = select(CorrectAnswer).where(CorrectAnswer.question_id == question_id)

        # I assumed there is always one and only one correct answer for each question
        correct_answer = session.exec(stm).first()

        correct_answer_id = str(correct_answer.answer_id)

    redis_client.set(f'correct_answer_{question_id}', correct_answer_id)
    return correct_answer_id


def update_quiz_leaderboard(user_id, quiz_id, question_id=None, answer_id=None):
    leaderboard = get_quiz_leaderboard(quiz_id)

    if user_id not in leaderboard:
        leaderboard[user_id] = 0

    if question_id and answer_id:

        correct_answer_id = get_correct_answer_id(question_id)
        leaderboard[user_id] += 1 if answer_id == correct_answer_id else 0

    updated_leaderboard = {k: v for k, v in sorted(leaderboard.items(), key=lambda item: item[1], reverse=True)}

    # TODO: Required lock here to protect data in race condition
    redis_client.set(f'quiz_leaderboard_{quiz_id}', json.dumps(updated_leaderboard))

    event_manager.produce(Event.LEADERBOARD_UPDATED, {'quiz_id': quiz_id})


if __name__ == "__main__":
    event_manager.listen_on(Event.ANSWER_SUBMITTED, on_answer_submitted)
    event_manager.listen_on(Event.USER_JOINED_QUIZ, on_user_joined_quiz)

    event_manager.consume(SERVICE_NAME)
