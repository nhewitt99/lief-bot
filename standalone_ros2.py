"""
I'm feeling very lazy and am just writing this standalone file,
rather than properly wrapping all this in a ROS 2 package.
This *sucks* and I will probably face consequences down the line.
"""
import time
import threading
import queue

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, Vector3


class VelocityPublisher(Node):
    def __init__(self):
        super().__init__("velocity_publisher")
        self.publisher = self.create_publisher(Twist, "cmd_vel", 10)

    def pub_velocity(self, linear, angular):
        """
        Function to package linear and angular command into a Twist, then publish
        @param linear: the desired linear velocity in the z axis
        @param angular: the desired angular velocity in yaw
        """
        linear_vec = Vector3()
        angular_vec = Vector3()

        # Add scalars to the vectors
        linear_vec.x = float(linear)
        angular_vec.z = float(angular)

        # Package into a Twist
        msg = Twist(linear=linear_vec, angular=angular_vec)
        self.publisher.publish(msg)


class VelocityInterface:
    def __init__(self):
        # Keep track of latest command given
        self.latest_command = None
        self.latest_command_time = 0

        # How long to publish a command
        self.duration = 1.0

        # Use to tell thread when to stop doin things
        self.running = True

        # Spin up thread to repeatedly publish commands
        self.q = queue.Queue()
        self.thread = threading.Thread(target=self._ros_loop)
        self.thread.daemon = True
        self.thread.start()

    def __del__(self):
        self.running = False
        self.thread.join()

    def _ros_loop(self):
        rclpy.init()
        self.pub = VelocityPublisher()

        while self.running:
            self._check_queue()

            # Check whether we've received *any* commands
            if self.latest_command is not None:
                # Check for expiration
                if (time.time() - self.latest_command_time) < self.duration:
                    self.pub.pub_velocity(*(self.latest_command))
                else:
                    self.latest_command = None

            # Rate limit
            time.sleep(0.2)

        self.pub.destroy_node()
        rclpy.shutdown()

    def _check_queue(self):
        if not self.q.empty():
            self.latest_command = self.q.get()
            self.latest_command_time = time.time()

    def pub_velocity(self, linear, angular):
        self.q.put((linear, angular))


def main(args=None):
    pub = VelocityInterface()

    for _ in range(10):
        pub.pub_velocity(10, -5)
        time.sleep(1)


if __name__ == "__main__":
    main()
