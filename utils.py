import discord

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
        self.cap = cv2.VideoCapture(name)
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
                    self.q.get_nowait()   # discard previous (unprocessed) frame
                except queue.Empty:
                    pass
            self.q.put(frame)
        return

    def read(self):
        return self.q.get()


def add_text(frame):
    text = "LIVE nathan cam"
    location = (60, 50)
    font = cv2.FONT_HERSHEY_DUPLEX
    font_scale = 1
    color_1 = (0, 0, 0)  # BGR
    color_2 = (255, 255, 255)  # BGR
    thickness = 2

    new_frame = cv2.putText(frame, text, location, font, font_scale, color_1, thickness + 3)
    new_frame = cv2.putText(frame, text, location, font, font_scale, color_2, thickness)
    return new_frame


def add_circle(frame):
    center = (30, 40)
    size = (10, 10)
    angle = 0
    start_angle = 0
    end_angle = 360
    color = (0, 0, 255)  # BGR
    thickness = -1  # fill

    new_frame = cv2.ellipse(frame, center, size, angle, start_angle, end_angle, color, thickness)
    return new_frame


def decorate(frame):
    new_frame = add_circle(frame)
    new_frame = add_text(new_frame)
    return new_frame


def frame_to_discord(frame_array, filename="test"):
    """
    Take an image frame np array (like from opencv) and convert it to
    a discord.py File using pillow and a byte stream
    """
    img = cv2.cvtColor(frame_array, cv2.COLOR_BGR2RGB)
    pil = Image.fromarray(img)

    img_bytes = io.BytesIO()
    pil.save(img_bytes, format='PNG')
    img_bytes.seek(0)

    file = discord.File(img_bytes, filename=f"{filename}.png")
    return file


def parse_message_file(filename):
    with open(filename, "r") as f:
        lines = f.readlines()
        weights_and_messages = [i.split(":") for i in lines if len(i) > 0]
        random_weights = [float(i[0]) for i in weights_and_messages]
        random_messages = [i[1] for i in weights_and_messages]

    return random_messages, random_weights
