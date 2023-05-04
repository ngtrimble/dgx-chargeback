FROM python:3.10-slim-bullseye

WORKDIR /app

RUN apt-get update && \
    apt-get install -y libmagic1 && \
    rm -rf /var/lib/apt/*

COPY src/requirements.txt ./requirements.txt

RUN pip install --upgrade pip && \
    pip install --upgrade -r ./requirements.txt

COPY src/ ./

COPY docker-entrypoint.sh ./

EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Set the default startup service to chargeback
CMD ["chargeback"]