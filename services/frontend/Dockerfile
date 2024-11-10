FROM node:slim

RUN mkdir /app
RUN mkdir /app/src
WORKDIR /app

COPY ./services/frontend/start.sh /app

RUN npm install -g http-server -y
RUN chmod +x start.sh

ENTRYPOINT ["./start.sh"]