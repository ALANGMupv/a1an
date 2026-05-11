#!/usr/bin/env python3
import json

import cv2
import numpy as np
import rclpy
from cv_bridge import CvBridge, CvBridgeError
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String


class AssistiveObjectDetector(Node):
    def __init__(self):
        super().__init__('assistive_object_detector')

        self.declare_parameter('image_topic', '/camera/image_raw')
        self.declare_parameter('show_window', False)
        self.declare_parameter('min_area', 500)
        self.declare_parameter('process_every_n_frames', 2)

        self.image_topic = self.get_parameter('image_topic').value
        self.show_window = bool(self.get_parameter('show_window').value)
        self.min_area = int(self.get_parameter('min_area').value)
        self.process_every_n_frames = max(1, int(self.get_parameter('process_every_n_frames').value))

        self.bridge = CvBridge()
        self.frame_count = 0
        self.last_message = ''

        self.detections_pub = self.create_publisher(String, '/a1an_vision/detected_objects', 10)
        self.status_pub = self.create_publisher(String, '/a1an_vision/status', 10)
        self.debug_image_pub = self.create_publisher(Image, '/a1an_vision/debug_image', 10)
        self.create_subscription(Image, self.image_topic, self.camera_callback, 10)

        self.targets = [
            {
                'label': 'Botella',
                'color': (255, 120, 0),
                'hsv_ranges': [
                    (np.array([105, 70, 50]), np.array([130, 255, 255])),
                ],
            },
            {
                'label': 'Telefono',
                'color': (255, 255, 0),
                'hsv_ranges': [
                    (np.array([80, 70, 50]), np.array([100, 255, 255])),
                ],
            },
            {
                'label': 'Medicinas',
                'color': (0, 0, 255),
                'hsv_ranges': [
                    (np.array([0, 80, 50]), np.array([12, 255, 255])),
                    (np.array([168, 80, 50]), np.array([180, 255, 255])),
                ],
            },
        ]

        self.get_logger().info(f'Detector de objetos listo. Escuchando {self.image_topic}')

    def camera_callback(self, data):
        self.frame_count += 1
        if self.frame_count % self.process_every_n_frames != 0:
            return

        try:
            image = self.bridge.imgmsg_to_cv2(data, desired_encoding='bgr8')
        except CvBridgeError as exc:
            self.get_logger().error(f'Error convirtiendo imagen: {exc}')
            return

        detections, debug_image = self.detect_objects(image)
        self.publish_results(detections, image.shape)
        self.publish_debug_image(debug_image, data.header)

        if self.show_window:
            cv2.imshow('A1AN deteccion de objetos', debug_image)
            cv2.waitKey(1)

    def detect_objects(self, image):
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        output = image.copy()
        detections = []

        for target in self.targets:
            mask = self.create_mask(hsv, target['hsv_ranges'])
            mask = self.clean_mask(mask)

            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if not contours:
                continue

            contour = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(contour)
            if area < self.min_area:
                continue

            x, y, w, h = cv2.boundingRect(contour)
            center_x = x + w // 2
            center_y = y + h // 2
            confidence = min(1.0, area / (self.min_area * 8.0))

            detection = {
                'label': target['label'],
                'confidence': round(confidence, 2),
                'center_x': int(center_x),
                'center_y': int(center_y),
                'bbox': [int(x), int(y), int(w), int(h)],
                'position': self.position_name(center_x, center_y, image.shape),
            }
            detections.append(detection)

            cv2.rectangle(output, (x, y), (x + w, y + h), target['color'], 2)
            cv2.circle(output, (center_x, center_y), 5, target['color'], -1)
            cv2.putText(
                output,
                f"{target['label']} {int(confidence * 100)}%",
                (x, max(25, y - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                target['color'],
                2,
            )

        if not detections:
            cv2.putText(
                output,
                'No se detectan objetos relevantes',
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2,
            )

        return detections, output

    @staticmethod
    def create_mask(hsv, hsv_ranges):
        mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
        for lower, upper in hsv_ranges:
            mask = cv2.bitwise_or(mask, cv2.inRange(hsv, lower, upper))
        return mask

    @staticmethod
    def clean_mask(mask):
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        return cv2.dilate(mask, kernel, iterations=1)

    @staticmethod
    def position_name(center_x, center_y, shape):
        height, width = shape[:2]
        horizontal = 'izquierda' if center_x < width / 3 else 'derecha' if center_x > 2 * width / 3 else 'centro'
        vertical = 'arriba' if center_y < height / 3 else 'abajo' if center_y > 2 * height / 3 else 'centro'
        return f'{vertical}-{horizontal}'

    def publish_results(self, detections, shape):
        height, width = shape[:2]
        payload = {
            'detected': bool(detections),
            'message': 'Objetos relevantes detectados' if detections else 'No se han detectado objetos relevantes en la escena',
            'image_width': int(width),
            'image_height': int(height),
            'objects': detections,
        }
        text = json.dumps(payload, ensure_ascii=False)
        self.detections_pub.publish(String(data=text))
        self.status_pub.publish(String(data=payload['message']))

        if text != self.last_message:
            if detections:
                labels = ', '.join(detection['label'] for detection in detections)
                positions = ', '.join(
                    f"{detection['label']} en {detection['position']}"
                    for detection in detections
                )
                self.get_logger().info(f'Objetos detectados: {labels}. Posiciones: {positions}')
            else:
                self.get_logger().info(payload['message'])
            self.last_message = text

    def publish_debug_image(self, image, header):
        try:
            image_msg = self.bridge.cv2_to_imgmsg(image, encoding='bgr8')
        except CvBridgeError as exc:
            self.get_logger().error(f'Error publicando imagen procesada: {exc}')
            return
        image_msg.header = header
        self.debug_image_pub.publish(image_msg)

    def destroy_node(self):
        if self.show_window:
            cv2.destroyAllWindows()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = AssistiveObjectDetector()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
