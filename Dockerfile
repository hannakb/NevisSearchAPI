FROM python:3.14

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x scripts/entrypoint.sh

ENTRYPOINT ["scripts/entrypoint.sh"]

CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
