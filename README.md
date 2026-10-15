# loguru-extra

Небольшое расширение [loguru](https://github.com/Delgan/loguru): готовый формат логов
и сквозной trace id для синхронного и асинхронного кода.

```
2024-03-29 12:00:00.000 | 2bfd0a05-7ca4-4eae-bf55-2403eb8a9753 | 1401... |  MainThread  | INFO     | app:handle:9 - handling request
```

## Установка

```bash
pip install loguru-extra
```

## Использование

```python
from loguru_extra import add_file_logger, logger, setup, trace, traceable

setup()                                         # вывод в stdout, уровень INFO
add_file_logger("app.log", rotation="10 MB")    # любые аргументы logger.add


@traceable
def handle_request():
    logger.info("handling request")             # у каждого вызова свой trace id


@traceable
async def handle_async():
    logger.info("works with async too")


with trace(request.headers["X-Request-ID"]):   # свой trace id, например из заголовка
    logger.info("...")
```

- `setup(sink=sys.stdout, level="INFO", **kwargs)` — заменяет все обработчики loguru одним
  с форматом loguru-extra. Импорт пакета сам по себе ничего не настраивает.
- `add_file_logger(file_name, level="INFO", **kwargs)` — добавляет файловый обработчик.
- `trace(trace_id=None)` — контекстный менеджер. Без аргумента переиспользует trace id внешнего
  блока, а если его нет — генерирует новый. После выхода восстанавливает предыдущее значение.
- `@traceable` — оборачивает каждый вызов функции (обычной или `async`) в `trace()`.
  Вложенные вызовы получают trace id внешнего, параллельные задачи asyncio — каждая свой.
- `get_trace_id()` — текущий trace id или `None`.

По умолчанию `diagnose=False`, чтобы значения переменных (пароли, токены) не попадали
в трейсбеки. Включить: `setup(diagnose=True)`.

## Разработка

Проект использует [uv](https://docs.astral.sh/uv/).

```bash
uv sync          # создать .venv и поставить зависимости
uv run pytest    # запустить тесты
```

## Публикация в PyPI

1. Поднять версию в `pyproject.toml` (например, `uv version --bump patch`).
2. Собрать и опубликовать:

```bash
rm -rf dist
uv build
uv publish --token pypi-...      # или через переменную окружения UV_PUBLISH_TOKEN
```

Токен создаётся на https://pypi.org/manage/account/token/. Проверить публикацию заранее
можно на TestPyPI:

```bash
uv publish --publish-url https://test.pypi.org/legacy/ --token pypi-...
```
