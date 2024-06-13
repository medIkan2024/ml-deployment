# Gunakan base image Python
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV MODEL_URL=https://storage.googleapis.com/bucket-ml-medikan/model/model.h5
ENV GCS_BUCKET_NAME=profile-user-medikan

# Buat direktori kerja untuk aplikasi
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy aplikasi ke dalam direktori kerja
COPY . /app/

# Expose port yang digunakan oleh aplikasi
EXPOSE 8080

# Jalankan aplikasi saat container dijalankan
CMD ["python", "app.py"]
