FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN pip config set global.index-url https://pypi.org/simple
RUN pip install --no-cache-dir --default-timeout=200 --retries=10 -r requirements.txt

COPY app.py /app/app.py

ENV API_URL=http://api:8000

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
