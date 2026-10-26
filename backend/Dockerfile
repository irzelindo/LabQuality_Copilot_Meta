FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
COPY requirements.lock ./
RUN pip install --no-cache-dir -r requirements.lock
COPY . .
RUN useradd --create-home --uid 10001 labquality && mkdir -p /data/storage && chown -R labquality:labquality /app /data
USER labquality
EXPOSE 8000
CMD ["sh", "entrypoint.sh"]
