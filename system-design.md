# Real-Time Quiz Feature System Design Document

## 1. Overview
This document describes the architecture and design considerations for a real-time quiz feature in an English learning application. The feature enables users to join quiz sessions, answer questions, see real-time score updates, and view live leaderboards. The system is designed to support up to 10 million concurrent users.

## 2. Functional Requirements
- **User Participation**: Users join a quiz session via a unique quiz ID. Multiple users can join the same session simultaneously.
- **Real-Time Score Updates**: User scores update in real time as they submit answers, maintaining accuracy and consistency.
- **Real-Time Leaderboard**: Leaderboard displays participants standings, updating immediately as scores change.

## 3. Non-Functional Requirements
- **Scalability**: The system must handle large numbers of users and quiz sessions.
- **Performance**: Components must perform well under heavy load, optimizing resources and minimizing latency.
- **Reliability**: Resilience to failures is crucial, ensuring graceful error handling and data consistency.
- **Monitoring and Observability**: System performance and issues must be trackable and diagnosable, with comprehensive logging and alerting.

## 4.Assumptions:
- There are 10 million users as total and 100.000 concurrent using users at peak
- The maximum concurrent users can join the same quiz session is 10.000 
- Each user submits an answer every 10-20 seconds
- Each quiz session have an average duration of 1 - 1.5 hours
-  the system should be capable of hosting 1.000.000 simultaneous quiz sessions.

## 4. System Architecture
The architecture consists of the following components:

- Load Balancer (AWS ALB)
- Quiz Service (Python + Fastapi + SocketIO)
- Event Streaming (Kafka)
- Quiz Database (Postgres)
- Cache (Redis)
- Message Broker (Redis)
- Task Queue (RabbitMQ)
- Leaderboard Service (Python)
- Leaderboard Database (Postgres)
- Data Saver (Python)
- Logging and Maintenance (ELK Stack)

## 5. Component Design

### 5.1 Load Balancer
- **Purpose**: Distributes incoming traffic across Quiz Service instances, supporting horizontal scaling.

### 5.2 Quiz Service
- **Functionality**:
  - Hosts a Socket.IO server to manage user connections and interactions.
  - Sends `user_joined_quiz` and `answer_submitted` events to Kafka for processing by the Leaderboard Service and Data Saver.
  - Receives leaderboard updates from Kafka by listening to event `leaderboard_updated` to broadcast to participants.
  - Manages user sessions and broadcasts leaderboard updates to the respective quiz rooms.
- **Scalability**: Horizontally scalable, with Redis Pub/Sub or Redis Streams to synchronize instances.
- **High Availability**: Uses Redis-based message brokering to prevent single points of failure in Socket.IO connections.

### 5.3 Kafka for Event Streaming
- **Functionality**:
  - Acts as an event stream for `user_joined_quiz`, `answer_submitted` and `leaderboard_updated` events.
  - Distributes events to corresponding services.
  - Provides an event queue for `leaderboard_updated` notifications.
- **Partitioning Strategy**: Events are partitioned by quiz ID to parallelize event processing, maintaining message order within each partition.

### 5.4 Quiz Database
- **Purpose**: Stores quiz metadata (e.g., quiz details, questions, answers).
- **Optimization**: Sharded by quiz ID to balance load across multiple database instances. Read replicas are used to handle frequent read requests without affecting the primary database.

### 5.5 Cache (Redis)
- **Purpose**:
  - Caches frequently accessed quiz metadata to reduce load on the Quiz Database.
  - Stores the current leaderboard and answers, reducing latency for leaderboard recalculations.
- **Sharding**: Quiz metadata and leaderboard data are sharded by quiz ID to optimize load distribution and access times.

### 5.6 Message Broker (Redis)
- **Purpose**: Ensures synchronization between Quiz Service nodes, supporting horizontal scaling of WebSocket connections.
- **High Availability**: A separate Redis instance is used for Pub/Sub messaging to isolate it from caching operations, reducing the chance of bottlenecks.

### 5.7 Task Queue
- **Purpose**: Manages non-real-time tasks such as loading metadata into cache and handling database operations.

### 5.8 Leaderboard Service
- **Functionality**:
  - Listens to `user_joined_quiz` and `answer_submitted` events from Kafka.
  - Recalculates leaderboard scores and pushes updates to Redis for caching.
  - Notifies the Quiz Service to broadcast leaderboard updates to users.

### 5.9 Scoring Database
- **Purpose**: Stores user answers and leaderboard data for each quiz, maintaining long-term data integrity.
- **Partitioning**: Sharded by user ID to manage high write throughput and allow parallel read/write operations.

### 5.10 Data Saver
- **Purpose**: Separate updating and storing data into 2 different processes to maintain the low latency of updating leaderboard process
- **Functionality**: Listens for `user_joined_quiz` and `answer_submitted` events, saving them to the Scoring Database.
- **Reliability**: Ensures data persistence by synchronizing data across different services, maintaining integrity and consistency.

### 5.11 Logging and Maintenance (ELK Stack)
- **Purpose**: Provides comprehensive logging and monitoring for tracing and diagnosing issues across services.
- **Metrics and Alerting**: Tracks key metrics (e.g., user connection rates, answer submission rates, latency). Alerts trigger auto-scaling policies when resource utilization or latency surpasses predefined thresholds.

## 6. Data Flow

### User Joins Quiz
1. A user joins a quiz session, connecting via WebSocket.
2. The Quiz Service sends a `user_joined_quiz` event to Kafka for processing by the Leaderboard and Data Saver services.

### User Submits Answer
1. The Quiz Service receives an answer from a user and sends an `answer_submitted` event to Kafka.
2. Kafka routes this event to the Leaderboard Service for score calculation and the Data Saver for storage.
3. The Leaderboard Service recalculates the leaderboard and sends an update to Redis, which is broadcast to the Quiz Service.

### Leaderboard Update
1. Once the leaderboard is recalculated, the Quiz Service retrieves it from Redis and broadcasts it to all users in the quiz session.

## 7. Scalability and Performance Considerations
- **Quiz Service Horizontal Scaling**: Redis-backed message brokering supports horizontal scaling of the Quiz Service nodes for WebSocket connections.
- **Partitioned Kafka Processing**: Partitioning Kafka by quiz ID allows for parallel processing, distributing the event load effectively.
- **Sharded Caching**: Redis caching of metadata and leaderboard data is sharded to reduce cache latency and minimize database load.
- **Throttled Leaderboard Calculations**: Leaderboard recalculations are throttled to reduce load on Kafka and Redis, ensuring efficiency.

## 8. Reliability and Fault Tolerance
- **Redis for Resilience**: Separate Redis instances for caching and Pub/Sub messaging isolate critical services, enhancing fault tolerance.
- **Retry Mechanisms in Kafka**: Kafka’s built-in retry mechanisms prevent message loss, ensuring data consistency even if a component fails.
- **Data Saver for Persistent Storage**: The Data Saver ensures data integrity, providing a reliable backup of user actions and scores.

## 9. Monitoring and Observability
- **Distributed Tracing**: OpenTelemetry or similar tools trace user journeys across services, identifying latency sources.
- **ELK Stack for Centralized Logging**: Logs are centrally stored in the ELK stack, allowing for efficient query and filtering during troubleshooting.
- **Automated Alerting and Scaling**: Alerts based on metrics like WebSocket connection count and Redis latency trigger autoscaling to manage peak loads.

## 10. Trade-Offs and Future Improvements
- **Caching Overhead vs. Freshness**: Redis caching reduces latency but may present stale data; optimized cache invalidation is essential.
- **Throttling vs. Real-Time Accuracy**: Throttling leaderboard recalculations balances performance but might slightly delay leaderboard updates.
- **Scaling Complexity**: Horizontal scaling of Redis and Kafka introduces configuration complexity but ensures stability and resilience under high load.

This design, focusing on distributed processing, sharding, and message-driven architecture, aims to provide a robust, high-performance system for real-time quiz functionality while supporting the scalability, reliability, and observability essential for managing millions of users.