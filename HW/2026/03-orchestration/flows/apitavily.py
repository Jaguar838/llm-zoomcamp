import os
from tavily import TavilyClient

# 1. Инициализация клиента вашим API-ключом
# Рекомендуется использовать переменные окружения, но для быстрого теста можно вставить строкой
TAVILY_API_KEY = "TAVILY_API_KEY" 

try:
    client = TavilyClient(api_key=TAVILY_API_KEY)
    
    # 2. Выполнение простого одиночного поискового запроса
    print("Отправка запроса в Tavily...")
    response = client.search(query="Какая сейчас последняя стабильная версия Kestra?")
    
    # 3. Вывод результатов для проверки
    print("\n[УСПЕХ] API-ключ работает корректно!")
    print(f"Найдено результатов: {len(response.get('results', []))}\n")
    
    for idx, result in enumerate(response.get('results', []), 1):
        print(f"{idx}. {result.get('title')}")
        print(f"   URL: {result.get('url')}")
        print(f"   Контент: {result.get('content')[:150]}...\n")
        
except Exception as e:
    print(f"\n[ОШИБКА] Не удалось проверить API-ключ.")
    print(f"Детали ошибки: {e}")
