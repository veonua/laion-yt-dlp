# Dockerized YouTube DLP

This is a lightweight dockerized version of [YouTube DLP](https://github.com/yt-dlp/yt-dlp) designed to run on small, network-optimized CPU nodes.
The image is based on [Alpine Linux](https://alpinelinux.org/) and includes only the bare minimum dependencies required to run YouTube DLP.
[Celery](https://docs.celeryq.dev/en/stable/index.html) is used to distribute the download tasks across multiple worker nodes.


## Features

- Lightweight image based on Alpine Linux
- Includes FFmpeg to compress downloaded videos efficiently on most CPUs
- Easy distribute download tasks across multiple worker nodes
- Handles download errors gracefully, and retries failed downloads
- Supports most of yt-dlp features, 
  - downloading subtitles, audio tracks, comments and sections
  - downloading entire playlists
  - support of various video-platforms

## Usage

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) installed on worker nodes
- [Redis](https://redis.io/) is a recommended server to use as a broker and backend for celery (https://docs.celeryq.dev/en/stable/getting-started/backends-and-brokers/index.html)

### Running the worker

It is recommended to use Docker to run the worker application on each worker node. This eliminates the need to install ffmpeg and python libraries on each node.

To run the worker image, use the following command:

```bash
docker pull veonua/yt_dlp
docker run -e CELERY_BROKER='redis://XX.XX.XX.XX:6379/0' -e CELERY_BACKEND='redis://XX.XX.XX.XX:6379/0' -v /path/to/store/:/output/ --rm -it veonua/yt_dlp
```

Replace XX.XX.XX.XX with the IP address of your Redis server (master node).

### Configuration

You can configure the following environment variables:

- `CELERY_BROKER` - Address the Redis server to use as a broker
- `CELERY_BACKEND` - Address the Redis server to use as a backend
- `DOWNLOAD_THREADS` - Number of concurrent downloads per worker to run (default: 10, recommended for videos longer than 10 minutes)

### Adding tasks

[See app_example](./app_example/main.py)
To add tasks to the Celery queue, use the following Python code:

```python
import os
redis_host = "XX.XX.XX.XX"
os.environ['CELERY_BROKER']  = f'redis://{redis_host}:6379/0'
os.environ['CELERY_BACKEND'] = f'redis://{redis_host}:6379/0'
from tasks import download_and_compress

links = ["https://www.youtube.com/watch?v=XXXXXXXXXXX", "https://www.youtube.com/watch?v=YYYYYYYYYYY"] 

for url in links:
    download_and_compress.delay(url)
```

This tasker can be run on any machine with Python installed. It will add the tasks to the queue, and the workers will pick them up and process them.

To monitor the status of the tasks, use [Flower](https://flower.readthedocs.io/en/latest/).


# Performance

Non-key frames are removed using ffmpeg from the downloaded video to reduce the file size.

264 MB mp4 file Duration: 01:28:51  640x360  =>
  41.4 Mb audio
  44.2 Mb archive with key frames (1778 jpegs)

processing took about 20 seconds on my laptop