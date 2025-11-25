# From python:3.10
FROM local/reddit_producer:base

WORKDIR /app

COPY . .

# RUN pip install -r requirements.txt

# CMD ["python", "reddit_to_kafka_stress.py"]
CMD ["python", "reddit_producer.py"]