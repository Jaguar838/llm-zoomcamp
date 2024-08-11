# Підготовка даних у RAG

## Початок роботи

1. Клонуйте [репозиторій](https://github.com/mage-ai/rag-project):
```bash
git clone https://github.com/mage-ai/rag-project
cd rag-project
```
2. Перейдіть до директорії `rag-project/llm`, додайте `spacy` до файлу `requirements.txt`.
3. Потім оновіть файл `Dockerfile`, який знаходиться в директорії `rag-project`, додавши наступне:
```YAML
RUN python -m spacy download en_core_web_sm
```
4. Запустіть:
```bash
./scripts/start.sh
```

Після запуску перейдіть до [http://localhost:6789/](http://localhost:6789/).

Для отримання додаткової інформації про налаштування, ознайомтеся з [інструкціями](https://docs.mage.ai/getting-started/setup#docker-compose-template).


## 0. Огляд модуля

<a href="https://www.youtube.com/watch?v=gP2ZOsG9Umg&list=PL3MmuxUbc_hIB4fSqLy_0AfTjVLpgjV3R">
  <img src="https://markdown-videos-api.jorgenkh.no/youtube/gP2ZOsG9Umg">
</a>

## 1. Інтеграція

У цьому розділі ми розглянемо інтеграцію документів з одного джерела даних.

<a href="https://www.youtube.com/watch?v=9BJppvgLINc&list=PL3MmuxUbc_hIB4fSqLy_0AfTjVLpgjV3R">
  <img src="https://markdown-videos-api.jorgenkh.no/youtube/9BJppvgLINc">
</a>

* [Код](https://github.com/mage-ai/rag-project/blob/master/llm/rager/data_loaders/runic_oblivion.py)
* [Посилання на документ для API Data Loader](https://raw.githubusercontent.com/DataTalksClub/llm-zoomcamp/main/01-intro/documents.json)

## 2. Розбиття на частини

Після того, як дані інтегровані, ми ділимо їх на керовані частини.

Дані Q&A вже поділені на частини – тексти невеликі, і їх легко обробляти та індексувати. Але інші набори даних можуть бути не такими (тексти книг, транскрипти тощо).

У цьому відео ми обговоримо перетворення великих текстів на менші документи – тобто розбиття на частини.

<a href="https://www.youtube.com/watch?v=H2oq5GSCKhM&list=PL3MmuxUbc_hIB4fSqLy_0AfTjVLpgjV3R">
  <img src="https://markdown-videos-api.jorgenkh.no/youtube/H2oq5GSCKhM">
</a>

[Код](https://github.com/mage-ai/rag-project/blob/master/llm/rager/transformers/radiant_photon.py)

## 3. Токенізація

Токенізація є важливим кроком в обробці тексту та підготовці даних для ефективного пошуку.

<a href="https://www.youtube.com/watch?v=hrMrqRgZryg&list=PL3MmuxUbc_hIB4fSqLy_0AfTjVLpgjV3R">
  <img src="https://markdown-videos-api.jorgenkh.no/youtube/hrMrqRgZryg">
</a>

[Код](https://github.com/mage-ai/rag-project/blob/master/llm/rager/transformers/vivid_nexus.py)

## 4. Вбудовування

Вбудовування даних перекладає текст у числові вектори, які можна обробляти моделями.

Раніше для цього ми використовували трансформери речень. У цьому відео ми покажемо іншу стратегію.

<a href="https://www.youtube.com/watch?v=8wrArv0DEKc&list=PL3MmuxUbc_hIB4fSqLy_0AfTjVLpgjV3R">
  <img src="https://markdown-videos-api.jorgenkh.no/youtube/8wrArv0DEKc">
</a>

[Код](https://github.com/mage-ai/rag-project/blob/master/llm/rager/transformers/prismatic_axiom.py)

## 5. Експорт

Після обробки дані потрібно експортувати для зберігання, щоб їх можна було отримати для кращого контекстуалізації запитів користувачів.

Тут ми збережемо вбудовування в Elasticsearch.

Будь ласка, переконайтеся, що використовуєте ім’я, яке ви дали своєму сервісу Elasticsearch у вашому файлі docker-compose, а також порт як рядок підключення, наприклад, нижче:

`<docker-compose-service-name><port>` http://elasticsearch:9200

<a href="https://www.youtube.com/watch?v=cHrphSoRBX4&list=PL3MmuxUbc_hIB4fSqLy_0AfTjVLpgjV3R">
  <img src="https://markdown-videos-api.jorgenkh.no/youtube/cHrphSoRBX4">
</a>

[Код](https://github.com/mage-ai/rag-project/blob/master/llm/rager/data_exporters/numinous_fission.py)

## 6. Витягування: тестовий пошуковий запит

Після експортування частин і вбудованих векторів, ми можемо протестувати пошуковий запит, щоб отримати відповідні документи на приклад запитів.

<a href="https://www.youtube.com/watch?v=z5NqDcaBglY&list=PL3MmuxUbc_hIB4fSqLy_0AfTjVLpgjV3R">
  <img src="https://markdown-videos-api.jorgenkh.no/youtube/z5NqDcaBglY">
</a>

[Код](code/06_retrieval.py)

## 7. Автоматизація щоденних запусків

Автоматизація є ключовим моментом для підтримки та оновлення вашої системи. У цьому розділі показано, як налаштувати та автоматично запускати щоденні запуски ваших даних, щоб забезпечити актуальність та узгодженість обробки даних.

<a href="https://www.youtube.com/watch?v=nuk7_soKMUA&list=PL3MmuxUbc_hIB4fSqLy_0AfTjVLpgjV3R">
  <img src="https://markdown-videos-api.jorgenkh.no/youtube/nuk7_soKMUA">
</a>

## Домашнє завдання

TBA

# Примітки

* Перший посилання розміщене тут
* Ви робили нотатки? Додайте їх вище цієї лінії (Надішліть PR із *посиланнями* на ваші нотатки)