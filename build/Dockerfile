FROM python:3.8-slim-buster

WORKDIR /app

COPY src/ ./

#RUN apt-get update && \
#    apt-get upgrade -y && \
#    rm -rf /var/lib/apt/*

RUN pip install --upgrade -r ./requirements.txt

ENTRYPOINT [ "/bin/sh" ]
CMD ["-c", "python", "charegeback.py"]