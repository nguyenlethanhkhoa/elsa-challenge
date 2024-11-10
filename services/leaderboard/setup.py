import os
import json
import psycopg2
import sqlalchemy

from shared.model import CorrectAnswer, Leaderboard
from sqlalchemy import create_engine
from sqlmodel import SQLModel, Session


def create_database():
    conn = psycopg2.connect(
        dbname="postgres",
        user=os.environ.get('DB_USER', 'research'),
        password=os.environ.get('DB_PASSWORD', 'research'),
        host=os.environ.get('DB_HOST', 'localhost'),
        port=os.environ.get('DB_PORT', '5432')
    )

    cursor = conn.cursor()
    conn.autocommit = True

    try:
        cursor.execute("CREATE DATABASE leaderboard")
    except psycopg2.errors.DuplicateDatabase:
        pass

    cursor.close()
    conn.close()


def insert_dummy_data():
    with open('./dummy_data.json', 'r') as f:
        quizzes = json.load(f)

    leaderboard_db_engine = create_engine("postgresql://{}:{}@{}:{}/{}".format(
        os.environ.get('DB_USER', 'research'),
        os.environ.get('DB_PASSWORD', 'research'),
        os.environ.get('DB_HOST', 'localhost'),
        os.environ.get('DB_PORT', '5432'),
        os.environ.get('DB_NAME', 'leaderboard')
    ))
    SQLModel.metadata.create_all(leaderboard_db_engine)
    with Session(leaderboard_db_engine) as session:
        for quiz in quizzes:
            for question_order, question in enumerate(quiz['questions']):
                for answer in question['answers']:
                    if answer['is_correct']:
                        correct_answer = CorrectAnswer()
                        correct_answer.question_id = question['id']
                        correct_answer.answer_id = answer['id']

                        session.add(correct_answer)

        try:
            session.commit()
        except sqlalchemy.exc.IntegrityError:
            pass


if __name__ == "__main__":
    create_database()
    insert_dummy_data()
