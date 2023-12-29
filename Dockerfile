FROM python:3.11-alpine
LABEL maintainer="Andrew Matiuk / (@veonua)"

RUN apk add --update --no-cache --virtual .build-deps gcc musl-dev \
&& pip install --upgrade pip \
&& pip install pycrypto yt-dlp \
&& rm -rf ~/.cache/pip \
&& apk del .build-deps \
&& apk add ffmpeg \
&& chmod o+w /media \
&& adduser -D yt-dlp

RUN pip install celery[redis]

COPY tasks.py /app/tasks.py
WORKDIR /app
USER yt-dlp

ENV DOWNLOAD_PATH=/tmp/
ENV DOWNLOAD_THREADS=5
#  celery -A tasks worker --loglevel=INFO
CMD [ "celery", "-A", "tasks", "worker", "--loglevel=INFO", "--concurrency=20" ]