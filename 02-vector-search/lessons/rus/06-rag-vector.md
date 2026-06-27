# RAG с векторным поиском

Видео: [Посмотреть этот урок](https://www.youtube.com/watch?v=-GBW3g3PVTM&list=PL3MmuxUbc_hLZFNgSad56pDBKK8KO0XIv)

В модуле 1 мы построили RAG-конвейер из трех шагов:

```python
def rag(question):
    search_results = search(question)
    user_prompt = build_prompt(question, search_results)
    return llm(user_prompt)
```

Шаг поиска использовал поиск по ключевым словам. Теперь мы заменим его на векторный поиск.
Поскольку RAG модульный, поиск — это единственный этап, который мы затронем. Создание
промпта и вызов LLM останутся точно такими же, как и были.

## Использование RAGBase

В [модуле 1](../../01-agentic-rag/) мы поместили всю логику RAG в вспомогательный класс
[`RAGBase`](../../01-agentic-rag/code/rag_helper.py). У него есть методы `search`,
`build_prompt` и `llm`, поэтому нам нужно только переопределить `search`.

Скачайте `rag_helper.py` (и `ingest.py`, если вы не скачали его ранее) в свой проект:

```bash
wget https://raw.githubusercontent.com/DataTalksClub/llm-zoomcamp/main/01-agentic-rag/code/rag_helper.py
wget https://raw.githubusercontent.com/DataTalksClub/llm-zoomcamp/main/01-agentic-rag/code/ingest.py
```

Сначала создайте клиент OpenAI:

```python
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
openai_client = OpenAI()
```

Затем скачайте и проиндексируйте данные:

```python
from ingest import load_faq_data, build_index

documents = load_faq_data()
index = build_index(documents)
```

Затем используйте класс `RAGBase`:

```python
from rag_helper import RAGBase

assistant = RAGBase(
    index=index,
    llm_client=openai_client,
)
```

Задайте ему вопрос:

```python
query = "I just found out about the program, can I still sign up?"
assistant.rag(query)
```

Это все еще использует поиск по ключевым словам. Текстовый поиск здесь неплох, так что
ответ уже может выглядеть правильно. Далее мы заменим поиск на векторный.

У нас уже есть:

- Все проиндексированные документы `documents`
- Матрица эмбеддингов `X` со всеми этими документами
- Движок векторного поиска `vindex`

Мы не можем передать `vindex` в RAG "как есть". Текстовый поиск принимает строку запроса
напрямую, но для векторного поиска запрос сначала должен быть представлен в виде вектора.
Поэтому мы создадим подкласс `RAGBase` и переопределим `search`, чтобы кодировать запрос
перед поиском.

Подкласс переопределяет `search`:

```python

class RAGVector(RAGBase):

    def __init__(self, embedder, **kwargs):
        super().__init__(**kwargs)
        self.embedder = embedder

    def search(self, query, num_results=5):
        query_vector = self.embedder.encode(query)
        filter_dict = {"course": self.course}

        return self.index.search(
            query_vector,
            num_results=num_results,
            filter_dict=filter_dict
        )
```

Метод `__init__` добавляет один дополнительный аргумент `embedder` для sentence transformer.
Внутри `search` мы используем его, чтобы превратить запрос в вектор. Затем мы запрашиваем
`vindex` с этим вектором вместо чистого текста. Все остальное наследуется от `RAGBase`.

## Использование

Давайте инициализируем его:

```python
vector_assistant = RAGVector(
    embedder=model,
    index=vindex,
    llm_client=openai_client,
)
```

Попробуйте разные запросы:

```python
vector_assistant.rag("the program has already begun, can I still sign up?")
```

Ответы должны быть близки к тем, что мы получили при поиске по ключевым словам, но
векторный поиск лучше справляется с перефразированными вопросами. Замена была тривиальной,
потому что RAG состоит из трех четких шагов. Тот же прием позволит нам позже сменить
провайдера LLM, переопределив только шаг `llm`.

[← Векторный поиск с minsearch](05-minsearch-vector.md) | [Векторный поиск с sqlitesearch →](07-sqlitesearch-vector.md)
