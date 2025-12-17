FROM apache/airflow:2.8.3-python3.10

USER airflow

COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

ENV PYTHONPATH="/opt/airflow/plugins:${PYTHONPATH}"