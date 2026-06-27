# Эмбеддинг нашего датасета

Видео: [Посмотреть этот урок](https://www.youtube.com/watch?v=NC89mz1iG4E&list=PL3MmuxUbc_hLZFNgSad56pDBKK8KO0XIv)

В предыдущем уроке мы увидели, как работают эмбеддинги на паре примеров. Теперь применим
их ко всему набору данных FAQ.

## Загрузка данных

В [модуле 1](../../01-agentic-rag/) мы создали файл [`ingest.py`](../../01-agentic-rag/code/ingest.py)
для загрузки данных FAQ.

Скачайте его в свой проект:

```bash
wget https://raw.githubusercontent.com/DataTalksClub/llm-zoomcamp/main/01-agentic-rag/code/ingest.py
```

Мы используем его здесь:

```python
from ingest import load_faq_data

documents = load_faq_data()
```

## Генерация эмбеддингов

Каждый документ представляет собой словарь Python с вопросом и ответом. Мы будем
создавать эмбеддинги для того и другого вместе. Таким образом, запрос сможет
сопоставляться и с текстом вопроса, и с текстом ответа в нашем индексе.

Сформируем один текст для каждого документа:

```python
texts = []

for doc in documents:
    text = doc["question"] + " " + doc["answer"]
    texts.append(text)
```

Теперь сгенерируем эмбеддинги. У нас около 1200 текстов. Мы не будем передавать их
модели все сразу. Это займет много времени, и мы не сможем видеть, что происходит внутри.
Вместо этого мы разделим их на пакеты (batches).

Сначала импортируем `tqdm`, чтобы следить за прогрессом:

```python
from tqdm.auto import tqdm
```

Затем разобьем датасет на пакеты по 50 штук и закодируем каждый пакет:

```python
batch_size = 50
vectors = []

for i in tqdm(range(0, len(texts), batch_size)):
    batch = texts[i:i + batch_size]
    batch_vectors = model.encode(batch)
    vectors.extend(batch_vectors)

len(vectors)
```

В итоге мы получим 1208 векторов. На GPU это происходит быстро. Большинство из нас
работает в Codespaces без GPU, поэтому это займет некоторое время, но это разовая операция.

Превратим их в двухмерный массив (матрицу), где:

- строки — это документы (векторы)
- столбцы — это размерности векторов

```python
import numpy as np
X = np.array(vectors)
```

Вызов `X.shape` вернет (1208, 384) — количество документов против количества размерностей.

[← Эмбеддинги](02-embeddings.md) | [Векторный поиск →](04-vector-search.md)
