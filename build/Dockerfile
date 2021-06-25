FROM python:3.8-slim-buster

WORKDIR /app

COPY src/ ./

RUN pip install --upgrade -r ./requirements.txt

ENTRYPOINT ["python", "main.py"]