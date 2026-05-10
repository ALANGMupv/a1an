#!/usr/bin/env python3
import cv2
import rclpy
from cv_bridge import CvBridge, CvBridgeError
from rclpy.node import Node
from sensor_msgs.msg import Image


class CameraViewer(Node):
    def __init__(self):
        super().__init__('camera_viewer')

        self.declare_parameter('image_topic', '/camera/image_raw')
        self.declare_parameter('show_window', True)
        self.declare_parameter('log_every_n_frames', 30)

        self.image_topic = self.get_parameter('image_topic').value
        self.show_window = bool(self.get_parameter('show_window').value)
        self.log_every_n_frames = max(1, int(self.get_parameter('log_every_n_frames').value))

        self.bridge = CvBridge()
        self.frame_count = 0

        self.create_subscription(Image, self.image_topic, self.camera_callback, 10)
        self.get_logger().info(f'Leyendo imagenes desde {self.image_topic}')

    def camera_callback(self, data):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(data, desired_encoding='bgr8')
        except CvBridgeError as exc:
            self.get_logger().error(f'Error convirtiendo imagen: {exc}')
            return

        self.frame_count += 1
        if self.frame_count % self.log_every_n_frames == 0:
            height, width, channels = cv_image.shape
            self.get_logger().info(
                f'Imagen recibida: ancho={width}, alto={height}, canales={channels}'
            )

        if self.show_window:
            cv2.imshow('Imagen capturada por A1AN', cv_image)
            cv2.waitKey(1)

    def destroy_node(self):
        if self.show_window:
            cv2.destroyAllWindows()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = CameraViewer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
