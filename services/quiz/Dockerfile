FROM python:3.10-slim

RUN mkdir /app
WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

RUN mkdir /app/shared
COPY shared/shared /app/shared/shared
COPY shared/requirements.txt /app/shared/
COPY shared/setup.py /app/shared/
WORKDIR /app/shared
RUN pip install .

WORKDIR /app
COPY dummy_data.json .
COPY services/quiz/main.py .
COPY services/quiz/setup.py .
COPY services/quiz/start.sh .

RUN chmod +x start.sh

CMD [ "./start.sh" ]
