import cv2
import io
from PIL import Image
import queue
import threading


class VideoCapture:
    """
    Shamelessly from stack overflow
    cv2 buffers camera frames, but we always want the latest. This spins up a thread
    which will discard all outdated frames, allowing the latest one to be accessed
    by the read() function.
    """

    def __init__(self, name):
        self.cap = cv2.VideoCapture(name)  # , cv2.CAP_V4L)
        self.q = queue.Queue()
        self.running = True

        self.t = threading.Thread(target=self._reader)
        self.t.daemon = True
        self.t.start()

    def __del__(self):
        self.cleanup()

    def cleanup(self):
        self.running = False
        self.t.join()

    # read frames as soon as they are available, keeping only most recent one
    def _reader(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                break
            if not self.q.empty():
                try:
                    self.q.get_nowait()  # discard previous (unprocessed) frame
                except queue.Empty:
                    pass
            self.q.put(frame)
        return

    def read(self):
        return self.q.get()
