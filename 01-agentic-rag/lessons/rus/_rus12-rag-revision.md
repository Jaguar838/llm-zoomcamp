# Краткий обзор RAG (Опционально)

Видео: [Смотреть этот урок](https://www.youtube.com/watch?v=gH8fB-6Emmo&list=PL3MmuxUbc_hLZFNgSad56pDBKK8KO0XIv)

Прежде чем говорить об агентах, давайте настроим конвейер RAG, который мы построили в первой части.

На наших курсах много участников. Они задают одни и те же вопросы снова и снова, поэтому мы ведем документ FAQ и направляем студентов к нему. RAG берет этот FAQ и находит запись, соответствующую вопросу. Затем он отправляет эту запись в LLM, чтобы она могла ответить. Таким образом, студент получает ответ сразу, а не листает длинный документ.

Мы будем использовать два вспомогательных файла (helpers), которые мы определили ранее:

- [`rag_helper.py`](../code/rag_helper.py) — класс `RAGBase`, оборачивающий поиск, создание промпта и вызов LLM.
- [`ingest.py`](../code/ingest.py) — функции `load_faq_data` и `build_index` для загрузки FAQ и создания индекса `minsearch`.

Если вы проходите вторую часть как отдельный воркшоп (без первой части), скачайте их в свой проект:

```bash
wget https://raw.githubusercontent.com/DataTalksClub/llm-zoomcamp/main/01-agentic-rag/code/rag_helper.py
wget https://raw.githubusercontent.com/DataTalksClub/llm-zoomcamp/main/01-agentic-rag/code/ingest.py
```

## Настройка RAG

Настройте клиент OpenAI:

```python
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
openai_client = OpenAI()
```

Загрузите данные и создайте поисковый индекс:

```python
from rag_helper import RAGBase
from ingest import load_faq_data, build_index

documents = load_faq_data()
index = build_index(documents)
```

Создайте ассистента:

```python
instructions = """
You're a course teaching assistant.
Answer the QUESTION based on the CONTEXT from the FAQ database.
Use only the facts from the CONTEXT when answering the QUESTION.
""".strip()

assistant = RAGBase(
    index=index,
    llm_client=openai_client,
    instructions=instructions,
)
```

## Тестирование

Давайте попробуем задать вопрос:

```python
assistant.rag("How do I run Ollama locally?")
```

Это работает нормально. Поиск находит релевантные записи FAQ об Ollama, и LLM дает хороший ответ.

Теперь попробуйте что-то немного другое:

```python
assistant.rag("How do I run Olama locally?")
```

Слово «Olama» не совпадает со словом «Ollama» в нашем индексе. Мы используем лексический поиск, поэтому он ищет точное слово и ничего не находит. LLM получает эти плохие результаты и либо говорит «Я не знаю», либо отвечает нерелевантной информацией.

Это ограничение фиксированного конвейера. Поиск запускается один раз с точным запросом, который ввел пользователь, и второго шанса нет. Конвейер не знает, что поиск не удался, поэтому не может попробовать снова с исправленным запросом.

Нам нужно что-то более умное. Нам нужен агент.

[← Агенты (введение в часть 2)](11-agents-intro.md) | [Вызов функций →](13-function-calling.md)
