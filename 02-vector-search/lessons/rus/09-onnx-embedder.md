# Использование ONNX Runtime вместо PyTorch

Видео: [Посмотреть этот урок](https://www.youtube.com/watch?v=BMqa4OsCk58&list=PL3MmuxUbc_hLZFNgSad56pDBKK8KO0XIv)

При переходе в продакшен важно сократить накладные расходы — как зависимости, так и размер
самого развертывания. `sentence-transformers` тянет за собой PyTorch и целую пачку
библиотек Nvidia, что довольно много. ONNX Runtime позволяет использовать ту же модель
без этого лишнего веса.

Чтобы не быть голословным, я создал два пустых проекта. В одном я запустил
`uv add sentence-transformers`, во втором настроил ONNX Runtime.

Затем я измерил размеры виртуальных окружений:

- sentence-transformers: 4.8 ГБ, 58 пакетов
- ONNX Runtime: 147 МБ, 27 пакетов

Это в 33 раза меньше при тех же эмбеддингах и тех же результатах. Часто нам даже не нужно
конвертировать модель самим. Обычно кто-то уже опубликовал ONNX-версию, которую мы можем
просто скачать.

Для разработки и экспериментов `sentence-transformers` вполне подходит. Для продакшена
лучше выбрать более легкий вариант.

Создадим отдельный проект для этого урока:

```bash
mkdir llm-zoomcamp-onnx && cd llm-zoomcamp-onnx
uv init --no-workspace
uv add onnxruntime tokenizers numpy tqdm minsearch
uv add --dev huggingface-hub jupyter
```


`huggingface-hub` нужен только для скачивания модели. Во время работы нам понадобятся
`onnxruntime`, `tokenizers` и `numpy`.

Затем зарегистрируйте ядро (kernel) для этого проекта:

```bash
uv run python -m ipykernel install --user --name llm-zoomcamp-onnx --display-name "llm-zoomcamp-onnx"
```


## Скачивание модели

Мы будем использовать скрипт [download.py](../embed/download.py) из директории `embed/`
для загрузки ONNX-модели с HuggingFace.

Скопируйте его в свой проект и запустите:

```bash
uv run python download.py
```

Это создаст структуру:

```text
models/
  Xenova/
    all-MiniLM-L6-v2/
      tokenizer.json
      model.onnx
```

Это нужно запустить только один раз. После этого файлы модели будут храниться локально.

Добавьте директорию с моделями в `.gitignore`:

```text
models/
```

## Класс Embedder

Для генерации эмбеддингов мы будем использовать скрипт [embedder.py](../embed/embedder.py)
из директории `embed/`.

Также скопируйте его в свой проект.

"Под капотом" он делает четыре вещи:

1. Токенизация — преобразует текст в целочисленные ID и маски внимания.
2. Запуск модели ONNX — выполняет граф модели на CPU.
3. Mean pooling — усредняет эмбеддинги токенов, взвешенные по маске внимания.
4. Нормализация — делит на L2-норму, чтобы векторы можно было сравнивать через
   скалярное произведение.

Вам не обязательно вникать в каждый шаг внутри `embedder.py`. Он предоставляет нам тот
же интерфейс `encode`, что и раньше, но без веса PyTorch.

## Тот же конвейер, без PyTorch

Давайте повторим примеры, которые были раньше, и убедимся, что цифры совпадают.

Сначала сравним два запроса с документом:

```python
from embedder import Embedder

embed = Embedder()

q1 = "Can I still join the course after the start date?"
q2 = "How to install Docker on Windows?"
d  = "You don't need to register. You're accepted. You can also just start learning and submitting homework without registering."

v1 = embed.encode(q1)
v2 = embed.encode(q2)
dv = embed.encode(d)
```

Вычислим сходство:

```python
v1.dot(dv)
```

И второе сходство:

```python
v2.dot(dv)
```

Мы получаем те же результаты, что и раньше. Первая оценка выше, потому что запрос о
присоединении к курсу более похож на документ о регистрации.

Теперь создадим эмбеддинги для датасета FAQ.

Если вы не скачали `ingest.py` ранее, сделайте это сейчас:

```bash
wget https://raw.githubusercontent.com/DataTalksClub/llm-zoomcamp/main/01-agentic-rag/code/ingest.py
```

Загрузим документы:

```python
from ingest import load_faq_data

documents = load_faq_data()
```

Объединим вопрос и ответ для каждого документа:

```python
texts = [doc["question"] + " " + doc["answer"] for doc in documents]
```

Создадим эмбеддинги пакетами:

```python
from tqdm.auto import tqdm
import numpy as np

batch_size = 50
X = []

for i in tqdm(range(0, len(texts), batch_size)):
    batch = texts[i:i + batch_size]
    batch_vectors = embed.encode_batch(batch)
    X.extend(batch_vectors)

X = np.array(X)
```

И выполним поиск:

```python
query = "Can I still join the course after the start date?"
v_query = embed.encode(query)

scores = X.dot(v_query)
idx = np.argmax(scores)

documents[idx]
```

Те же результаты, тот же конвейер, но примерно в 33 раза легче.

## Доступные модели

Все перечисленные ниже модели работают с тем же кодом — просто измените имя модели в
`download.py` и путь в `Embedder()`:

- [Xenova/all-MiniLM-L6-v2](https://huggingface.co/Xenova/all-MiniLM-L6-v2) (384d) — лучшая маленькая модель общего назначения.
- [Xenova/all-MiniLM-L12-v2](https://huggingface.co/Xenova/all-MiniLM-L12-v2) (384d) — выше качество, но медленнее.
- [Xenova/paraphrase-MiniLM-L6-v2](https://huggingface.co/Xenova/paraphrase-MiniLM-L6-v2) (384d) — обнаружение парафраз.
- [Xenova/paraphrase-multilingual-MiniLM-L12-v2](https://huggingface.co/Xenova/paraphrase-multilingual-MiniLM-L12-v2) (384d) — многоязычная.
- [Xenova/multilingual-e5-small](https://huggingface.co/Xenova/multilingual-e5-small) (384d) — многоязычный поиск.
- [Xenova/multilingual-e5-base](https://huggingface.co/Xenova/multilingual-e5-base) (768d) — более мощная многоязычная модель.
- [Xenova/bge-small-en-v1.5](https://huggingface.co/Xenova/bge-small-en-v1.5) (384d) — сильный поисковый движок.
- [Xenova/bge-base-en-v1.5](https://huggingface.co/Xenova/bge-base-en-v1.5) (768d) — еще более мощный поиск.
- [Xenova/gte-small](https://huggingface.co/Xenova/gte-small) (384d) — легкая современная модель.
- [Xenova/gte-base](https://huggingface.co/Xenova/gte-base) (768d) — мощная модель GTE.

Чтобы использовать другую модель, добавьте её в `download.py`, запустите скачивание,
а затем обновите путь:

```python
embed = Embedder("models/Xenova/bge-base-en-v1.5")
vectors = embed.encode("your text here")
print(vectors.shape)
```

Поскольку среда выполнения зависит только от `onnxruntime`, `tokenizers` и `numpy`, вы
можете развертывать её в минимальных окружениях:

- небольшие Docker-образы
- serverless-функции
- edge-устройства

[← Векторный поиск с PGVector](08-pgvector.md) | [Следующие шаги →](10-next-steps.md)
