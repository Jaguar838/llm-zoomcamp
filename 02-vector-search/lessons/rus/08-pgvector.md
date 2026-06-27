# Векторный поиск с PGVector

Видео: [Посмотреть этот урок](https://www.youtube.com/watch?v=0P54MFyz-mc&list=PL3MmuxUbc_hLZFNgSad56pDBKK8KO0XIv)

Многие реальные базы данных умеют выполнять векторный поиск. В Elasticsearch он есть,
также существуют специализированные хранилища, такие как Qdrant и Chroma. Мы выберем
Postgres. Большинство из нас уже использует его в работе, и курс по дата-инженерии также
использует его. Концепция такая же, как в sqlitesearch, меняется только база данных
"под капотом".

[pgvector](https://github.com/pgvector/pgvector) — это расширение для PostgreSQL, которое
позволяет это реализовать. Установите его, и Postgres сможет выполнять поиск по сходству
векторов. Вдобавок к этому вы получаете обычные возможности для продакшена, такие как
параллельный доступ, транзакции и работа с больными объемами данных.

Мы запустим Postgres с pgvector в Docker.

## Запуск Postgres с pgvector

Скачайте образ и запустите контейнер:

```bash
docker run -it \
    --name pgvector \
    -e POSTGRES_USER=user \
    -e POSTGRES_PASSWORD=pswd \
    -e POSTGRES_DB=faq \
    -v pgvector_data:/var/lib/postgresql/data \
    -p 5432:5432 \
    pgvector/pgvector:pg17
```

В этом образе расширение pgvector уже предустановлено. Флаг `-v` создает именованный
том (volume), чтобы данные сохранялись при перезагрузке контейнера.

## Установка Python-клиента

Установите драйвер:

```bash
uv add psycopg[binary]
```

Мы будем использовать `psycopg` (v3) для подключения и выполнения запросов. Обратите
внимание: это отличается от `psycopg2` — psycopg v3 поддерживает выполнение команд через
`conn.execute()` напрямую, без создания курсора.

## Подготовка данных

Нам нужны документы FAQ и их эмбеддинги.

Вот что мы делали в предыдущих уроках, собранное в один скрипт:

```python
from tqdm.auto import tqdm

from ingest import load_faq_data
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

documents = load_faq_data()
texts = [doc["question"] + " " + doc["answer"] for doc in documents]

batch_size = 50
vectors = []

for i in tqdm(range(0, len(texts), batch_size)):
    batch = texts[i:i + batch_size]
    batch_vectors = model.encode(batch)
    vectors.extend(batch_vectors)
```


Теперь подключаемся к Postgres:

```python
import psycopg

conn = psycopg.connect(
    "postgresql://user:pswd@localhost:5432/faq"
)
conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
```

Вторая строка активирует pgvector. Образ Docker, который мы запустили, — это не просто
обычный Postgres, расширение уже встроено в него, и эта команда его включает. Она
добавляет тип столбца `vector` и операторы поиска по сходству.

## Создание таблицы

Создайте таблицу для хранения документов с их эмбеддингами:

```python
conn.execute("""
    DROP TABLE IF EXISTS documents
""")

conn.execute("""
    CREATE TABLE documents (
        id SERIAL PRIMARY KEY,
        course TEXT,
        section TEXT,
        question TEXT,
        answer TEXT,
        embedding vector(384)
    )
""")
```

Столбец `vector(384)` будет хранить наши 384-мерные эмбеддинги из модели
`all-MiniLM-L6-v2`.

## Вставка документов с эмбеддингами

Давайте вставим документы и их векторы в PGVector:

```python
def vec_to_str(vector):
    return "[" + ",".join(str(x) for x in vector) + "]"

for doc, vec in tqdm(zip(documents, vectors), total=len(documents)):
    conn.execute(
        """
        INSERT INTO documents (course, section, question, answer, embedding)
        VALUES (%s, %s, %s, %s, %s::vector)
        """,
        (doc["course"], doc["section"], doc["question"], doc["answer"],
         vec_to_str(vec))
    )

conn.commit()
```

Мы проходим циклом по документам и вставляем каждый вместе с его эмбеддингом. Мы передаем
вектор в Postgres как строку, поэтому приведение типа `::vector` говорит базе данных
распарсить эту строку обратно в вектор. Мы вызываем `conn.commit()`, чтобы сохранить изменения.

## Поиск по косинусному сходству

Выполним поиск по запросу:

```python
query = "I just discovered the course. Can I still join it?"
query_vector = model.encode(query)
query_str = vec_to_str(query_vector)
```

Найдем наиболее похожие документы:

```python
results = conn.execute(
    """
    SELECT course, question, answer,
           1 - (embedding <=> %s::vector) AS similarity
    FROM documents
    ORDER BY embedding <=> %s::vector
    LIMIT 5
    """,
    (query_str, query_str)
).fetchall()

for row in results:
    print(f"[{row[0]}] {row[1]} (similarity: {row[3]:.4f})")
```

Оператор `<=>` вычисляет косинусное расстояние (1 - косинусное сходство). Мы сортируем по
возрастанию расстояния, чтобы ближайшие векторы шли первыми.

## Фильтрация по курсу

Поскольку это обычный SQL, фильтрация по курсу — это просто дополнительное условие `WHERE`:

```python
results = conn.execute(
    """
    SELECT course, question, answer,
           1 - (embedding <=> %s::vector) AS similarity
    FROM documents
    WHERE course = %s
    ORDER BY embedding <=> %s::vector
    LIMIT 5
    """,
    (query_str, "llm-zoomcamp", query_str)
).fetchall()
```

## Создание индекса для ускорения поиска

До сих пор мы использовали поиск "грубой силой", сравнивая наш запрос с каждой строкой.
Для нашего небольшого набора данных это нормально.

Для более крупного датасета создайте индекс HNSW, чтобы перейти к приближенному поиску:

```python
conn.execute("""
    CREATE INDEX ON documents
    USING hnsw (embedding vector_cosine_ops)
""")
```

Это строит индекс HNSW (Hierarchical Navigable Small World) — тот же современный алгоритм,
который используют специализированные векторные базы данных. Это ускоряет поиск за счет
небольшой потери точности.

## Инкапсуляция логики в функцию

Оформим логику поиска в виде функции для повторного использования:

```python
def pgvector_search(query, course="llm-zoomcamp", num_results=5):
    query_vector = model.encode(query)
    query_str = vec_to_str(query_vector)
    rows = conn.execute(
        """
        SELECT course, section, question, answer
        FROM documents
        WHERE course = %s
        ORDER BY embedding <=> %s::vector
        LIMIT %s
        """,
        (course, query_str, num_results)
    ).fetchall()

    return [
        {"course": r[0], "section": r[1], "question": r[2], "answer": r[3]}
        for r in rows
    ]
```

Попробуйте:

```python
results = pgvector_search("How do I join the course?")
```

## Использование в RAG

Возьмем ту же функцию `search` и перенесем её в класс. Мы передаем соединение Postgres
вместо индекса. Устанавливаем `index=None`, так как `RAGBase` ожидает индекс и в противном
случае выдаст ошибку.

Класс переопределяет метод `search` для выполнения запросов к PGVector:

```python
from rag_helper import RAGBase

class RAGPgVector(RAGBase):

    def __init__(self, embedder, conn, **kwargs):
        super().__init__(index=None, **kwargs)
        self.embedder = embedder
        self.conn = conn

    def search(self, query, num_results=5):
        query_vector = self.embedder.encode(query)
        query_str = vec_to_str(query_vector)

        rows = self.conn.execute(
            """
            SELECT course, section, question, answer
            FROM documents
            WHERE course = %s
            ORDER BY embedding <=> %s::vector
            LIMIT %s
            """,
            (self.course, query_str, num_results)
        ).fetchall()

        return [
            {"course": r[0], "section": r[1], "question": r[2], "answer": r[3]}
            for r in rows
        ]
```

Инициализация клиента OpenAI:

```python
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
openai_client = OpenAI()
```

Создание векторного ассистента:

```python
vector_assistant = RAGPgVector(
    embedder=model,
    conn=conn,
    llm_client=openai_client,
)
```

Попробуйте:

```python
vector_assistant.rag("the program has already begun, can I still sign up?")
```

## Особенности PGVector

Вот как PGVector соотносится с инструментами, которые мы использовали ранее:

- minsearch: не требует настройки, работает в памяти, лучше всего подходит для ноутбуков
  и экспериментов.
- sqlitesearch: не требует настройки, постоянное хранение в файле SQLite, лучше всего
  подходит для пет-проектов.
- PGVector: требует Docker, база данных Postgres с параллельным доступом, справляется
  с миллионами записей, лучше всего подходит для продакшен-систем.

Выбирайте PGVector, когда вам нужны возможности для промышленной эксплуатации:

- параллельное чтение и запись
- транзакции
- интеграция с существующим приложением на базе Postgres

[← Векторный поиск с sqlitesearch](07-sqlitesearch-vector.md) | [Использование ONNX Runtime →](09-onnx-embedder.md)
