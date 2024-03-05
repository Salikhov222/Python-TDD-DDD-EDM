FROM python:3.10-slim

# Устанавливаем рабочую директорию
# WORKDIR /src

# Копируем файл зависимостей в директорию tmp и устанавливаем их
COPY requirements.txt .
RUN pip install -r requirements.txt

# Создание директории /src и копирование содержимого из локальной директории внутрь образа
# RUN mkdir -p /src
# COPY src/ /src
# RUN pip install -e /src
# COPY tests/ /tests

# ENV PYTHONPATH=/src

CMD [ "uvicorn", "src.allocation.entrypoints.fastAPI_app:app", "--reload", "--host", "0.0.0.0", "--port", "80" ]