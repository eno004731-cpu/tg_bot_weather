FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN groupadd --system app && \
    useradd --system --gid app --create-home --home-dir /home/app app && \
    mkdir -p /app/data && \
    chown -R app:app /app /home/app

COPY requirements.txt ./
RUN python -m pip install --upgrade pip && \
    pip install --no-compile -r requirements.txt

COPY --chown=app:app . .

USER app

CMD ["python", "bot.py"]
