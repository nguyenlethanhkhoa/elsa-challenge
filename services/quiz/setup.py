import os
import json
import psycopg2
import sqlalchemy

from shared.model import Quiz, Question, Answer, QuizQuestion
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
        cursor.execute("CREATE DATABASE quiz")
    except psycopg2.errors.DuplicateDatabase:
        pass

    cursor.close()
    conn.close()


def insert_dummy_data():
    quiz_db_engine = create_engine("postgresql://{}:{}@{}:{}/{}".format(
        os.environ.get('DB_USER', 'research'),
        os.environ.get('DB_PASSWORD', 'research'),
        os.environ.get('DB_HOST', 'localhost'),
        os.environ.get('DB_PORT', '5432'),
        os.environ.get('DB_NAME', 'quiz')
    ))
    SQLModel.metadata.create_all(quiz_db_engine)

    with open('./dummy_data.json', 'r') as f:
        quizzes = json.load(f)

    correct_answers = []

    with Session(quiz_db_engine) as session:
        for quiz in quizzes:
            quiz_item = Quiz(**quiz)
            session.add(quiz_item)

            for question_order, question in enumerate(quiz['questions']):
                question_item = Question(**question)

                quiz_question = QuizQuestion()
                quiz_question.quiz_id = quiz['id']
                quiz_question.question_id = question['id']
                quiz_question.order = question_order

                session.add(question_item)
                session.add(quiz_question)

                for answer in question['answers']:
                    answer_item = Answer(**answer)
                    session.add(answer_item)

                    if answer['is_correct']:
                        correct_answers.append({
                            'question_id': question['id'],
                            'answer_id': answer['id']
                        })

        try:
            session.commit()
        except sqlalchemy.exc.IntegrityError:
            pass


if __name__ == "__main__":
    create_database()
    insert_dummy_data()
