# Дашборд обратной связи

_Для этого урока нет видео._

Теперь мы собираем два вида обратной связи: оценки пользователей ("пальцы вверх/вниз") и метки релевантности от судьи. Но мы пока их не видим. Давайте добавим их на дашборд Streamlit из урока 07, рядом с панелями стоимости и задержки.

Сначала добавим запросы для обратной связи в `db_query.py`.

Получение распределения релевантности от судьи:

```python
def get_relevance_stats():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT relevance, COUNT(*)
                FROM feedback
                WHERE source = 'judge'
                GROUP BY relevance
            """)
            rows = cur.fetchall()
    finally:
        conn.close()
    return dict(rows)
```

Получение статистики пользовательских оценок:

```python
def get_user_feedback_stats():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    SUM(CASE WHEN score > 0 THEN 1 ELSE 0 END),
                    SUM(CASE WHEN score < 0 THEN 1 ELSE 0 END)
                FROM feedback
                WHERE source = 'user'
            """)
            row = cur.fetchone()
    finally:
        conn.close()
    return row
```

Обновите `dashboard.py`, чтобы отобразить панели обратной связи.

Импортируйте новые функции:

```python
from db_query import get_conversations, get_stats, get_relevance_stats, get_user_feedback_stats
```

Распределение релевантности от судьи:

```python
st.subheader("Оценка релевантности судьей")
relevance = get_relevance_stats()
st.bar_chart(relevance)
```

Обратная связь от пользователей:

```python
st.subheader("Оценки пользователей")
thumbs_up, thumbs_down = get_user_feedback_stats()
col1, col2 = st.columns(2)
col1.metric("Пальцы вверх", int(thumbs_up or 0))
col2.metric("Пальцы вниз", int(thumbs_down or 0))
```

Теперь дашборд показывает качество ответов наряду со стоимостью и скоростью. Проблема лишь в том, что при малом количестве реальных диалогов графики выглядят пустыми. Прежде чем переходить к Grafana, давайте наполним базу данных данными, чтобы нам было на что посмотреть.

[← Встроенный судья](09-built-in-judge.md) | [Синтетические данные →](11-synthetic-data.md)
