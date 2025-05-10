FROM python:3.11-slim

# Zaman dilimini ayarla
ENV TZ=Europe/Istanbul
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Gerekli paketleri kurma
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Uygulama klasörü oluşturma
WORKDIR /app

# Gerekli paketleri kopyalama ve kurma
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulamayı kopyalama
COPY . .

# Çalıştırma komutu
CMD ["python", "main.py"]