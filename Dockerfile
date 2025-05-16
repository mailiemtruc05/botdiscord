FROM python:3.12-slim

# Cài đặt ffmpeg và các thư viện cần thiết
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Đặt thư mục làm việc
WORKDIR /app

# Copy file requirements và cài đặt thư viện Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ code vào container
COPY . .

# Đặt quyền thực thi cho script start.sh
RUN chmod +x start.sh

# Chạy lệnh start.sh khi container khởi động
CMD ["./start.sh"]
