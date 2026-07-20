# Ассистент

Видео: [Посмотреть этот урок](https://www.youtube.com/watch?v=jMO8rqPmR-4&list=PL3MmuxUbc_hLZFNgSad56pDBKK8KO0XIv)

Прежде чем что-либо мониторить, нам нужно то, что мы будем мониторить. Поэтому мы начинаем с RAG-конвейера, который отвечает на вопросы о наших курсах.

Мы не будем строить его с нуля. Мы уже делали это в предыдущих модулях, и процесс состоит из тех же трех шагов, что и всегда.

Сначала мы ищем в FAQ вопросы, наиболее релевантные вопросу пользователя. Затем мы составляем промпт из этого вопроса и найденных документов. Наконец, мы отправляем его в LLM, которая дает нам ответ. Это весь конвейер, и мы используем его "как есть".

## Настройка

Этот конвейер поддерживают два вспомогательных файла. `ingest.py` загружает набор данных FAQ и строит по нему поисковый индекс, а `rag_helper.py` содержит класс `RAGBase`, который выполняет цикл "поиск-промпт-ответ".

Если у вас их нет, скачайте их:

```bash
PREFIX=https://raw.githubusercontent.com/DataTalksClub/llm-zoomcamp/main

wget ${PREFIX}/01-agentic-rag/code/ingest.py
wget ${PREFIX}/01-agentic-rag/code/rag_helper.py
```

Добавьте зависимости:

```bash
uv add python-dotenv
```

Мы используем `python-dotenv` для загрузки `OPENAI_API_KEY` из файла `.env`.

## Создание ассистента

Теперь мы объединяем эти два вспомогательных компонента в одном месте. `assistant.py` загружает данные и строит индекс, затем передает и то, и другое в `RAGBase`. Мы не передаем здесь свои собственные инструкции. `RAGBase` уже поставляется с системным промптом, предписывающим модели отвечать на вопросы по курсу. Второй промпт был бы излишним.

Создайте `assistant.py`.

Импорты:

```python
import sys

from dotenv import load_dotenv
from openai import OpenAI

from ingest import load_faq_data, build_index
from rag_helper import RAGBase
```

Функция для создания ассистента:

```python
def create_assistant():
    load_dotenv()

    documents = load_faq_data()
    index = build_index(documents)

    return RAGBase(
        index=index,
        llm_client=OpenAI(),
    )
```

Протестируйте его из командной строки:

```python
if __name__ == "__main__":
    assistant = create_assistant()

    query = "How do I join the course?"
    if len(sys.argv) > 1:
        query = sys.argv[1]

    answer = assistant.rag(query)
    print(answer)
```

Запустите ассистента:

```bash
uv run python assistant.py
```

Мы будем запускать эту команду снова и снова, и вводить её полностью каждый раз надоедает. Поэтому мы добавим её в `Makefile`.

Добавьте цель `run`:

```makefile
run:
	uv run python assistant.py
```

Теперь мы можем запустить:

```bash
make run
```

Или с произвольным вопросом:

```bash
uv run python assistant.py "How do I join the course?"
```

Вы должны увидеть ответ, выведенный в консоль. Запуск из командной строки удобен для нас, но это не то, как пользователь будет взаимодействовать с системой. Далее мы создадим простой интерфейс с помощью Streamlit.

[← Интро](01-intro.md) | [Чат-приложение →](03-chat-app.md)
