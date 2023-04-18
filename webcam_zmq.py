import sys
import cv2
import zlib
import zmq
import pickle
import threading
import queue
import time

import capture


class CameraPublisher:
    def __init__(self, address="127.0.0.1", port=4949, fps=2, interface="/dev/video0"):
        # Set up a capture to always have latest webcam frame available
        self.capture = capture.VideoCapture(interface)

        # Use to signal thread when to stop
        self.running = True

        # How long to delay between frames
        self.period = 1 / fps

        # Set up publisher socket
        self.host = f"tcp://{address}:{port}"
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.bind(self.host)

        # Spin up thread to continually send data
        self.thread = threading.Thread(target=self._loop)
        self.thread.daemon = True
        self.thread.start()

    def __del__(self):
        self.cleanup()

    def cleanup(self):
        self.running = False
        self.thread.join()
        self.context.destroy()

    def send_frame(self):
        frame = self.capture.read()
        message = zlib.compress(pickle.dumps(frame))
        self.socket.send(bytearray(message))

    def _loop(self):
        t = time.time()

        # Do some goofy stuff to throttle framerate
        while self.running:
            now = time.time()

            if (now - t) >= self.period:
                # Actually send latest camera frame over network
                self.send_frame()
                t = now
            else:
                time.sleep(0.001)


class CameraSubscriber:
    def __init__(self, address="127.0.0.1", port=4949):
        self.host = f"tcp://{address}:{port}"

        # Set up a subscription on the host
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        self.socket.connect(self.host)
        self.socket.setsockopt(zmq.SUBSCRIBE, "".encode())  # Receive all topics

        # Used to signal thread to stop
        self.running = True

        # Spin up thread to receive from network
        self.q = queue.Queue()
        self.thread = threading.Thread(target=self._reader)
        self.thread.daemon = True
        self.thread.start()

    def __del__(self):
        self.cleanup()

    def cleanup(self):
        self.running = False
        self.thread.join()
        self.context.destroy()

    def get_frame(self):
        # Blocking read
        data = self.socket.recv()

        # Decompress and unpickle cv2 frame
        decompressed = zlib.decompress(data)
        frame = pickle.loads(decompressed)
        return frame

    def read(self):
        return self.q.get()

    def _reader(self):
        while self.running:
            frame = self.get_frame()
            if not self.q.empty():
                try:
                    self.q.get_nowait()  # discard previous frames
                except queue.Empty:
                    pass
            self.q.put(frame)
        return


def main():
    argc = len(sys.argv)

    assert argc > 1, "Must at least specify pub or sub!"

    pubsub = sys.argv[1]
    address = "127.0.0.1"
    port = 4949

    if argc > 2:
        address = sys.argv[2]
    if argc > 3:
        port = sys.argv[3]

    if pubsub == "pub":
        pub = CameraPublisher(address=address, port=port)

        try:
            time.sleep(1000000)
        except KeyboardInterrupt:
            pass

    elif pubsub == "sub":
        sub = CameraSubscriber(address=address, port=port)

        try:
            while True:
                frame = sub.read()
                cv2.imshow("test", frame)
                cv2.waitKey(1)
        except KeyboardInterrupt:
            pass

    else:
        print("Specify pub or sub, doofus!")


if __name__ == "__main__":
    main()
