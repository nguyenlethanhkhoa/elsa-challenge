import json
import os
import traceback
from typing import Callable, Any

from aiokafka import AIOKafkaConsumer
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError

from ..logger import logger


class Event:
    ANSWER_SUBMITTED = 'answer_submitted'
    LEADERBOARD_UPDATED = 'leaderboard_updated'
    USER_JOINED_QUIZ = 'user_joined_quiz'


class EventManager:

    def __init__(self):
        bootstrap_servers = os.environ.get('EVENT_BROKER_SERVERS', 'localhost:9092')
        bootstrap_servers = [server.strip() for server in bootstrap_servers.split(',')]
        logger.info('bootstrap_servers')
        logger.info(bootstrap_servers)
        self.bootstrap_servers = bootstrap_servers

        self.producer = KafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        )

        self.callbacks = {}

    async def async_dispatch(self, consumer, message):
        callbacks = self.callbacks[message.topic]
        for callback in callbacks:
            try:
                await callback(message)
                await consumer.commit()
            except Exception as e:
                e_traceback = traceback.format_exc()
                # TODO: Add log and implement retry methodology
                logger.info(e_traceback)
                pass

    async def async_consume(self, service_name: str):
        topics = self.callbacks.keys()
        topic_names = "\t\n".join(topics)
        logger.info(f'Service {service_name} consumed below events: \n{topic_names}')
        consumer = AIOKafkaConsumer(
            *topics,
            bootstrap_servers=self.bootstrap_servers,
            group_id=service_name,
            enable_auto_commit=False,
            auto_offset_reset="earliest",
        )

        await consumer.start()

        try:
            async for msg in consumer:
                logger.info(f'Service {service_name} received {msg.topic} event')
                try:
                    await self.async_dispatch(consumer, msg)
                    await consumer.commit()
                except Exception as e:
                    # TODO: Add log and implement retry methodology
                    pass
        finally:
            await consumer.stop()

    def listen_on(self, event: str, callback: Callable):
        if event not in self.callbacks:
            self.callbacks[event] = []

        self.callbacks[event].append(callback)

    def dispatch(self, consumer, message):
        callbacks = self.callbacks[message.topic]
        for callback in callbacks:
            try:
                callback(message)
                consumer.commit()
            except Exception as e:
                logger.info('callback exception')
                logger.info(e)
                # TODO: Add log and implement retry methodology
                pass

    def consume(
        self,
        service_name: str,
    ):
        topics = self.callbacks.keys()
        topic_names = "\t\n".join(topics)
        logger.info(f'Service {service_name} consumed below events: \n{topic_names}')
        consumer = KafkaConsumer(
            *topics,
            bootstrap_servers=self.bootstrap_servers,
            auto_offset_reset='earliest',
            value_deserializer=lambda v: json.loads(v.decode('utf-8')),
            enable_auto_commit=False,
            group_id=service_name,
        )

        try:
            for message in consumer:
                logger.info(f'Service {service_name} received {message.topic} event')
                self.dispatch(consumer, message)
        except KafkaError as e:
            logger.info(f"Kafka error: {e}")
        finally:
            consumer.close()

    def produce(self, event: str, message: Any):
        logger.info(f'Produce {event} event')
        self.producer.send(event, value=message)
        self.producer.flush()
