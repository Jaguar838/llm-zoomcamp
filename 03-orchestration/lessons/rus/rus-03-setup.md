# Настройка Kestra

Видео: [Настройка Kestra](https://www.youtube.com/watch?v=ghkf93rfb2w&list=PL3MmuxUbc_hLZFNgSad56pDBKK8KO0XIv)

Ниже описано, как настроить все необходимое для запуска примеров потоков в этом модуле.

## Предварительные требования

Для этого модуля требуется [Docker](https://docs.docker.com/get-started/get-docker/) с Docker Compose для локального запуска Kestra. [Docker Desktop](https://www.docker.com/products/docker-desktop/) — это самый простой способ получить и то, и другое на Mac и Windows. Если у вас не установлен Docker, настройте его перед продолжением.

## Шаг 1: Запуск Kestra

Этот модуль включает `docker-compose.yml` с предварительно настроенной Kestra:

```bash
cd 03-orchestration
docker compose up -d
```

Как только контейнер запустится, перейдите в интерфейс Kestra по адресу http://localhost:8080.

Чтобы остановить Kestra:

```bash
docker compose down
```

## Шаг 2: Получение API-ключей

**API-ключ Gemini (обязательно)**

1. Посетите [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Войдите в свой аккаунт Google
3. Нажмите "Create API Key" и скопируйте свой ключ

Бесплатного уровня достаточно для легкого использования, но лимиты запросов относительно низкие — вы можете быстро исчерпать квоту, если будете часто запускать потоки с агентами и мультиагентными системами. Если вы столкнетесь с ошибками `429 Resource Exhausted`, подождите минуту перед повторной попыткой или рассмотрите возможность перехода на платный уровень.

**API-ключ OpenAI (требуется для потока 3)**

1. Посетите [platform.openai.com](https://platform.openai.com/home), войдите или создайте аккаунт
2. Перейдите в раздел **API keys** и создайте новый ключ

**API-ключ Tavily (требуется для веб-поиска: потоки 3, 5 и 6)**

1. Посетите [Tavily](https://tavily.com/)
2. Зарегистрируйтесь на бесплатном уровне
3. Получите свой API-ключ в личном кабинете

Бесплатный уровень включает 1000 поисковых запросов в месяц.

## Шаг 3: Настройка API-ключей в Kestra

Kestra считывает секреты из переменных окружения с префиксом `SECRET_`, где значение закодировано в base64. Экспортируйте свои ключи перед запуском Kestra:

```bash
export GEMINI_API_KEY="ваш-gemini-api-ключ" # обязательно
export SECRET_GEMINI_API_KEY=$(echo -n $GEMINI_API_KEY | base64) # обязательно
export SECRET_OPENAI_API_KEY=$(echo -n "ваш-openai-api-ключ" | base64)   # требуется для потока 3
export SECRET_TAVILY_API_KEY=$(echo -n "ваш-tavily-api-ключ" | base64)   # необязательно
```

Затем запустите (или перезапустите) Kestra:

```bash
docker compose up -d
```

В потоках ссылайтесь на секреты с помощью `{{ secret('GEMINI_API_KEY') }}` — опускайте префикс `SECRET_` при вызове `secret()`.

> [!WARNING]
> Никогда не фиксируйте (commit) API-ключи в Git!

## Шаг 4: Импорт примеров потоков

```bash
cd 03-orchestration

# Отрегулируйте имя пользователя и пароль в соответствии с вашими настройками Kestra
curl -X POST -u 'admin@kestra.io:Admin1234!' http://localhost:8080/api/v1/flows/import -F fileUpload=@flows/1_chat_without_rag.yaml
curl -X POST -u 'admin@kestra.io:Admin1234!' http://localhost:8080/api/v1/flows/import -F fileUpload=@flows/2_chat_with_rag.yaml
curl -X POST -u 'admin@kestra.io:Admin1234!' http://localhost:8080/api/v1/flows/import -F fileUpload=@flows/3_rag_with_websearch.yaml
curl -X POST -u 'admin@kestra.io:Admin1234!' http://localhost:8080/api/v1/flows/import -F fileUpload=@flows/4_simple_agent.yaml
curl -X POST -u 'admin@kestra.io:Admin1234!' http://localhost:8080/api/v1/flows/import -F fileUpload=@flows/5_web_research_agent.yaml
curl -X POST -u 'admin@kestra.io:Admin1234!' http://localhost:8080/api/v1/flows/import -F fileUpload=@flows/6_multi_agent_research.yaml
```

Либо скопируйте и вставьте YAML потока напрямую в интерфейс Kestra.

## Шаг 5: Запуск вашего первого агента

1. Откройте интерфейс Kestra по адресу http://localhost:8080
2. Перейдите в пространство имен (namespace) `zoomcamp`
3. Найдите поток `4_simple_agent` и нажмите "Execute"
4. Оставьте входные данные по умолчанию или настройте их
5. Наблюдайте за выполнением и просмотрите результаты
6. Затем запустите `5_web_research_agent` и `6_multi_agent_research` и проанализируйте логи и результаты

[← Проектирование контекста](rus-02-context-engineering.md) | [AI Copilot →](rus-04-ai-copilot.md)
