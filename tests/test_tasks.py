import unittest
from tasks import download_audio, download_and_compress, setUp

class TestMain(unittest.TestCase):
    def setUp(self) -> None:
        setUp('/tmp/', '/tmp/')

    def test_download_audio_segment(self):
        res = download_audio("https://www.youtube.com/watch?v=-1PZQg5Gi8A", "*20-30")
        self.assertEqual(res, 0)

    def test_short_vertical_video(self):
        # test fallback to best MP4
        res = download_and_compress("https://www.youtube.com/watch?v=XU7pW9yDFyE") # Makeup for Glamorous Evening Look
        self.assertEqual(res, "ok")

    def test_long_video(self):
        res = download_and_compress("https://www.youtube.com/watch?v=5hiPF558-vc")
        self.assertEqual(res, "ok")

    @unittest.skip("play list is too long")
    def test_long_playlist(self):
        res = download_and_compress("https://www.youtube.com/embed/videoseries?list=UU_HnGIfMXED5wYK8ay1KRLQ&hl=fr_FR")
        self.assertEqual(res, "ok")

if __name__ == '__main__':
    unittest.main()