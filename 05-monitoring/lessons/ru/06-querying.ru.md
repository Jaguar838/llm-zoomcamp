# Запрос данных

Видео: [Посмотреть этот урок](https://www.youtube.com/watch?v=18vEtjPJwLc&list=PL3MmuxUbc_hLZFNgSad56pDBKK8KO0XIv)

Теперь, когда мы сохраняем диалоги, следующий шаг — научиться их считывать. На этом будет строиться наш дашборд. Обычно в таких случаях я открываю Jupyter notebook, чтобы сначала изучить данные и попробовать несколько запросов. Но так как наши данные небольшие и простые, мы пропустим этот этап и сразу перейдем к написанию скрипта.

Создайте `db_query.py`.

Подключимся к той же базе данных:

```python
from dataclasses import dataclass

from db_init import get_db_connection
from metrics import LLMCallRecord
```

## Получение диалогов

Запрос возвращает каждую строку в виде простого кортежа (tuple). Вам придется помнить, что в 4-й колонке находится модель, а в 6-й — промпт. Работать так неудобно. Поэтому мы преобразуем каждую строку обратно в `LLMCallRecord` — тот же dataclass, который мы используем для текущих вызовов.

Вспомогательная функция для преобразования строки БД в `LLMCallRecord`:

```python
def row_to_record(row):
    return LLMCallRecord(
        model=row[4],
        prompt=row[6],
        instructions=row[5],
        answer=row[2],
        prompt_tokens=row[7],
        completion_tokens=row[8],
        total_tokens=row[9],
        response_time=row[10],
        cost=row[11],
        timestamp=row[12],
    )
```

Теперь обновим `get_conversations`, чтобы использовать эту функцию:

```python
def get_conversations(limit=10):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, question, answer, course, model,
                       instructions, prompt,
                       prompt_tokens, completion_tokens, total_tokens,
                       response_time, cost, timestamp
                FROM conversations
                ORDER BY timestamp DESC
                LIMIT %s
                """,
                (limit,),
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    return [row_to_record(row) for row in rows]
```

Мы сортируем по `timestamp`, чтобы получить самые последние вызовы. Стоит учитывать, что по мере роста таблицы отсутствие индекса на `timestamp` может стать проблемой. Впрочем, колонка `id` имеет индекс, и поскольку ID со временем растут, сортировка по `id` была бы быстрее. Либо можно просто добавить индекс на `timestamp`. Для нескольких строк это не имеет значения, поэтому мы пока оставим всё как есть.

Протестируйте скрипт:

```python
if __name__ == "__main__":
    records = get_conversations()
    for record in records:
        print(record)
```

Запустите его:

```bash
uv run python db_query.py
```

Вывод будет представлять собой сплошной текст, который не слишком удобно читать. Тем не менее, это доказывает, что мы можем извлекать данные из базы. Теперь давайте выведем их на дашборд.

[← Хранение данных в PostgreSQL](05-database.md) | [Дашборд Streamlit →](07-streamlit-dashboard.md)
