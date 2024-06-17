# Statistic Bot

This repository contains a statistic bot that uses MongoDB for storage. The bot is containerized using Docker and can be run locally using Docker Compose.

## Prerequisites

Before you start, ensure you have the following installed on your machine:

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)

## Setup

1. **Clone the repository**:

    ```bash
    git clone https://github.com/yourusername/statistic-bot.git
    cd statistic-bot
    ```

2. **Create a `.env` file**:

    In the root directory of the repository, create a file named `.env` and add the following environment variables:

    ```dotenv
    BOT_TOKEN=your_bot_token
    GROK_API_KEY=your_grok_api_key
    MONGO_DB=bot_db
    MONGO_CONN=mongo:27017/
    ```

    Replace `your_bot_token` and `your_grok_api_key` with your actual bot token and Grok API key.

3. **Build and run the stack**:

    Use Docker Compose to build and run the services defined in the `docker-compose.yml` file:

    ```bash
    docker-compose up --build
    ```

    This command will start the MongoDB and statistic bot services. The MongoDB service will be available at `mongo:27017`.

## Services

- **MongoDB**:
  - Container Name: `mongo`
  - Image: `mongo:7.0.11-jammy`
  - Ports: `27017:27017`
  - Volume: `mongo:/data/db`
  - Logging: JSON file with a max size of 10MB and a maximum of 50 files

- **Statistic Bot**:
  - Container Name: `staticsbot`
  - Build Context: Current directory (.)
  - Environment Variables: Loaded from `.env` file
  - Depends on: `mongo` service
  - Logging: JSON file with a max size of 10MB and a maximum of 50 files

## Stopping the Stack

To stop the stack, press `Ctrl+C` in the terminal where the stack is running. To remove the containers, networks, and volumes defined in `docker-compose.yml`, run:

```bash
docker-compose down
```
