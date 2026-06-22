# RAG Helper

Видео: [Смотреть этот урок](https://www.youtube.com/watch?v=JxaC6Hrym6c&list=PL3MmuxUbc_hLZFNgSad56pDBKK8KO0XIv)

В предыдущих уроках мы строили поток RAG по частям — сначала поиск, затем промпт, затем вызов LLM. Конвейер работает, но каждый раз, когда мы хотим его использовать, нам приходится повторять один и тот же код.

Мы будем использовать этот код на протяжении всего курса, поэтому давайте вынесем его в два переиспользуемых файла:

- [ingest.py](../code/ingest.py) — загрузка данных и создание поискового индекса
- [rag_helper.py](../code/rag_helper.py) — логика RAG (поиск, промпт, LLM)

Тогда в ноутбуках мы сможем просто импортировать эти файлы и использовать их.

## ingest.py

Этот файл отвечает за загрузку данных и создание индекса — все, что нам нужно перед тем, как мы сможем выполнять поиск.

Создайте `ingest.py` с двумя функциями:

```python
import requests
from minsearch import Index

def load_faq_data():
    docs_url = "https://datatalks.club/faq/json/courses.json"
    response = requests.get(docs_url)
    courses_raw = response.json()

    documents = []
    url_prefix = "https://datatalks.club/faq"

    for course in courses_raw:
        course_url = f"""{url_prefix}{course["path"]}"""
        course_response = requests.get(course_url)
        course_response.raise_for_status()
        course_data = course_response.json()

        documents.extend(course_data)

    return documents

def build_index(documents):
    index = Index(
        text_fields=["question", "section", "answer"],
        keyword_fields=["course"]
    )
    index.fit(documents)
    return index
```

Мы будем использовать `load_faq_data()` для загрузки документов и `build_index()` для создания индекса `minsearch`. Позже в этот же файл мы добавим поддержку `sqlitesearch`.

## rag_helper.py

Этот файл содержит логику RAG — те же функции, которые мы написали в предыдущих уроках, но теперь организованные в виде класса.

Мы используем класс, потому что `index` и `openai_client` сейчас являются глобальными переменными. Если перенести функции в отдельный файл, эти глобальные переменные исчезнут. Мы могли бы импортировать их обратно, но это привяжет файл к одному конкретному индексу и одному конкретному клиенту. Это затруднит повторное использование и настройку кода.

Поэтому мы помещаем зависимости внутрь класса. Индекс и клиент LLM становятся аргументами конструктора. Теперь при создании объекта мы можем передать любой индекс или клиент. А поскольку это класс, мы можем позже создать подкласс, чтобы переопределить одну часть, не трогая остальное. Например, мы можем заменить OpenAI на локальную модель.

Создайте `rag_helper.py`:

```python
INSTRUCTIONS = """
Your task is to answer questions from the course participants
based on the provided context.

Use the context to find relevant information and provide accurate
answers. If the answer is not found in the context,
respond with "I don't know."
"""

PROMPT_TEMPLATE = """
QUESTION: {question}

CONTEXT:
{context}
""".strip()
```

Теперь класс:

```python
class RAGBase:
    def __init__(
        self,
        index,
        llm_client,
        instructions=INSTRUCTIONS,
        prompt_template=PROMPT_TEMPLATE,
        course="llm-zoomcamp",
        model="gpt-5.4-mini"
    ):
        self.index = index
        self.llm_client = llm_client
        self.instructions = instructions
        self.course = course
        self.prompt_template = prompt_template
        self.model = model
```

Параметр `index` может быть чем угодно, у чего есть метод `search`, будь то `minsearch`, `sqlitesearch` или что-то другое. У остальных четырех параметров есть значения по умолчанию. Вы передаете `course`, `instructions`, `prompt_template` или `model` только тогда, когда хотите изменить поведение по умолчанию. Позже мы заменим индекс, не трогая код RAG.

Метод `search` делегирует выполнение индексу:

```python
    def search(self, query, num_results=5):
        boost_dict = {"question": 3.0, "section": 0.5}
        filter_dict = {"course": self.course}

        return self.index.search(
            query,
            num_results=num_results,
            boost_dict=boost_dict,
            filter_dict=filter_dict
        )
```

Методы `build_context` и `build_prompt` форматируют результаты поиска:

```python
    def build_context(self, search_results):
        lines = []

        for doc in search_results:
            lines.append(doc["section"])
            lines.append("Q: " + doc["question"])
            lines.append("A: " + doc["answer"])
            lines.append("")

        return "\n".join(lines).strip()

    def build_prompt(self, query, search_results):
        context = self.build_context(search_results)
        return self.prompt_template.format(
            question=query, context=context
        )
```

Метод `llm` отправляет промпт в LLM:

```python
    def llm(self, prompt):
        input_messages = [
            {"role": "developer", "content": self.instructions},
            {"role": "user", "content": prompt}
        ]

        response = self.llm_client.responses.create(
            model=self.model,
            input=input_messages
        )

        return response.output_text
```

И метод `rag` соединяет все это вместе:

```python
    def rag(self, query):
        search_results = self.search(query)
        prompt = self.build_prompt(query, search_results)
        answer = self.llm(prompt)
        return answer
```

## Использование в ноутбуке

Теперь в ноутбуке импортируйте функции и классы из обоих файлов и соберите все вместе:

```python
from dotenv import load_dotenv
load_dotenv()

from ingest import load_faq_data, build_index
from rag_helper import RAGBase
from openai import OpenAI

documents = load_faq_data()
index = build_index(documents)

openai_client = OpenAI()

assistant = RAGBase(
    index=index,
    llm_client=openai_client,
)

answer = assistant.rag("I just discovered the course. Can I join now?")
print(answer)
```

Нам не нужно передавать `instructions` — используются значения по умолчанию из `rag_helper.py`.

Вы можете переопределить их, если хотите другого поведения:

```python
custom_instructions = """
You're a course teaching assistant.
Answer the QUESTION based on the CONTEXT from the FAQ database.
Use only the facts from the CONTEXT when answering the QUESTION.
""".strip()

assistant = RAGBase(
    index=index,
    llm_client=openai_client,
    instructions=custom_instructions,
)
```

Попробуйте другие вопросы:

```python
assistant.rag("How do I get a certificate?")
assistant.rag("Can I still join the course after it started?")
```

Мы будем использовать эти два файла на протяжении всего курса. В следующем уроке мы увидим, как добавить поддержку `sqlitesearch` в `ingest.py` для создания постоянного поискового индекса.

[← LLM](07-llm.md) | [Загрузка данных →](09-data-ingestion.md)
