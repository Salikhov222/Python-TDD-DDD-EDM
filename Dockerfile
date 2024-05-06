FROM python:3.10-slim

# Копируем файл зависимостей в директорию tmp и устанавливаем их
COPY requirements.txt .
RUN pip install -r requirements.txt

# Создание директории /src и копирование содержимого из локальной директории внутрь образа
# Не работает, не видит директорию src, почему?

RUN mkdir -p /src
COPY src/ ./src
RUN pip install -e /src
COPY tests/ /tests/

WORKDIR /src
ENV PYTHONPATH /

CMD [ "uvicorn", "src.allocation.entrypoints.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000" ]