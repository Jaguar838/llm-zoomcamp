# Векторный поиск с minsearch

Видео: [Посмотреть этот урок](https://www.youtube.com/watch?v=E7KdO3xmESg&list=PL3MmuxUbc_hLZFNgSad56pDBKK8KO0XIv)

В предыдущем разделе мы выполняли векторный поиск вручную с помощью numpy. Мы превращали
запрос в эмбеддинг, вычисляли скалярные произведения и находили лучшие совпадения.
Писать код для argsort и матричных операций каждый раз надоедает, к тому же так нельзя
фильтровать по курсу. Поэтому вместо этого мы будем использовать библиотеку, которая
все это инкапсулирует.

Мы будем использовать [minsearch](https://github.com/alexeygrigorev/minsearch) — небольшую
библиотеку для поиска в оперативной памяти, которую мы уже использовали в модуле 1 для
текстового поиска. В ней есть класс `VectorSearch` для векторного поиска.

Оба класса имеют одинаковый API:

- `fit` для индексации данных
- `search` для выполнения запросов
- `filter_dict` в методе `search` для фильтрации по ключевым словам

Это самый простой способ начать работу с векторным поиском.

## Создание индекса

У нас уже есть документы и векторы из предыдущего раздела.

Проиндексируем их:

```python
from minsearch import VectorSearch

vindex = VectorSearch(keyword_fields=["course"])
vindex.fit(X, documents)
```

Мы передаем numpy-массив `X` со всеми эмбеддингами и список документов в качестве полезной
нагрузки. Параметр `keyword_fields` работает так же, как и в текстовом индексе `Index`,
поэтому позже мы сможем фильтровать результаты по курсу.

## Поиск

Давайте выполним поиск по вопросу:

```python
query = "I just discovered the course. Can I still join it?"
query_vector = model.encode(query)

results = vindex.search(query_vector, num_results=5)
```

"Под капотом" библиотека делает то же самое, что мы делали вручную. Она вычисляет
скалярное произведение между каждым вектором (после фильтрации) и вектором нашего запроса.

Посмотрим на лучший результат:

```python
results[0]
```

Он должен вернуть документ о присоединении к курсу с опозданием:


```python
{"id": "74eb249bbf",
 "course": "llm-zoomcamp",
 "section": "General Course-Related Questions",
 "question": "I just discovered the course. Can I still join?",
 "answer": "Yes, but if you want to receive a certificate, you need to submit your project while we’re still accepting submissions."}
```

## Фильтрация по курсу

Как и в текстовом индексе, мы можем фильтровать по ключевым полям. Это важно для
пользовательского опыта. Студенту LLM Zoom Camp не интересны ответы из курса по дата-инженерии.
Поэтому мы сначала сужаем поиск до нужного курса, а затем ранжируем результаты только внутри него.

Передайте `filter_dict`:

```python
results = vindex.search(
    query_vector,
    filter_dict={"course": "llm-zoomcamp"},
    num_results=5
)
```

Теперь, когда мы умеем запускать векторный поиск, давайте используем его в RAG.

[← Векторный поиск](04-vector-search.md) | [RAG с векторным поиском →](06-rag-vector.md)
