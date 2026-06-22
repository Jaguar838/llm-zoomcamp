# Сборка промпта

Видео: [Смотреть этот урок](https://www.youtube.com/watch?v=DV4e2n-dIv0&list=PL3MmuxUbc_hLZFNgSad56pDBKK8KO0XIv)

LLM не видит наши документы, если мы их не передадим. Поэтому нам нужно составить промпт, который будет включать вопрос пользователя и результаты поиска.

Когда мы создаем системы ИИ, мы обычно делим промпт на две части:

- Инструкции (также называемые системным промптом): они говорят LLM, как себя вести. Эта часть никогда не меняется и одинакова для каждого запроса.
- Пользовательский промпт: он меняется с каждым запросом. Он содержит актуальный вопрос и извлеченный контекст.

Мы разделяем их, потому что инструкции фиксированы, а пользовательский промпт — нет. Такое разделение позволяет легко переиспользовать фиксированную часть и каждый раз заново собирать изменяемую.

## Инструкции

Инструкции сообщают LLM ее роль и то, как нужно отвечать:

```python
INSTRUCTIONS = """
Your task is to answer questions from the course participants
based on the provided context.

Use the context to find relevant information and provide accurate
answers. If the answer is not found in the context,
respond with "I don't know."
"""
```

Это то, что привязывает ответ к нашим данным и уменьшает количество галлюцинаций.

## Шаблон пользовательского промпта

Шаблон пользовательского промпта содержит заполнители (placeholders) для вопроса и контекста:

```python
USER_PROMPT_TEMPLATE = """
Question:
{question}

Context:
{context}
"""
```

## Сборка контекста

`context` — это отформатированная строка со всеми результатами поиска:

```python
def build_context(search_results):
    lines = []

    for doc in search_results:
        lines.append(doc["section"])
        lines.append("Q: " + doc["question"])
        lines.append("A: " + doc["answer"])
        lines.append("")

    return "\n".join(lines).strip()
```

Каждый документ становится блоком с разделом, вопросом и ответом. Такой формат удобен для чтения моделью LLM. Мы превратили список словарей в одну строку. Это небольшой этап предварительной обработки перед отправкой данных в LLM.

## Сборка промпта

Теперь мы объединяем вопрос с контекстом в пользовательский промпт:

```python
def build_prompt(question, search_results):
    context = build_context(search_results)
    prompt = USER_PROMPT_TEMPLATE.format(
        question=question,
        context=context
    )
    return prompt.strip()
```

Давайте попробуем:

```python
prompt = build_prompt(question, search_results)

print(prompt)
```

Вы должны увидеть промпт с вопросом наверху и несколькими записями FAQ под ним. Это именно то, что мы отправим в LLM.

Промпт выглядит примерно так:

```text
Question:
I just discovered the course. Can I join now?

Context:
General Course-Related Questions
Q: I just discovered the course. Can I still join?
A: Yes, but if you want to receive a certificate, you need to submit your project while we're still accepting submissions.

General Course-Related Questions
Q: Course: I have registered for the LLM Zoomcamp. When can I expect to receive the confirmation email?
A: You don't need it. You're accepted. You can also just start learning and submitting homework...

...
```

Промпт — это мост между поиском и LLM. Плохой промпт позволяет LLM игнорировать контекст и галлюцинировать. Хороший промпт удерживает ответ в рамках предоставленных данных.

Промпт-инжиниринг — это отчасти искусство, отчасти наука. Вы экспериментируете, пробуете разные подходы и смотрите, что работает. Позже в курсе мы разберем метрики оценки, чтобы вы могли измерять эффективность вашего промпта, а не гадать. На данный момент этот шаблон является хорошей отправной точкой.

Код: [notebook.ipynb](../code/notebook.ipynb)

[← Поиск](05-search.md) | [LLM →](07-llm.md)
