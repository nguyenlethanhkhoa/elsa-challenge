import asyncio
import json
import os
import uuid

import redis
from fastapi import FastAPI

from fastapi_socketio import SocketManager
from shared.event.manager import EventManager, Event
from shared.model import Quiz, Question, QuizQuestion, Answer
from shared.logger import logger
from sqlalchemy import create_engine
from sqlmodel import SQLModel, select, Session, col

SERVICE_NAME = os.environ.get('SERVICE_NAME', 'quiz_service')

app = FastAPI()
event_manager = EventManager()
redis_client = redis.Redis(
    host=os.environ.get('MSG_QUEUE_HOST', 'localhost'),
    port=os.environ.get('MSG_QUEUE_PORT', '6379')
)
socket_manager = SocketManager(
    app=app,
    mount_location="/socket.io",
    message_queue="redis://{}:{}/0".format(
        os.environ.get('MSG_QUEUE_HOST', 'localhost'),
        os.environ.get('MSG_QUEUE_PORT', '6379'),
    ),
)

engine = create_engine("postgresql://{}:{}@{}:{}/{}".format(
    os.environ.get('DB_USER', 'research'),
    os.environ.get('DB_PASSWORD', 'research'),
    os.environ.get('DB_HOST', 'localhost'),
    os.environ.get('DB_PORT', '5432'),
    os.environ.get('DB_NAME', 'quiz')
))
SQLModel.metadata.create_all(engine)


async def on_leaderboard_updated(message):

    message = json.loads(message.value.decode("utf-8"))
    quiz_id = message.get("quiz_id")

    updated_leaderboard = redis_client.get(f'quiz_leaderboard_{quiz_id}')
    if not updated_leaderboard:
        return

    updated_leaderboard = json.loads(updated_leaderboard)

    logger.info(f'on_leaderboard_updated called with quiz_id is {quiz_id}')
    if quiz_id:
        await socket_manager.emit(
            "leaderboard_updated",
            updated_leaderboard,
            room=quiz_id
        )


@app.on_event("startup")
async def startup_event():
    # Start the Kafka consumer loop as a background task
    event_manager.listen_on(Event.LEADERBOARD_UPDATED, on_leaderboard_updated)
    asyncio.create_task(event_manager.async_consume(SERVICE_NAME))


@socket_manager.on("quiz_session_start")
async def handle_start_quiz(sid, data):
    quiz_id = data.get("quiz_id")
    user_id = data.get('user_id')
    user_id = user_id if user_id else str(uuid.uuid4())

    message = {
        "status": "success",
        'message': f"{sid} joined",
        "user_id": user_id
    }
    event_manager.produce(Event.USER_JOINED_QUIZ, {'user_id': user_id, 'quiz_id': quiz_id})
    if quiz_id:
        await socket_manager.enter_room(sid, quiz_id)
        await socket_manager.emit(
            "quiz_session_started",
            message,
            to=sid
        )


@socket_manager.on("submit_answer")
async def handle_submit_answer(sid, data):
    user_id = data.get('user_id')
    question_id = data.get('question_id')
    answer_id = data.get("answer_id")
    quiz_id = data.get('quiz_id')

    if quiz_id and question_id and answer_id:
        event_manager.produce(Event.ANSWER_SUBMITTED, {
            'user_id': user_id,
            'quiz_id': quiz_id,
            'question_id': question_id,
            'answer_id': answer_id
        })
        await socket_manager.emit(
            "answer_received", {
                "status": "received_answer", "answer_id": answer_id
            },
            room=quiz_id
        )


@app.get('/quizzes')
def get_quizzes():
    with Session(engine) as session:
        quizzes = session.exec(select(Quiz)).all()
        return {
            'status': 'success',
            'result': {
                'items': [quiz.dict() for quiz in quizzes],
                'total': len(quizzes)
            }
        }


@app.get('/quizzes/{quiz_id}/questions')
def get_questions(quiz_id: str):
    with Session(engine) as session:
        stm = select(Question)\
            .join(QuizQuestion, QuizQuestion.question_id == Question.id)\
            .where(QuizQuestion.quiz_id == quiz_id)

        questions = session.exec(stm).all()

        stm = select(Answer)\
            .where(col(Answer.question_id).in_([question.id for question in questions]))

        answers = session.exec(stm).all()

        question_answer_map = {}
        for answer in answers:
            if answer.question_id not in question_answer_map:
                question_answer_map[answer.question_id] = []

            question_answer_map[answer.question_id].append(answer.dict())

        result_items = []
        for question in questions:
            result_item = question.dict()
            result_item['answers'] = question_answer_map.get(question.id, [])

            result_items.append(result_item)

        return {
            'status': 'success',
            'result': {
                'items': result_items,
                'total': len(result_items)
            }
        }


