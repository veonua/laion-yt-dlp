import os
redis_host = "XX.XX.XX.XX"
os.environ['CELERY_BROKER']  = f'redis://{redis_host}:6379/0'
os.environ['CELERY_BACKEND'] = f'redis://{redis_host}:6379/0'
from tasks import download_and_compress

from datasets import load_dataset
df = load_dataset("ChristophSchuhmann/yt-urls-for-emotional-tts")['train'].to_pandas()

links = df['link'][15000:]

for url in links:
    res = download_and_compress.delay(url)

print(len(links))