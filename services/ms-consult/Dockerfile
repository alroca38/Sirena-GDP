FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    GDP_VALIDATION_SPEC=/app/shared/validation-spec.json

WORKDIR /app

COPY libs/gdp-common /app/libs/gdp-common
COPY shared/validation-spec.json /app/shared/validation-spec.json
COPY services/ms-consult/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir /app/libs/gdp-common && \
    pip install --no-cache-dir -r /app/requirements.txt

COPY services/ms-consult/app /app/app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

