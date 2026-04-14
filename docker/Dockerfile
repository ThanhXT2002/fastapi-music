# BƯỚC 1: Lấy bộ FFmpeg chính hãng từ Docker Hub
FROM mwader/static-ffmpeg:latest AS ffmpeg-image

# BƯỚC 2: Tạo Image chính cho Backend Python
FROM python:3.10-slim

# Copy 2 file chạy cốt lõi của ffmpeg thả vào thư mục hệ thống của Linux (/usr/local/bin)
# Nơi mà mọi thư viện (kể cả yt-dlp) đều tự động tìm thấy mà không cần chỉ đường dẫn
COPY --from=ffmpeg-image /ffmpeg /usr/local/bin/
COPY --from=ffmpeg-image /ffprobe /usr/local/bin/

# Ngăn chặn Python sinh ra ba cái file rác .pyc
ENV PYTHONDONTWRITEBYTECODE=1
# Cho phép log (print) xả thẳng ra terminal để dễ xem lỗi
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Ưu tiên copy file yêu cầu và cài đặt thư viện trước để tối ưu tốc độ Build ở các lần sau
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Mặc dù ở Dev chúng ta xài code qua volume, nhưng vẫn copy code vào image làm khung nền
COPY . .

# Mở cổng API
EXPOSE 8000

# Khởi động Uvicorn với chế độ reload tự thay đổi khi code được lưu
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# docker compose -f docker\docker-compose.yml up --build -d
