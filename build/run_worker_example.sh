# Description: Example of worker script for yt_dlp celery
# Author: Veon (Andrew Matiuk)

# create folder for output
mkdir /mnt/big_storage/audioset/
# set permissions, so that celery worker can write to it
chmod 666 /mnt/big_storage/audioset/

# pull latest image
docker pull veonua/yt_dlp
# run worker
# Assuming that redis is running on machine with IP XX.XX.XX.XX
docker run -e CELERY_BROKER='redis://XX.XX.XX.XX:6379/0' -e CELERY_BACKEND='redis://XX.XX.XX.XX:6379/0' -v /mnt/big_storage/audioset/:/output/ --rm -it veonua/yt_dlp