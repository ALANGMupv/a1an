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
        self.declare_parameter('min_area', 120)
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
                'min_area': 120,
                'max_aspect_ratio': 0.85,
                'mask_kernel': 5,
                'open_mask': True,
                'close_iterations': 2,
                'dilate_iterations': 1,
                'hsv_ranges': [
                    (np.array([95, 35, 25]), np.array([135, 255, 255])),
                ],
            },
            {
                'label': 'Telefono',
                'color': (255, 255, 0),
                'min_area': 8,
                'min_aspect_ratio': 1.1,
                'mask_kernel': 3,
                'open_mask': False,
                'close_iterations': 1,
                'dilate_iterations': 2,
                'hsv_ranges': [
                    (np.array([75, 25, 15]), np.array([110, 255, 255])),
                ],
            },
            {
                'label': 'Medicinas',
                'color': (255, 0, 255),
                'min_area': 6,
                'mask_kernel': 3,
                'open_mask': False,
                'close_iterations': 1,
                'dilate_iterations': 2,
                'bbox_padding': 10,
                'requires_light_background': True,
                'light_background_padding': 14,
                'min_light_background_ratio': 0.35,
                'min_center_y_ratio': 0.35,
                'max_width_ratio': 0.28,
                'max_height_ratio': 0.45,
                'hsv_ranges': [
                    (np.array([165, 80, 40]), np.array([176, 255, 255])),
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
            mask = self.clean_mask(mask, target)

            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if not contours:
                continue

            contour = self.find_best_contour(contours, target, hsv, image.shape)
            if contour is None:
                continue

            area = cv2.contourArea(contour)
            min_area = int(target.get('min_area', self.min_area))

            x, y, w, h = cv2.boundingRect(contour)
            x, y, w, h = self.expand_bbox(x, y, w, h, image.shape, int(target.get('bbox_padding', 0)))
            center_x = x + w // 2
            center_y = y + h // 2
            confidence = min(1.0, area / (min_area * 8.0))

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

    def find_best_contour(self, contours, target, hsv, shape):
        min_area = int(target.get('min_area', self.min_area))

        for contour in sorted(contours, key=cv2.contourArea, reverse=True):
            area = cv2.contourArea(contour)
            if area < min_area:
                continue

            _, _, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / float(h)
            if (
                self.matches_shape(target, aspect_ratio)
                and self.matches_size_and_position(contour, target, shape)
                and self.matches_context(contour, target, hsv)
            ):
                return contour

        return None

    @staticmethod
    def clean_mask(mask, target):
        kernel_size = int(target.get('mask_kernel', 5))
        kernel = np.ones((kernel_size, kernel_size), np.uint8)

        if target.get('open_mask', True):
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        close_iterations = int(target.get('close_iterations', 2))
        if close_iterations > 0:
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=close_iterations)

        dilate_iterations = int(target.get('dilate_iterations', 1))
        if dilate_iterations > 0:
            mask = cv2.dilate(mask, kernel, iterations=dilate_iterations)

        return mask

    @staticmethod
    def expand_bbox(x, y, w, h, shape, padding):
        if padding <= 0:
            return x, y, w, h

        height, width = shape[:2]
        x1 = max(0, x - padding)
        y1 = max(0, y - padding)
        x2 = min(width, x + w + padding)
        y2 = min(height, y + h + padding)
        return x1, y1, x2 - x1, y2 - y1

    @staticmethod
    def matches_shape(target, aspect_ratio):
        min_aspect_ratio = target.get('min_aspect_ratio')
        max_aspect_ratio = target.get('max_aspect_ratio')

        if min_aspect_ratio is not None and aspect_ratio < min_aspect_ratio:
            return False
        if max_aspect_ratio is not None and aspect_ratio > max_aspect_ratio:
            return False
        return True

    @staticmethod
    def matches_size_and_position(contour, target, shape):
        x, y, w, h = cv2.boundingRect(contour)
        height, width = shape[:2]
        center_y_ratio = (y + h / 2.0) / float(height)
        width_ratio = w / float(width)
        height_ratio = h / float(height)

        min_center_y_ratio = target.get('min_center_y_ratio')
        max_width_ratio = target.get('max_width_ratio')
        max_height_ratio = target.get('max_height_ratio')

        if min_center_y_ratio is not None and center_y_ratio < min_center_y_ratio:
            return False
        if max_width_ratio is not None and width_ratio > max_width_ratio:
            return False
        if max_height_ratio is not None and height_ratio > max_height_ratio:
            return False
        return True

    @staticmethod
    def matches_context(contour, target, hsv):
        if not target.get('requires_light_background', False):
            return True

        x, y, w, h = cv2.boundingRect(contour)
        padding = int(target.get('light_background_padding', 10))
        height, width = hsv.shape[:2]
        x1 = max(0, x - padding)
        y1 = max(0, y - padding)
        x2 = min(width, x + w + padding)
        y2 = min(height, y + h + padding)
        roi = hsv[y1:y2, x1:x2]

        if roi.size == 0:
            return False

        saturation = roi[:, :, 1]
        value = roi[:, :, 2]
        light_pixels = np.logical_and(saturation < 65, value > 120)
        light_ratio = np.count_nonzero(light_pixels) / float(light_pixels.size)
        return light_ratio >= float(target.get('min_light_background_ratio', 0.35))

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
