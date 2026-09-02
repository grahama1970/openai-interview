FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY pyproject.toml README.md /app/
COPY src /app/src
RUN pip install --no-cache-dir . && useradd --create-home --shell /usr/sbin/nologin appuser
USER appuser
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import json, urllib.request; r=urllib.request.urlopen('http://127.0.0.1:8080/health/live', timeout=2); assert json.load(r)['status'] == 'ok'"
CMD ["uvicorn", "openai_interview.main:app", "--host", "0.0.0.0", "--port", "8080"]
