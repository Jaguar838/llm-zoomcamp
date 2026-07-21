# Интеграция Groq с Pydantic AI

В этом руководстве описано, как использовать **Groq** в качестве провайдера моделей в **Pydantic AI**.

## 1. Установка

Для начала добавьте зависимость `groq` в ваш проект. Если вы используете `uv`:

```bash
uv add "pydantic-ai-slim[groq]"
```

Или через обычный `pip`:

```bash
pip install "pydantic-ai-slim[groq]"
```

## 2. Настройка API ключа

Получите API ключ в [Groq Console](https://console.groq.com/keys).

Рекомендуется использовать файл `.env` для хранения ключа:

```bash
GROQ_API_KEY=gsk_ваш_ключ_здесь
```

## 3. Базовое использование

Используйте класс `GroqModel` для инициализации. Pydantic AI автоматически найдет переменную окружения `GROQ_API_KEY`.

```python
from pydantic_ai import Agent
from pydantic_ai.models.groq import GroqModel

# Инициализация модели
model = GroqModel('llama-3.3-70b-versatile')

# Создание агента
agent = Agent(model)

# Синхронный запуск
result = agent.run_sync('Какая столица у Франции?')
print(result.data)
```

## 4. Популярные модели Groq

Вы можете использовать следующие идентификаторы моделей:

*   `llama-3.3-70b-versatile` — Самая мощная модель на данный момент.
*   `llama-3.1-70b-versatile` — Универсальная модель.
*   `openai/gpt-oss-20b` — Быстрая и эффективная.

Полный список доступен в [документации Groq](https://console.groq.com/docs/models).

## 5. Программная передача ключа

Если вы не хотите использовать переменные окружения, вы можете передать ключ явно через `GroqProvider`:

```python
from pydantic_ai.models.groq import GroqModel
from pydantic_ai.providers.groq import GroqProvider

model = GroqModel(
    'llama-3.3-70b-versatile',
    provider=GroqProvider(api_key='your-api-key')
)
```

## 6. Совместимость с Logfire

Для мониторинга и трассировки в домашнем задании не забудьте добавить:

```python
import logfire

logfire.configure()
logfire.instrument_pydantic_ai()
```

Это позволит видеть все вызовы Groq в панели Logfire.
