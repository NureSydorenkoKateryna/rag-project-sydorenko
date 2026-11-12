# Корпус документів для RAG-системи

Цей каталог містить відфільтрований корпус описів сюжетів книжок. Він є похідним від набору CMU Book Summary Dataset.

## Походження та автори

- Початковий набір: CMU Book Summary Dataset.
- Автори набору: David Bamman, Noah A. Smith (Carnegie Mellon University).
- Сторінка набору: https://www.cs.cmu.edu/~dbamman/booksummaries.html
- Публікація: Bamman D., Smith N. A. New Alignment Methods for Discriminative Book Summarization, 2013.
- Описи сюжетів вилучено авторами набору з англомовної Вікіпедії (знімок від 2 листопада 2012 року), метадані (автор, назва, жанри) зіставлено з Freebase. Автори текстів описів, отже, учасники Вікіпедії.

## Ліцензія

Дані поширюються за ліцензією Creative Commons Attribution-ShareAlike (CC BY-SA), версія 3.0 US, як вказано в описі проєкту. Текст ліцензії: https://creativecommons.org/licenses/by-sa/3.0/us/

Ліцензія стосується лише даних. Код у каталозі `src/` до неї не належить.

## Внесені зміни

Початковий файл `booksummaries.txt` (16 559 записів) змінено так:
1. приведено до UTF-8 та перетворено на формат JSONL;
2. з усіх текстових полів прибрано HTML-розмітку, нормалізовано Unicode (NFC), видалено керівні та невидимі символи, нормалізовано пробіли;
3. поле жанрів перетворено зі словника «ідентифікатор Freebase : назва» на список назв;
4. залишено записи, у яких заповнені всі поля, список жанрів не порожній, опис містить не менше 100 символів, а ідентифікатор статті не повторюється.

У результаті отримано 9 216 записів. Кількість записів після кожного кроку наведена у файлі `stage2_stats.json`.

## Файли

| Файл | Опис |
|---|---|
| `documents.jsonl` | Відфільтрований корпус, один JSON-об'єкт на рядок, кодування UTF-8 |
| `stage2_stats.json` | Кількість записів після кожного правила відбору та використані параметри |
| `token_stats.json` | Довжина описів у токенах та розрахункова кількість чанків для різних перекриттів |

## Поля запису

| Поле | Опис |
|---|---|
| `doc_id` | Ключ документа у форматі `doc_{wiki_id}_{номер}`, де номер це послідовний номер у фінальному корпусі (наприклад, `doc_620_1`) |
| `wiki_id` | Ідентифікатор статті у Вікіпедії |
| `freebase_id` | Ідентифікатор у Freebase |
| `title` | Назва книжки |
| `author` | Автор |
| `date` | Дата публікації (у початковому вигляді, формат може відрізнятися між записами) |
| `genres` | Список назв жанрів |
| `summary` | Опис сюжету |

## Відтворення

Усі команди виконуються з кореня репозиторію (PowerShell). Вихідний файл `booksummaries.txt` потрібно завантажити зі сторінки набору та розмістити в `data/raw/`.

1. Створити й активувати віртуальне середовище, встановити залежність:

   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. Етап 1: визначення кодування, очищення тексту, запис у JSONL (`data/interim/cleaned.jsonl`):

   ```powershell
   python src/ingestion/stage1_normalize.py --src data/raw/booksummaries.txt --dst data/interim/cleaned.jsonl --stats data/interim/stage1_stats.json
   ```

3. Етап 2: фільтрація записів (`data/processed/documents.jsonl`):

   ```powershell
   python src/ingestion/stage2_filter.py --src data/interim/cleaned.jsonl --dst data/processed/documents.jsonl --min-len 100 --max-docs 10000 --seed 42
   ```

4. Статистика довжини в токенах і розрахункова кількість чанків (`data/processed/token_stats.json`). Токенайзер моделі BAAI/bge-small-en-v1.5 завантажується з Hugging Face Hub:

   ```powershell
   python src/ingestion/token_stats.py --src data/processed/documents.jsonl --out data/processed/token_stats.json
   ```

Для Linux або macOS середовище активується командою `source .venv/bin/activate`, решта команд однакові.
