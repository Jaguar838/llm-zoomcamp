# Docker Compose

_Для этого урока нет видео._

К этому моменту у нас запущены три компонента: PostgreSQL, Grafana и приложение Streamlit. Запускать каждый из них вручную можно, но это неудобно. Нужно помнить о сети и вводить длинные команды. К тому же, при повторном запуске Docker может пожаловаться, что контейнер с таким именем уже существует, и вам придется его удалять.

Docker Compose позволяет описать все три сервиса в одном файле и запустить их одновременно в общей сети. Вместо множества команд вы используете одну.

## Структура проекта

Схема проекта:

```text
code/
├── docker-compose.yaml
├── Dockerfile
├── .env
├── pyproject.toml
├── uv.lock
├── .python-version
├── app.py           # Приложение Streamlit
├── assistant.py     # RAG-конвейер + LLM
├── db_init.py       # Инициализация БД
├── db_save.py       # Сохранение диалогов
└── dashboard.py     # Дашборд Streamlit
```

## Dockerfile

Для приложения Streamlit нужен собственный контейнер:

```dockerfile
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH"

COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --locked

COPY . .

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

## Переменные окружения

Файл `.env` хранит конфигурацию:

```text
POSTGRES_DB=course_assistant
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_HOST=postgres
OPENAI_API_KEY=your-key-here
```

## Docker Compose

Файл Compose определяет все три сервиса в одной сети:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:17
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    depends_on:
      - postgres
```

Сервис Streamlit собирается из Dockerfile:

```yaml
  streamlit:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      - POSTGRES_HOST=postgres
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    ports:
      - "8501:8501"
    depends_on:
      - postgres

volumes:
  postgres_data:
  grafana_data:
```

## Запуск всего стека

Запустите все сервисы:

```bash
docker-compose up
```

Инициализируйте базу данных:

```bash
uv run python db_init.py
```

Приложение доступно по адресу `http://localhost:8501`, а Grafana — по адресу `http://localhost:3000` (логин: admin / admin).

Чтобы остановить работу:

```bash
docker-compose down
```

Данные в PostgreSQL и Grafana сохраняются между перезапусками благодаря томам (volumes) Docker.

[← Grafana](12-grafana.md) | [Следующие шаги →](14-next-steps.md)
