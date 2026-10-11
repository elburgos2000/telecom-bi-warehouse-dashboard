FROM python:3.11-slim

WORKDIR /app

# Copy all application files
COPY . /app

EXPOSE 8080

CMD ["python", "server.py"]
