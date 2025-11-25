# Dockerfile
FROM python:3.10-slim

# Cài gcc (cần cho transformers)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --upgrade pip \
    -i https://pypi.tuna.tsinghua.edu.cn/simple
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# CÀI TORCH CPU (phiên bản chính thức, không cần +cpu)
# 2.7.0 trở lên đã có sẵn CPU build trên PyPI
RUN pip install --no-cache-dir torch==2.7.0 -i https://pypi.tuna.tsinghua.edu.cn/simple

# Copy code
COPY . .

EXPOSE 36000

CMD ["python", "app.py"]
