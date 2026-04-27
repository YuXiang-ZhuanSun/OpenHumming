FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY openhumming ./openhumming
COPY workspace ./workspace

RUN pip install --no-cache-dir .

EXPOSE 8765

CMD ["openhumming", "serve", "--host", "0.0.0.0", "--port", "8765"]
