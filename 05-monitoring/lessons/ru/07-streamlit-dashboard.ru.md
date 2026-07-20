# Дашборд Streamlit

Видео: [Посмотреть этот урок](https://www.youtube.com/watch?v=OrWlgDKZclI&list=PL3MmuxUbc_hLZFNgSad56pDBKK8KO0XIv)

Прежде чем переходить к Grafana, давайте создадим быстрый дашборд прямо в Streamlit. Для многих проектов этого более чем достаточно. Когда вы только начинаете, возможность видеть задержку, стоимость и последние диалоги в одном месте — это уже огромный шаг вперед. Часто Grafana может и вовсе не понадобиться.

Если вы решите остановиться на этом этапе, вам даже не нужен Postgres. Вы могли бы заменить его на SQLite и вообще обойтись без Docker. Мы используем Postgres только потому, что Grafana легче подключается к нему, чем к SQLite, что станет важным позже. Для легковесного проекта связка SQLite и дашборда на Streamlit — отличный вариант.

Я не эксперт в Streamlit. Когда я создаю такие страницы, я описываю то, что хочу, в ChatGPT или другом ИИ-помощнике и позволяю ему написать код верстки. Этот дашборд я намеренно оставил простым, чтобы вы могли прочитать его сверху вниз и понять, что происходит.

Сначала добавим агрегирующие запросы в `db_query.py`.

Добавьте dataclass `Stats` в `db_query.py`:

```python
@dataclass
class Stats:
    total: int
    avg_response_time: float
    total_cost: float
    avg_tokens: float
```

Функция для расчета агрегированной статистики:

```python
def get_stats():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    COUNT(*),
                    AVG(response_time),
                    SUM(cost),
                    AVG(total_tokens)
                FROM conversations
            """)
            row = cur.fetchone()
    finally:
        conn.close()

    return Stats(
        total=row[0],
        avg_response_time=row[1],
        total_cost=row[2],
        avg_tokens=row[3],
    )
```

Создайте `dashboard.py`:

```python
import streamlit as st
from dataclasses import asdict
import pandas as pd
from db_query import get_conversations, get_stats
```

В верхней части мы выводим четыре ключевых показателя, за которыми больше всего стоит следить на старте. Можно вывести гораздо больше, но это хорошая база.

Отображение ключевых метрик:

```python
st.title("Дашборд ассистента по курсу")

stats = get_stats()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Всего диалогов", stats.total)
col2.metric("Среднее время ответа", f"{stats.avg_response_time:.2f}с")
col3.metric("Общая стоимость", f"${stats.total_cost:.4f}")
col4.metric("Среднее кол-во токенов", f"{stats.avg_tokens:.0f}")
```

Для временных графиков мы берем последние 100 диалогов и позволяем Streamlit их отрисовать. Это не самый эффективный способ: мы извлекаем целые записи только для того, чтобы построить график по двум колонкам. Более оптимальный вариант — запрашивать только временную метку и нужное значение. При наших объемах это не критично, поэтому мы выбрали более короткий путь.

Графики стоимости и времени ответа:

```python
records = get_conversations(limit=100)
df = pd.DataFrame([asdict(r) for r in records])

st.subheader("Стоимость во времени")
st.line_chart(df, x="timestamp", y="cost")

st.subheader("Время ответа во времени")
st.line_chart(df, x="timestamp", y="response_time")
```

Последние диалоги:

```python
st.subheader("Последние диалоги")
records = get_conversations(limit=20)

for record in records:
    st.write(f"**{record.prompt[:80]}...**")
    st.write(f"{record.answer[:200]}...")
    st.write(f"Время: {record.response_time:.2f}с | Стоимость: ${record.cost:.4f}")
    st.divider()
```

Запустите дашборд.

Поскольку порт 8501 уже занят чат-приложением, мы будем использовать другой порт:

```bash
uv run streamlit run dashboard.py --server.port 8502
```

Для отображения диалогов нам даже не понадобилась таблица — обычного текста достаточно, чтобы передать суть. Этот простой дашборд уже дает реальное представление о работе системы. Позже мы настроим Grafana для более мощного мониторинга с алертами и более информативными панелями.

[← Запрос данных](06-querying.md) | [Обратная связь от пользователя →](08-user-feedback.md)
