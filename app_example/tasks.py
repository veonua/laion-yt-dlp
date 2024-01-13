import os
from celery import Celery

broker = os.environ.get('CELERY_BROKER', 'redis://localhost:6379/0')
backend = os.environ.get('CELERY_BACKEND', 'redis://localhost:6379/0')

app = Celery('yt-dlp', broker=broker, backend=backend)

@app.task(autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 5})
def download_and_compress(url: str, yt_format: str = 'b[height<=360][ext=mp4]'):
    pass

@app.task
def download_audio(url: str, sections: str, yt_format: str = '140'):
    pass
