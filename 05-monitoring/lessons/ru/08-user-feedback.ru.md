# Обратная связь от пользователя

Видео: [Посмотреть этот урок](https://www.youtube.com/watch?v=GEifsHDadBw&list=PL3MmuxUbc_hLZFNgSad56pDBKK8KO0XIv)

До сих пор мы собирали технические метрики: время ответа, количество токенов и стоимость. Но всё это не говорит нам о том, был ли ответ действительно хорошим. Люди, использующие систему, знают это — так же, как вы можете оценить ответ в ChatGPT. Поэтому мы добавим кнопки "палец вверх" и "палец вниз" и будем записывать, на что нажимают пользователи.

Сбор такой обратной связи полезен не только для дашборда. Эти данные можно использовать для оценки (evaluation). Если пользователь отметил ответ как хороший, судья, которого вы построили в предыдущем модуле, в идеале должен быть с ним согласен. Это согласие дает вам данные для калибровки вашего автоматического судьи.

Этот сигнал довольно зашумленный. Кто-то может нажать кнопку случайно или оценить плохой ответ как хороший (я сам делаю так в демо-версии). Но это всё равно ценно для создания набора данных для оценки. А на дашборде всплеск отрицательных оценок за последний час — четкий сигнал: идите и проверьте, что сломалось.

## Таблица обратной связи

Обратная связь может поступать от человека или, позже, от LLM-судьи. Поэтому мы используем одну таблицу `feedback` с колонкой `source`, в которой записывается источник каждой записи. На данный момент `source` будет `"user"`, и мы будем сохранять оценку.

Добавьте новую функцию `init_feedback` в `db_init.py`:

```python
def init_feedback():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS feedback")

            cur.execute("""
                CREATE TABLE feedback (
                    id SERIAL PRIMARY KEY,
                    conversation_id INTEGER REFERENCES conversations(id),
                    source TEXT NOT NULL,
                    relevance TEXT,
                    explanation TEXT,
                    score INTEGER,
                    timestamp TIMESTAMP WITH TIME ZONE NOT NULL
                )
            """)
        conn.commit()
    finally:
        conn.close()
```

Обновите блок `__main__`, чтобы вызвать обе функции инициализации:

```python
if __name__ == "__main__":
    init_db()
    init_feedback()
    print("База данных инициализирована")
```

Снова запустите скрипт инициализации:

```bash
uv run python db_init.py
```

- `source`: `"user"` для человеческой обратной связи, `"judge"` для оценок от LLM
- `score`: +1 для "пальца вверх", -1 для "пальца вниз"
- `relevance` и `explanation`: будут использоваться позже встроенным судьей

## Сохранение обратной связи

Создайте `db_feedback.py`:

```python
from datetime import datetime
from db_init import get_db_connection, DB_TIMEZONE

def save_feedback(conversation_id, source, relevance=None,
                  explanation=None, score=None):
    timestamp = datetime.now(DB_TIMEZONE)

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO feedback (
                    conversation_id, source, relevance,
                    explanation, score, timestamp
                ) VALUES (
                    %s, %s, %s, %s, %s, %s
                )
                """,
                (conversation_id, source, relevance,
                 explanation, score, timestamp),
            )
        conn.commit()
    finally:
        conn.close()
```

## Добавление кнопок в приложение

Мы уже сохраняем диалоги в `app.py` из урока 05. Чтобы привязать отзыв к правильному ответу, нам нужен `conversation_id`, который возвращает `save_conversation`. Мы будем хранить его в `st.session_state`. Streamlit перезапускает весь скрипт при каждом клике, и состояние сессии (session state) — это способ передать ID от ответа к нажатию кнопки.

Добавьте этот импорт в `app.py`:

```python
from db_feedback import save_feedback
```

Обновите кнопку "Спросить", чтобы сохранять ID диалога:

```python
if st.button("Спросить"):
    with st.spinner("Обработка..."):
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

Теперь добавьте кнопки обратной связи:

```python
col1, col2 = st.columns(2)
with col1:
    if st.button("+1"):
        cid = st.session_state.conversation_id
        save_feedback(cid, "user", score=1)
        st.write("Спасибо!")

with col2:
    if st.button("-1"):
        cid = st.session_state.conversation_id
        save_feedback(cid, "user", score=-1)
        st.write("Спасибо за отзыв!")
```

Теперь пользователи могут оценивать каждый ответ. Мы показываем кнопки постоянно, а не только после получения ответа. Было бы правильнее показывать их только тогда, когда ответ готов. Но это добавит логику, которую я бы не хотел вносить в это небольшое приложение. Если вы хотите это реализовать, попросите ИИ-помощника добавить условие появления кнопок только при наличии ответа.

Далее мы добавим второй источник обратной связи в ту же таблицу. LLM-судья будет оценивать ответы автоматически, не дожидаясь нажатия кнопок пользователем.

[← Дашборд Streamlit](07-streamlit-dashboard.md) | [Встроенный судья →](09-built-in-judge.md)
