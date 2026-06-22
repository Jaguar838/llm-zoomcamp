# Агентный цикл (The Agentic Loop)

Видео: [Смотреть этот урок](https://www.youtube.com/watch?v=ePlQUcTPPjw&list=PL3MmuxUbc_hLZFNgSad56pDBKK8KO0XIv)

В предыдущем уроке мы выполняли вызов функций вручную. Мы отправляли сообщение, получали запрос на вызов функции, выполняли ее, отправляли результат обратно и получали ответ.

Это работает для одного вызова функции. Но этот подход не годится, когда модель хочет выполнить поиск несколько раз или когда первый поиск не дал ответа. Мы не знаем заранее, сколько вызовов потребуется модели. Поэтому нам нужен цикл, который будет продолжать обращаться к модели и запускать инструменты до тех пор, пока задача не будет выполнена. Агент — это и есть такой цикл.

## Анатомия агента

Когда LLM находится за рулем, у нас есть агент. Это ИИ-ассистент, цель которого — помочь пользователю.

Агент состоит из трех частей:

- Инструкции: роль и поведение, которые мы ожидаем. Мы передаем их как сообщение `developer`. Чем лучше инструкции, тем эффективнее помогает агент.
- Инструменты: функции, которые агент может вызывать для выполнения задачи. Для нас это пока только `search`.
- Память: история сообщений. Мы добавляем туда каждый промпт, каждый ответ модели и каждый результат работы инструмента. Агент читает это, чтобы знать, что он уже пробовал.

Ниже приведен код, который соединяет эти три части внутри цикла.

## Системный промпт (Developer prompt)

До сих пор мы полагались на то, что модель сама поймет, когда нужно выполнить поиск. Мы сделаем это более надежным с помощью сообщения `developer`, в котором четко прописано, как себя вести. Именно здесь мы задаем агенту его роль. Это же сообщение подталкивает его к выполнению нескольких поисковых запросов, чтобы мы могли увидеть, как цикл отрабатывает не один раз.

```python
instructions = """
You're a course teaching assistant.
You're given a question from a course student and your task is to answer it.

If you want to look up information, use the search function. 
Use as many keywords from the user question as possible when making first requests.

Make multiple searches.

Try to expand your search by using new keywords
based on the results you get from the search.

At the end, ask if there are other areas that the user wants to explore.
""".strip()
```

## Вспомогательная функция для вызова инструментов

Мы будем многократно выполнять вызовы функций внутри цикла, поэтому давайте обернем это в небольшой хелпер. Он превращает JSON-аргументы в словарь Python, вызывает нужную функцию и сериализует результат. Поскольку у нас пока только один инструмент, мы будем выбирать функцию напрямую по ее имени.

```python
def make_call(call):
    args = json.loads(call.arguments)

    if call.name == "search":
        result = search(**args)

    result_json = json.dumps(result, indent=2)

    return {
        "type": "function_call_output",
        "call_id": call.call_id,
        "output": result_json,
    }
```

Этот хелпер возвращает именно ту структуру, которую ожидает Responses API. Когда мы позже добавим больше инструментов, мы расширим эту функцию новыми ветками `if` (или перейдем на использование реестра инструментов).

## Обработка одного ответа

Давайте обработаем один ответ модели. Мы будем добавлять каждый элемент вывода в диалог, выводить текстовые сообщения и запускать вызовы функций. Результаты вызовов функций также добавляются в историю.

```python
question = "I just discovered the course. Can I join it?"

messages = [
    {"role": "developer", "content": instructions},
    {"role": "user", "content": question},
]

response = openai_client.responses.create(
    model="gpt-5.4-mini",
    input=messages,
    tools=[search_tool],
)

messages.extend(response.output)
has_function_calls = False

for item in response.output:
    if item.type == "function_call":
        print("function_call:", item.name, item.arguments)
        call_output = make_call(item)
        messages.append(call_output)
        has_function_calls = True

    elif item.type == "message":
        print("ASSISTANT:")
        print(item.content[0].text)
```

Флаг `has_function_calls` сообщает нам, нужен ли еще один вызов API. Если ответ содержит вызов функции, значит, в обновленном списке `messages` есть результат работы инструмента, который модель еще не видела. Нам нужно будет отправить его обратно.

## Полный агентный цикл

Мы обернем это в цикл `while`. Цикл будет продолжать вызывать модель до тех пор, пока она не вернет ответ без вызовов функций. Мы также добавим счетчик итераций, чтобы видеть, сколько проходов было совершено.

```python
it = 1

while True:
    print(f"iteration #{it}...")
    has_function_calls = False

    response = openai_client.responses.create(
        model="gpt-5.4-mini",
        input=messages,
        tools=[search_tool],
    )

    messages.extend(response.output)

    for item in response.output:
        if item.type == "function_call":
            print("function_call:", item.name, item.arguments)
            call_output = make_call(item)
            messages.append(call_output)
            has_function_calls = True

        elif item.type == "message":
            print("ASSISTANT:")
            print(item.content[0].text)

    it = it + 1
    if has_function_calls == False:
        break
```

Это и есть ядро агентного цикла. Модель рассуждает о следующем действии. Ваш код выполняет его, и модель видит результат на следующем шаге. Цикл останавливается, когда модель возвращает финальный ответ без запросов на вызов инструментов.

Мы не решаем, сколько раз модель должна выполнить поиск. Это решает сама модель, а мы продолжаем крутить цикл, пока она запрашивает инструменты.

Условие выхода максимально простое: нет вызовов функций на текущем шаге — значит, мы закончили. Другие фреймворки добавляют защитные механизмы поверх этого, такие как максимальное количество итераций, бюджет токенов или ограничение по времени. Вы можете ограничить цикл пятью итерациями и заставить модель дать ответ на последней. Но основой остается этот единственный флаг.

## Обертывание в функцию

Давайте обернем цикл в функцию для повторного использования. Функция принимает инструкции и вопрос в качестве параметров и возвращает финальный ответ.

```python
def agent_loop(instructions, question, model="gpt-5.4-mini") -> str:
    messages = [
        {"role": "developer", "content": instructions},
        {"role": "user", "content": question}
    ]

    it = 1

    while True:
        print(f"iteration #{it}...")
        has_function_calls = False

        response = openai_client.responses.create(
            model=model,
            input=messages,
            tools=[search_tool]
        )

        messages.extend(response.output)

        for item in response.output:
            if item.type == "function_call":
                print("function_call:", item.name, item.arguments)
                call_output = make_call(item)
                messages.append(call_output)
                has_function_calls = True

            elif item.type == "message":
                print("ASSISTANT:")
                last_answer = item.content[0].text
                print(item.content[0].text)

        it = it + 1
        if has_function_calls == False:
            break

    return last_answer
```

Попробуйте задать вопрос с опечаткой:

```python
agent_loop(instructions, "How do I run Olama locally?")
```

Посмотрите, что произойдет. Агент ищет «Olama» и получает плохие результаты. Затем он повторяет поиск с «Ollama» и находит ответ. Цикл позволяет модели самостоятельно исправить ошибку поиска. В этом и заключается смысл перехода к агентному подходу.

Также попробуйте вопрос о регистрации на курс:

```python
agent_loop(instructions, "I just discovered the course. Can I still join it?")
```

## Поощрение нескольких поисковых запросов

Здесь есть тонкий момент. Модель часто отвечает после первого же поиска, даже если дополнительные запросы могли бы помочь. Она рассуждает так: я уже знаю достаточно, зачем утруждаться. Мы подталкиваем ее к более глубокому изучению, переписывая инструкции.

```python
instructions = """
You're a course teaching assistant.
You're given a question from a course student and your task is to answer it.

If you want to look up information, use the search function. 
Use as many keywords from the user question as possible when making first requests.

Make multiple searches. First perform search, analyze the results 
and then perform more searches. 

At the end, ask if there are other areas that the user wants to explore.
""".strip()

agent_loop(instructions, "I just discovered the course. Can I still join it?")
```

Теперь агент делает несколько поисковых запросов на один вопрос и не останавливается после первого раунда результатов. Инструкции — это то, как мы направляем агента. Тем не менее, он все равно может решить пропустить шаги, так что не ждите, что он будет следовать им беспрекословно при каждом запуске.

## Ограничение вопросов не по теме (Off-topic)

Сейчас агент будет отвечать на что угодно. Спросите его про шахматы, и он попытается ответить.

```python
agent_loop(instructions, "what's queen gambit?")
```

Нам нужен ассистент по курсу, а не универсальный чат-бот. Мы ужесточаем инструкции, чтобы агент отвечал только на основе FAQ. Для личного использования мы могли бы разрешить ему отвечать на основе общих знаний. Так что рассматривайте это прежде всего как иллюстрацию ограничения области ответственности (scope).

```python
instructions = """
You're a course teaching assistant.
You're given a question from a course student and your task is to answer it.

If you want to look up information, use the search function. 
Use as many keywords from the user question as possible when making first requests.

Make multiple searches. First perform search, analyze the results 
and then perform more searches. 

The question has to be about the course or its logistics, offtopic questions 
shouldn't be answered. If the search returns nothing, it's likely an off-topic question.
If you can't answer the question using FAQ, don't do it yourself. Only use the 
facts from the FAQ database.

At the end, ask if there are other areas that the user wants to explore.
""".strip()

agent_loop(instructions, "what's queen gambit?")
```

Это упрощенная форма входного фильтра (guardrail). Мы говорим агенту, что входит в его компетенцию, а что — нет. Настоящий фильтр (guardrail) проверяет ввод до того, как агент начнет работу, и может сразу заблокировать нерелевантные вопросы. Это отдельная тема, но инструкции — это первое, с чего стоит начать.

Этот написанный вручную цикл — лучший способ понять, что фреймворки скрывают от вас. Любой агентный фреймворк, будь то LangChain, PydanticAI или OpenAI Agents SDK, оборачивает именно этот паттерн.

[← Вызов функций](13-function-calling.md) | [ToyAIKit →](15-frameworks.md)
