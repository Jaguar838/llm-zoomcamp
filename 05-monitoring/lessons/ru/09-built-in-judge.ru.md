# Встроенный судья

Видео: [Посмотреть этот урок](https://www.youtube.com/watch?v=YLOLQyrMDuY&list=PL3MmuxUbc_hLZFNgSad56pDBKK8KO0XIv)

В предыдущем модуле мы использовали LLM в качестве судьи для офлайн-оценки. Одна LLM оценивает работу другой. Эту же идею можно применить и онлайн.

После каждого ответа мы спрашиваем судью, насколько этот ответ релевантен вопросу. Это дает нам автоматический сигнал качества для каждого ответа. Нам не нужно ждать, пока кто-то нажмет на "палец вверх" или "вниз".

Есть одно существенное отличие от офлайн-оценки. Тогда у нас была "эталонная истина" (ground truth) — образцовый ответ, с которым можно было сравнить результат. Судья мог сопоставить наш ответ с заведомо правильным. В онлайн-режиме у нас такого эталона нет.

Теперь судья видит только вопрос и ответ. Он должен вынести вердикт самостоятельно. Это более сложная задача, поэтому в инструкциях мы более тщательно описываем, как выглядит хороший ответ.

## Добавление оценки релевантности

Мы используем структурированный вывод (structured output), чтобы судья возвращал четкую метку вместо произвольного текста, который пришлось бы парсить.

Нам понадобится файл `evaluation_utils` из модуля 04.

Скачайте его, если у вас его нет:

```bash
PREFIX=https://raw.githubusercontent.com/DataTalksClub/llm-zoomcamp/main
wget ${PREFIX}/04-evaluation/code/evaluation_utils.py
```

Создайте `judge.py`:

```python
import json

from pydantic import BaseModel
from typing import Literal
from openai import OpenAI
from dotenv import load_dotenv

from evaluation_utils import llm_structured_retry

class RelevanceVerdict(BaseModel):
    relevance: Literal["NON_RELEVANT", "PARTLY_RELEVANT", "RELEVANT"]
    explanation: str

judge_instructions = """
You are an expert evaluator for a RAG system.
Analyze the relevance of the generated answer to the given question.

Classify the answer as:
- RELEVANT: the answer addresses the question
- PARTLY_RELEVANT: the answer partially addresses the question
- NON_RELEVANT: the answer does not address the question
""".strip()

judge_prompt = """
Question: {question}
Generated Answer: {answer}
""".strip()
```

Поле `explanation` (объяснение) важно, даже если мы не всегда его используем. Требование объяснить решение заставляет судью "рассуждать" об ответе перед тем, как поставить метку. Это обычно повышает качество оценки.

Мы вызываем судью через `llm_structured_retry` — вспомогательную функцию из предыдущего модуля. Она аналогична `llm_structured`, но выполняет повторные попытки в случае сбоя.

Изредка модель возвращает JSON, который не совсем соответствует запрошенной структуре. С компактными моделями OpenAI это случается редко, может быть один-два раза на моей практике. Это чаще встречается у других провайдеров (несколько случаев на тысячу вызовов). Повторные попытки как раз закрывают эти случаи.

Функция оценки.

Добавьте это в `judge.py`:

```python
def evaluate_relevance(question, answer, client=None):
    if client is None:
        client = OpenAI()

    prompt = judge_prompt.format(
        question=question,
        answer=answer
    )

    result, usage = llm_structured_retry(
        client,
        judge_instructions,
        prompt,
        RelevanceVerdict,
    )

    return result.relevance, result.explanation
```

Протестируйте:

```python
if __name__ == "__main__":
    load_dotenv()

    question = "Can I still join the course?"
    answer = "Yes, you can still join. The course is self-paced."

    relevance, explanation = evaluate_relevance(question, answer)
    print(relevance)
    print(explanation)
```

Запустите скрипт:

```bash
uv run python judge.py
```

Этот судья намеренно сделан простым, поэтому относитесь к его вердиктам с осторожностью. Иногда он может назвать слабый ответ релевантным или наоборот. Когда вы будете строить своего судью, уделите время промпту, пока метка "релевантно" не станет действительно означать релевантность.

Путь к этому — калибровка (alignment). Вы собираете метки от ваших пользователей или размечаете выборку самостоятельно. Затем вы настраиваете судью до тех пор, пока его мнение не совпадет с вашим. У команды Evidently есть отличное видео на эту тему на нашем канале DataTalks Club. Ищите "автоматизированная оптимизация промптов" ([automated prompt optimization](https://www.youtube.com/watch?v=uMNYVw4jh-8)).

## Сохранение отзывов судьи в базу данных

Мы уже создали таблицу `feedback` в уроке 08. В ней есть колонка `source`, которая указывает источник отзыва.

У нас уже есть `db_feedback.py` с функцией `save_feedback`. Нам просто нужно вызвать её с параметром `source="judge"`.

## Интеграция с приложением

В `app.py` вызывайте судью после получения ответа и сохраняйте результат:

```python
from judge import evaluate_relevance
from db_feedback import save_feedback
```

И далее:

```python
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

relevance, explanation = evaluate_relevance(user_input, answer)
save_feedback(conversation_id, "judge",
                relevance=relevance, explanation=explanation)
st.write(f"Релевантность: {relevance}")
st.write(f"Объяснение: {explanation}")
```

Теперь каждый ответ сопровождается автоматической меткой релевантности. Она попадает в ту же таблицу `feedback`, что и оценки пользователей из урока 08. Поскольку и те, и другие данные находятся в одном месте, мы можем сравнивать мнение судьи с мнением людей. И если на дашборде релевантность начнет падать, значит, что-то не так с поиском или промптом.

Несколько советов для систем сложнее демо-примера:

- Судья — это дополнительный вызов LLM на каждый вопрос, что увеличивает задержку и стоимость. В реальной системе это должно работать асинхронно: сначала отдайте ответ пользователю, а затем оценивайте его в фоновом режиме.
- Отслеживайте стоимость работы самого судьи отдельно, так как он тоже тратит деньги. Таблица `judge_feedback` с полями релевантности, объяснения и стоимости была бы хорошим решением.
- Когда у вас появится реальный трафик, не обязательно оценивать каждый ответ. Используйте выборку (sampling), например, оценивайте один из десяти ответов — вы всё равно получите нужный сигнал, но за гораздо меньшие деньги.

Здесь мы запускаем его последовательно для каждого вызова, чтобы код оставался простым.

[← Обратная связь от пользователя](08-user-feedback.md) | [Дашборд обратной связи →](10-feedback-dashboard.md)
