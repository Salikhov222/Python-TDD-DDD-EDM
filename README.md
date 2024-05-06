# Python-TDD-DDD-EDM

В этом репозитории представлена система, разработанная с помощью Python и с применением высоуровневых паттернов проектирования из книги  
`Паттерны разработки на Python. TDD, DDD и событийно-ориентированная архитектура - Г. Персиваль, Б. Грегори`

При написании кода были добавлены свои изменения:

- Фреймворк Flask, используемый в книге, был заменен на FastAPI и, следовательно, весь остальной код был ориентирован на FastAPI;
- Добавлены комментарии к коду и тестам;

_TODO:_

- Добавить конечную точку просмотра имеющихся партий товара, поиска партий по артикулу
- Внедрить авторизацию пользователя (OAuth2)
- Применить инструмент миграции БД (Alembic)
- Попытаться сделать рефакторинг кода под асинхронную библиотеку (asyncio)
