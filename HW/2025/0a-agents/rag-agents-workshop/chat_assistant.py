import json
import random
from IPython.display import display, HTML
import markdown

# === Мапа країн до столиць ===
country_to_capital = {
    "німеччина": "berlin",
    "germany": "berlin",
    "україна": "kyiv",
    "ukraine": "kyiv",
    "польща": "warsaw",
    "poland": "warsaw"
}

# === Нормалізація назв міст ===
def normalize_city_name(name):
    name = name.strip().lower()
    mapping = {
        "kiev": "kyiv",
        "кієв": "kyiv",
        "київ": "kyiv",
        "львів": "lviv",
        "lwow": "lviv"
    }
    return mapping.get(name, name)

# === Клас Tools ===
class Tools:
    def __init__(self):
        self.functions = {}
        self._schemas = {}

    def add_tool(self, function, schema):
        self.functions[function.__name__] = function
        self._schemas[function.__name__] = {
            "type": "function",
            "function": schema
        }

    def get_tools(self):
        return list(self._schemas.values())

    def function_call(self, tool_call_response):
        name = tool_call_response.function.name
        args = json.loads(tool_call_response.function.arguments)
        result = self.functions[name](**args)
        print(f"\n📊 known_weather_data = {known_weather_data}\n")
        return {
            "role": "tool",
            "tool_call_id": tool_call_response.id,
            "name": name,
            "content": json.dumps(result, indent=2)
        }

# === Інтерфейс ===
class ChatInterface:
    def input(self):
        return input("You: ")

    def display(self, text):
        print(text)

    def display_function_call(self, entry, result):
        args = entry.function.arguments
        html = f"""
        <details>
          <summary>Function call: <code>{entry.function.name}({args})</code></summary>
          <div><b>Result:</b>
            <pre>{result['content']}</pre>
          </div>
        </details>
        """
        display(HTML(html))

    def display_response(self, message):
        md = markdown.markdown(message.content)
        html = f"""
        <div style=\"margin:10px 0\">
          <b>Assistant:</b>
          <div>{md}</div>
        </div>
        """
        display(HTML(html))

# === Клас ChatAssistant ===
class ChatAssistant:
    def __init__(self, tools, developer_prompt, interface, client):
        self.tools = tools
        self.dev_prompt = developer_prompt
        self.iface = interface
        self.client = client
        self.last_city = None

    def llama(self, messages):
        return self.client.chat.completions.create(
            model='llama3-8b-8192',
            messages=messages,
            tools=self.tools.get_tools(),
            temperature=0.7,
            tool_choice="auto"
        )

    def run(self):
        chat_messages = [
            {"role": "system", "content": self.dev_prompt},
        ]

        repeat_limit = 5

        while True:
            question = self.iface.input()
            if question.strip().lower() in ('stop', 'стоп'):
                self.iface.display("Chat ended.")
                break

            chat_messages.append({"role": "user", "content": question})

            for attempt in range(repeat_limit):
                response = self.llama(chat_messages)
                msg = response.choices[0].message
                tool_calls = msg.tool_calls
                handled = False

                if tool_calls:
                    for entry in tool_calls:
                        handled = True
                        args = json.loads(entry.function.arguments)
                        if 'city' in args:
                            self.last_city = args['city']
                        result = self.tools.function_call(entry)
                        chat_messages.append(result)
                        self.iface.display_function_call(entry, result)

                if msg.content:
                    self.iface.display_response(msg)
                    break

                if not handled:
                    self.iface.display("⚠️ Невідомий формат відповіді.")
                    break
            else:
                self.iface.display("⚠️ Зупинено через надмірну кількість викликів функцій.")
