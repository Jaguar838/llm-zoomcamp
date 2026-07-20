# Хранение данных в PostgreSQL

Видео: [Посмотреть этот урок](https://www.youtube.com/watch?v=iXRu_AbMtuU&list=PL3MmuxUbc_hLZFNgSad56pDBKK8KO0XIv)

Метрики исчезают при закрытии приложения, поэтому нам нужно место для их хранения. Мы будем сохранять каждый диалог в PostgreSQL, который мы запускаем исключительно для мониторинга. Никакая другая часть системы не взаимодействует с этой базой данных. Мы выбрали Postgres по двум причинам: она хорошо справляется со структурированными данными, и к ней легко подключить Grafana в будущем.

## Запуск PostgreSQL с помощью Docker

Сначала создадим сеть Docker. Postgres и Grafana работают в контейнерах, и Grafana должна обращаться к Postgres по имени, поэтому им нужно находиться в одной сети.

Создайте сеть:

```bash
docker network create monitoring
```

Запустите PostgreSQL с томом (volume) для сохранения данных и подключите его к сети:

```bash
docker run -it \
    --name course-assistant-pg \
    --network monitoring \
    -e POSTGRES_USER=user \
    -e POSTGRES_PASSWORD=password \
    -e POSTGRES_DB=course_assistant \
    -p 5432:5432 \
    -v pgdata:/var/lib/postgresql/data \
    postgres:17
```

Если эти команды кажутся непонятными, вы можете попросить ChatGPT объяснить каждый флаг. Первый модуль нашего [курса по дата-инженерии](https://github.com/DataTalksClub/data-engineering-zoomcamp) содержит более подробную информацию о Docker.

Это длинные команды, которые мы будем запускать часто, поэтому добавим их в `Makefile` из урока 02. Цель `postgres` зависит от `network`, поэтому `make postgres` сначала создаст сеть, а затем запустит контейнер.

Добавьте эти цели:

```makefile
network:
	docker network create monitoring

postgres: network
	docker run -it \
		--name course-assistant-pg \
		--network monitoring \
		-e POSTGRES_USER=user \
		-e POSTGRES_PASSWORD=password \
		-e POSTGRES_DB=course_assistant \
		-p 5432:5432 \
		-v pgdata:/var/lib/postgresql/data \
		postgres:17
```

Теперь можно просто запустить:

```bash
make postgres
```

Для работы с Postgres из Python установим драйвер `psycopg`:

```bash
uv add "psycopg[binary]"
```

## Инициализация базы данных

Таблица будет хранить все данные из нашего `LLMCallRecord`, а также вопрос и название курса. Я назвал её `conversations`, что, возможно, не самое удачное название — я взял его из материалов двухлетней давности. Название `llm_call_records` лучше отражало бы суть, но это название уже закрепилось. Вы можете назвать свою таблицу как угодно.

Стоит сказать пару слов о двух полях. Мы сохраняем `course`, так как один и тот же ассистент может обслуживать несколько курсов. Сейчас это `llm-zoomcamp`, но наличие этой колонки позволит нам не менять структуру таблицы при добавлении других курсов. Поле `timestamp` намеренно сделано с учетом часового пояса (`TIMESTAMP WITH TIME ZONE`). Без этого Grafana позже не сможет правильно выстроить данные на временной шкале.

SQL для создания таблицы:

```sql
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    course TEXT NOT NULL,
    model TEXT NOT NULL,
    instructions TEXT NOT NULL,
    prompt TEXT NOT NULL,
    prompt_tokens INTEGER NOT NULL,
    completion_tokens INTEGER NOT NULL,
    total_tokens INTEGER NOT NULL,
    response_time FLOAT NOT NULL,
    cost FLOAT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL
)
```

Мы можем выполнить этот запрос через `psql` или любой другой инструмент, но давайте создадим Python-скрипт.

Создайте `db_init.py`.

Импорты:

```python
import os
import psycopg
from datetime import datetime

DB_TIMEZONE = datetime.now().astimezone().tzinfo
print(f"Используемый часовой пояс: {DB_TIMEZONE}")
```

Вспомогательная функция для подключения к базе данных.

Она использует переменные окружения со значениями по умолчанию, соответствующими запущенному нами контейнеру Docker:

```python
def get_db_connection():
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        dbname=os.getenv("POSTGRES_DB", "course_assistant"),
        user=os.getenv("POSTGRES_USER", "user"),
        password=os.getenv("POSTGRES_PASSWORD", "password"),
    )
```

Функция инициализации создает таблицу. Параметр `drop=True` сначала удаляет таблицу, что очищает все существующие данные. Это удобно, пока мы еще меняем схему и хотим начать с чистого листа. Но будьте осторожны: вы же не хотите случайно запустить удаление в реальной базе данных.

```python
def init_db(drop=False):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            if drop:
                cur.execute("DROP TABLE IF EXISTS conversations")

            cur.execute("""
                CREATE TABLE conversations (
                    id SERIAL PRIMARY KEY,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    course TEXT NOT NULL,
                    model TEXT NOT NULL,
                    instructions TEXT NOT NULL,
                    prompt TEXT NOT NULL,
                    prompt_tokens INTEGER NOT NULL,
                    completion_tokens INTEGER NOT NULL,
                    total_tokens INTEGER NOT NULL,
                    response_time FLOAT NOT NULL,
                    cost FLOAT NOT NULL,
                    timestamp TIMESTAMP WITH TIME ZONE NOT NULL
                )
            """)
        conn.commit()
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()
    print("База данных инициализирована")
```

Запустите скрипт инициализации:

```bash
uv run python db_init.py
```

Мы запускаем это один раз и не добавляем в `Makefile`. Контейнер `postgres` использует именованный том (`pgdata`), поэтому данные сохраняются после перезапуска. Таблица будет на месте при следующем запуске Postgres. Мы запускаем `db_init.py` снова только при изменении схемы таблицы.

## Сохранение диалогов

Мы хотим вставить запись `LLMCallRecord` в таблицу `conversations`. Колонка `id` имеет тип `SERIAL`, поэтому Postgres назначает её автоматически. Мы добавляем `RETURNING id`, чтобы получить это значение обратно, так как оно понадобится нам позже. Когда пользователь оценивает ответ, мы должны знать, к какому диалогу относится этот отзыв.

SQL-запрос, который мы хотим выполнить:

```sql
INSERT INTO conversations (
    question, answer, course, model, instructions, prompt,
    prompt_tokens, completion_tokens, total_tokens,
    response_time, cost, timestamp
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
)
RETURNING id
```

Создайте `db_save.py`.

Импорты:

```python
from datetime import datetime
from db_init import get_db_connection, DB_TIMEZONE
```

Мы передаем `question` отдельно, а не берем его из записи. Поле `prompt` в записи — это полный текст, отправленный модели, специфичный для вызова LLM. Исходный вопрос, который ввел пользователь — это другое. Мы хотим хранить его в отдельной колонке, чтобы всегда знать, что именно было спрошено. Вы могли бы включить вопрос в промпт, но здесь мы храним их раздельно.

Функция сохранения принимает `LLMCallRecord` и вставляет его в базу данных:

```python
def save_conversation(record, question, course):
    timestamp = datetime.now(DB_TIMEZONE)

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO conversations (
                    question, answer, course, model, instructions, prompt,
                    prompt_tokens, completion_tokens, total_tokens,
                    response_time, cost, timestamp
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                RETURNING id
                """,
                (
                    question,
                    record.answer,
                    course,
                    record.model,
                    record.instructions,
                    record.prompt,
                    record.prompt_tokens,
                    record.completion_tokens,
                    record.total_tokens,
                    record.response_time,
                    record.cost,
                    timestamp,
                ),
            )
            conversation_id = cur.fetchone()[0]
        conn.commit()
    finally:
        conn.close()
    return conversation_id
```

Мы также можем добавить это в блок `__main__` в `assistant.py`, чтобы каждый тест через CLI сохранялся.

Добавьте этот импорт в начало `assistant.py`:

```python
from db_save import save_conversation
```

Затем добавьте вызов сохранения после получения ответа в блоке `__main__`:

```python
save_conversation(assistant.last_call, query, "llm-zoomcamp")
```

Протестируйте:

```bash
uv run python assistant.py "How do I join the course?"
```

Проверьте данные:

```bash
docker exec -it course-assistant-pg psql -U user -d course_assistant \
    -c "SELECT id, question, response_time, cost FROM conversations;"
```

## Интеграция со Streamlit

В `app.py` просто добавьте импорт и одну строку после `assistant.rag()`:

```python
from db_save import save_conversation
```

И далее:

```python
answer = assistant.rag(user_input)
st.success("Готово!")
st.write(answer)

record = assistant.last_call
st.write(f"Время ответа: {record.response_time:.2f}с")
st.write(f"Входные токены (prompt): {record.prompt_tokens}")
st.write(f"Выходные токены (completion): {record.completion_tokens}")
st.write(f"Стоимость: ${record.cost:.4f}")

conversation_id = save_conversation(record, user_input, "llm-zoomcamp")
st.session_state.conversation_id = conversation_id
```

Каждый вопрос и ответ теперь сохраняются в PostgreSQL. Далее мы выполним запрос к данным, чтобы извлечь последние диалоги.

[← Сбор метрик](04-metrics.md) | [Запрос данных →](06-querying.md)
