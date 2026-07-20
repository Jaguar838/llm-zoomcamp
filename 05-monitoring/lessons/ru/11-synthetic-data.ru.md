# Генерация синтетических данных

_Для этого урока нет видео._

Пустой дашборд с тремя диалогами мало что показывает. Можно было бы продолжать задавать приложению вопросы вручную, пока не накопится достаточно данных для графиков, но это долго и скучно. Вместо этого мы напишем небольшой скрипт, который будет "закачивать" фиктивные диалоги в Postgres. Тогда мы сможем увидеть, как ведет себя дашборд при реальном объеме данных.

Скрипт будет вставлять новый диалог каждую секунду, пока мы его не остановим. Это также позволит нам наблюдать за обновлением Grafana почти в реальном времени.

## Образцы данных

Создайте `generate_data.py`.

Импорты и примеры данных:

```python
import time
import random

from metrics import LLMCallRecord
from db_save import save_conversation
from db_feedback import save_feedback
```

Примеры данных:

```python
SAMPLE_QUESTIONS = [
    "How do I install Docker?",
    "Can I still join the course?",
    "What are the prerequisites?",
    "How do I submit homework?",
    "When are the office hours?",
]

SAMPLE_ANSWERS = [
    "You can install Docker by downloading Docker Desktop from the official website.",
    "Yes, you can join at any time. The materials remain available.",
    "You need basic Python knowledge and familiarity with the command line.",
    "Submit your homework through the course portal before the deadline.",
    "Office hours are held weekly. Check the calendar for details.",
]

RELEVANCE = ["RELEVANT", "PARTLY_RELEVANT", "NON_RELEVANT"]
```

## Генерация диалогов

Вспомогательная функция для создания фиктивной записи `LLMCallRecord`:

```python
def fake_record(question, answer):
    return LLMCallRecord(
        model="gpt-5.4-mini",
        prompt=question,
        instructions="",
        answer=answer,
        prompt_tokens=random.randint(50, 200),
        completion_tokens=random.randint(50, 300),
        total_tokens=random.randint(100, 500),
        response_time=random.uniform(0.5, 5.0),
        cost=random.uniform(0.0001, 0.01),
    )
```

## Генерация одного диалога

Вспомогательная функция для случайного выбора оценки ("палец вверх/вниз").

Мы добавляем больше положительных оценок (1), чем отрицательных (-1), чтобы симулировать ситуацию, когда большинство пользователей довольны ответами:

```python
def random_score():
    return random.choice([1, 1, 1, 1, -1])
```

Функция, генерирующая один диалог с необязательной обратной связью:

```python
def generate_one():
    question = random.choice(SAMPLE_QUESTIONS)
    answer = random.choice(SAMPLE_ANSWERS)
    record = fake_record(question, answer)

    conversation_id = save_conversation(
        record, question, "llm-zoomcamp"
    )

    if random.random() < 0.7:
        relevance = random.choice(RELEVANCE)
        save_feedback(
            conversation_id, "judge",
            relevance=relevance,
            explanation=f"Answer is {relevance.lower()}.",
        )

    if random.random() < 0.5:
        score = random_score()
        save_feedback(conversation_id, "user", score=score)
```

## Поток данных в реальном времени

Вставка новых диалогов каждую секунду:

```python
def generate_live():
    print("Запуск генерации данных (Ctrl+C для остановки)...", flush=True)
    while True:
        generate_one()
        time.sleep(1)
```

## Запуск

Точка входа:

```python
if __name__ == "__main__":
    try:
        generate_live()
    except KeyboardInterrupt:
        print("Остановлено.")
```

Запустите скрипт:

```bash
uv run python generate_data.py
```

Скрипт будет генерировать новые данные каждую секунду. Мы будем использовать эти данные в Grafana в следующем уроке. Дашборд "оживет", и графики будут обновляться в реальном времени.

[← Дашборд обратной связи](10-feedback-dashboard.md) | [Grafana →](12-grafana.md)
