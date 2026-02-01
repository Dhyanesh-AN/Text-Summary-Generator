FROM python:3.11-slim-bullseye

RUN apt update -y && apt install awscli -y
WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir --upgrade accelerate
RUN pip uninstall -y transformers accelerate
RUN pip install --no-cache-dir transformers accelerate

EXPOSE 8080

CMD ["python3", "app.py"]