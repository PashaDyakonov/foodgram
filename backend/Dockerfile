FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install -r requirements.txt --no-cache-dir

RUN mkdir -p /app/data
COPY data/ingredients.csv /app/data/ingredients.csv

COPY . .

RUN python manage.py collectstatic --noinput

CMD bash -c "python manage.py migrate --noinput && \
    python manage.py load_ingredients && \
    gunicorn --bind 0.0.0.0:8000 foodgram.wsgi"