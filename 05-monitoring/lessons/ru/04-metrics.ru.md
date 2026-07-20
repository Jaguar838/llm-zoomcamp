# Сбор метрик

Видео: [Посмотреть этот урок](https://www.youtube.com/watch?v=JGh6-DqaueA&list=PL3MmuxUbc_hLZFNgSad56pDBKK8KO0XIv)

Наше чат-приложение работает, но каждый вызов — это "черный ящик". Мы не знаем, сколько времени он занял, сколько токенов использовал и во сколько обошелся. Чтобы мониторить систему, мы должны сначала фиксировать эти показатели в реальном времени. Поэтому мы инструментируем наш RAG-конвейер.

Создайте `metrics.py`.

Импорты:

```python
import time
from dataclasses import dataclass, field
from datetime import datetime

from rag_helper import RAGBase
```

Каждый вызов генерирует набор значений, которые мы хотим хранить вместе. Мы могли бы передавать их как словарь, но тогда пришлось бы помнить все ключи. `dataclass` четко описывает поля, так что любой, кто читает код, сразу видит, что именно мы записываем для каждого вызова.

Dataclass `LLMCallRecord`:

```python
@dataclass
class LLMCallRecord:
    model: str
    prompt: str
    instructions: str
    answer: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    response_time: float
    cost: float
    timestamp: datetime = field(default_factory=datetime.now)
```

## Расчет стоимости

Далее нам нужно рассчитать стоимость каждого вызова. Провайдер берет плату за миллион входных токенов и за миллион выходных токенов. Мы умножаем количество токенов на соответствующий тариф и делим на миллион. Объект `usage` поступает напрямую из ответа LLM и содержит количество токенов для только что сделанного вызова.

```python
def calculate_cost(model, usage):
    cost = 0
    if "gpt-5.4-mini" in model:
        cost = (usage.input_tokens * 0.15 + usage.output_tokens * 0.60) / 1_000_000
    return cost
```

Я копирую эту функцию из модуля в модуль, что не очень изящно. В реальном проекте вы бы вынесли её в общее место, но здесь это позволяет каждому уроку оставаться самодостаточным.

## Инструментированный RAG

`RAGBase` уже работает, и мне нравится использовать его "как есть", потому что это упрощает структуру. Поэтому вместо того, чтобы переписывать его, мы создадим подкласс и изменим только один метод, который вызывает LLM. Все остальное останется прежним, и каждый раз, когда вызывается `rag()`, метрики будут записываться автоматически.

Тот же прием работает и для агентов. Вы могли бы фиксировать каждый вызов инструмента так же, как мы фиксировали вызовы LLM в модуле оценки.

Также в `metrics.py` добавим подкласс, фиксирующий метрики:

```python
class RAGWithMetrics(RAGBase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_call: LLMCallRecord = None

    def llm(self, prompt):
        start_time = time.time()
        response = self._call_llm(prompt)
        response_time = time.time() - start_time
        self._log_response(prompt, response, response_time)
        return response.output_text
```

Метод `_call_llm` отправляет запрос в LLM:

```python
    def _call_llm(self, prompt):
        input_messages = [
            {"role": "developer", "content": self.instructions},
            {"role": "user", "content": prompt}
        ]
        response = self.llm_client.responses.create(
            model=self.model,
            input=input_messages
        )
        return response
```

Метод `_log_response` создает запись и сохраняет её в `self.last_call`. Хранение состояния в объекте — не самый чистый дизайн. Если бы два процесса вызвали его одновременно, возникла бы конкуренция за `last_call`.

Но это позволяет нам считывать метрики обратно без изменения типа возвращаемого значения метода. Для одного человека, работающего в приложении Streamlit, этого достаточно. Мы также выводим запись в консоль, чтобы видеть, что мы фиксируем.

Метод `_log_response` собирает все метрики:

```python
    def _log_response(self, prompt, response, response_time):
        usage = response.usage
        cost = calculate_cost(self.model, usage)

        call_record = LLMCallRecord(
            model=self.model,
            prompt=prompt,
            instructions=self.instructions,
            answer=response.output_text,
            prompt_tokens=usage.input_tokens,
            completion_tokens=usage.output_tokens,
            total_tokens=usage.total_tokens,
            response_time=response_time,
            cost=cost,
        )
    
        print(call_record)
        self.last_call = call_record
```

Теперь обновите `assistant.py`, чтобы импортировать `RAGWithMetrics` вместо `RAGBase`:

```python
import sys

from dotenv import load_dotenv
from openai import OpenAI

from ingest import load_faq_data, build_index
from metrics import RAGWithMetrics

def create_assistant():
    load_dotenv()

    documents = load_faq_data()
    index = build_index(documents)

    return RAGWithMetrics(
        index=index,
        llm_client=OpenAI()
    )
```

## Обновление приложения Streamlit

Файл `app.py` не требует изменений — он по-прежнему вызывает `create_assistant()` и `assistant.rag()`.

Но теперь мы можем также отображать метрики:

```python
if st.button("Спросить"):
    with st.spinner("Обработка..."):
        answer = assistant.rag(user_input)
        st.success("Готово!")
        st.write(answer)

        record = assistant.last_call
        st.write(f"Время ответа: {record.response_time:.2f}с")
        st.write(f"Входные токены (prompt): {record.prompt_tokens}")
        st.write(f"Выходные токены (completion): {record.completion_tokens}")
        st.write(f"Стоимость: ${record.cost:.4f}")
```

Запустите приложение снова:

```bash
make chat
```

Теперь под каждым ответом вы видите время ответа, количество токенов и стоимость. Это не самая красивая панель, но она показывает нужные нам цифры. Примечание по именованию: я называю их `prompt_tokens` и `completion_tokens`, следуя API. Названия `input_tokens` и `output_tokens` читаются понятнее, так что можете переименовать их в своей версии.

Теперь мы фиксируем метрики, но они исчезают, как только мы закрываем приложение. Далее мы сохраним каждую запись в базу данных, чтобы отслеживать использование во времени.

[← Чат-приложение](03-chat-app.md) | [Хранение данных в PostgreSQL →](05-database.md)
