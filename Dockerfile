# Sử dụng Python 3.11 slim làm base image
FROM python:3.11-slim

# Cài đặt các công cụ cần thiết (bao gồm CMake, g++, make, và libopenblas)
RUN apt-get update && apt-get install -y \
    libpq-dev gcc cmake g++ make libopenblas-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Thiết lập thư mục làm việc
WORKDIR /app

# Copy và cài đặt Django
COPY ./web_cheating_detect /app/web_cheating_detect
RUN pip install --upgrade pip
RUN pip install -r /app/web_cheating_detect/requirements.txt

# Copy và cài đặt FastAPI
COPY ./face_api /app/face_api
RUN pip install -r /app/face_api/requirements.txt

# Mở các cổng cần thiết
EXPOSE 8000 8081
