FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
ENV TELEGRAM_BOT_TOKEN=your_token_here
ENV DEEPSEEK_API_KEY=your_key_here

CMD ["python", "bot.py"]
