from typing import Optional

from celery import Celery
from celery.utils.log import get_task_logger
from celery.signals import worker_process_init

import os
import shutil

import subprocess

broker = os.environ.get('CELERY_BROKER', 'redis://localhost:6379/0')
backend = os.environ.get('CELERY_BACKEND', 'redis://localhost:6379/0')

DOWNLOAD_PATH = os.environ.get('DOWNLOAD_PATH', '/tmp/')
OUTPUT_PATH = os.environ.get('OUTPUT_PATH', '/output/')
DOWNLOAD_THREADS = int(os.environ.get('DOWNLOAD_THREADS', 10))
DEBUG = os.environ.get('DEBUG', False)  # do not delete tmp files if True

app = Celery('yt-dlp', broker=broker, backend=backend)
logger = get_task_logger(__name__)

def download(url: str, output_path: str = "/tmp/", yt_format: str = None,
             fall_back_format: Optional[str] = "b[ext=mp4]", sections: str = None):
    # see yt-dlp --help for more info
    # yt_format:                      Video format code, see "FORMAT SELECTION" for
    #                                 all the info
    #                                 Default: 'b[height<=360][ext=mp4]'
    # fall_back_format:               If the format given by "yt_format" is not available,
    #                                 download the best MP4
    # sections:                       Download only chapters that match the
    #                                 regular expression. A "*" prefix denotes
    #                                 time-range instead of chapter. Negative
    #                                 timestamps are calculated from the end.
    #                                 "*from-url" can be used to download between
    #                                 the "start_time" and "end_time" extracted
    #                                 from the URL. Needs ffmpeg. This option can
    #                                 be used multiple times to download multiple
    #                                 sections, e.g. --download-sections
    #                                 "*10:15-inf" --download-sections "intro"

    if yt_format is None:
        yt_format = 'b[height<=360][ext=mp4]'

    logger.info('Downloading video from YouTube %s format:%s', url, yt_format)
    args = ['yt-dlp',
            '-N', str(DOWNLOAD_THREADS),  # number of threads
            '--write-info-json', '--embed-subs', '--embed-chapters', '--embed-metadata',
            # '--write-comments', 
            '--no-progress', '-q',
            '--format', yt_format,  # 'bv*[height<=360][ext=mp4]+wa/b[height<=360] / w',
            '--output', output_path + "%(id)s.%(ext)s", url]

    if sections is not None:
        args.append('--download-sections')
        args.append(sections)

    pipes = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    std_out, std_err = pipes.communicate()

    if pipes.returncode == 0:
        return os.listdir(output_path)

    str_err = str(std_err)

    if "Too Many Requests" in str_err:
        logger.error('Too Many Requests %s', url)
        raise Exception("Too Many Requests")

    if fall_back_format is not None and 'Requested format is not available' in str_err:
        logger.warning('Trying to download best format')
        return download(url, output_path, fall_back_format, None, sections)

    logger.error('Error downloading video %s reason: %s', url, str_err)
    raise Exception(str_err)


@app.task(autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={'max_retries': 5})
def download_and_compress(url: str, yt_format: str = 'b[height<=360][ext=mp4]'):
    # Download video and drop non-keyframes using ffmpeg
    #
    # see yt-dlp --help for more info
    # yt_format:                      Video format code, see "FORMAT SELECTION" for
    #                                 all the info https://github.com/yt-dlp/yt-dlp?tab=readme-ov-file#format-selection
    #                                 Default: 'b[height<=360][ext=mp4]'

    logger.info('Downloading video from ' + url)

    import uuid
    tmp_path = DOWNLOAD_PATH + str(uuid.uuid4()) + '/'
    res = -1
    try:
        files = download(url, tmp_path, yt_format=yt_format)

        for json_file in (f for f in files if f.endswith('.json')):
            logger.info('Copying json ' + json_file)
            shutil.copy(tmp_path + json_file, OUTPUT_PATH + json_file)

        video_files = [f for f in files if not f.endswith('.json')]

        if len(video_files) == 0:
            logger.error('No video files found %s', url)
        else:
            for video_file in video_files:
                logger.info('Compressing video %s', video_file)
                args = ['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', '-discard', 'nokey', '-i',
                        tmp_path + video_file, '-c:s', 'copy', '-c', 'copy', "-copyts", OUTPUT_PATH + video_file]
                res = subprocess.call(args)
            logger.info('Compressed videos %s', url)

    finally:
        try:
            if not DEBUG:
                shutil.rmtree(tmp_path)
        except:
            pass

    if res != 0:
        logger.error('Error downloading video %s', url)
        return None

    logger.info('Video downloaded successfully')
    return "ok"

@app.task
def download_audio(url: str, sections: str, yt_format: str = '140'):
    # Download audio only
    #
    # from yt-dlp --help
    # yt_format:                      Video format code, see "FORMAT SELECTION" for
    #                                 all the info https://github.com/yt-dlp/yt-dlp?tab=readme-ov-file#format-selection
    #                                 Default: '140'
    # sections:                       Download only chapters that match the
    #                                 regular expression. A "*" prefix denotes
    #                                 time-range instead of chapter. Negative
    #                                 timestamps are calculated from the end.
    #                                 "*from-url" can be used to download between
    #                                 the "start_time" and "end_time" extracted
    #                                 from the URL. Needs ffmpeg. This option can
    #                                 be used multiple times to download multiple
    #                                 sections, e.g. --download-sections
    #                                 "*10:15-inf" --download-sections "intro"
    logger.info('Downloading audio from YouTube %s', url)
    args = ['yt-dlp',
            '-N', str(DOWNLOAD_THREADS),  # number of threads
            '--no-progress', '-q',
            '--format', yt_format,
            '--download-sections', sections,
            '--output', OUTPUT_PATH + "%(id)s.%(ext)s", url]
    result = subprocess.run(args, check=True)
    return result.returncode


@worker_process_init.connect()
def init_worker(**kwargs):
    try:
        os.makedirs(DOWNLOAD_PATH, exist_ok=True)
        os.makedirs(OUTPUT_PATH, exist_ok=True)
    except:
        logger.error('Error creating directories', exc_info=True)
        pass


def setUp(output_path: str, download_path: str):
    global OUTPUT_PATH, DOWNLOAD_PATH
    OUTPUT_PATH = output_path
    DOWNLOAD_PATH = download_path