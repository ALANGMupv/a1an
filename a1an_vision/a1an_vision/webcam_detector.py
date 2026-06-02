#!/usr/bin/env python3
import os
import cv2
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from ultralytics import YOLO


class WebcamDetector(Node):
    def __init__(self):
        super().__init__('webcam_detector')

       
        model_path = os.path.join(os.path.expanduser('~'), 'turtlebot3_ws', 'src', 'a1an', 'a1an', 'a1an_vision', 'model', 'best.pt')
        self.model = YOLO(model_path)
        self.publisher = self.create_publisher(String, '/a1an_vision/yolo_detections', 10)

        # Video (actual)
        # self.cap = cv2.VideoCapture('/home/santi/turtlebot3_ws/src/a1an/a1an/a1an_vision/video/videoDeteccionObjetosYOLO.mp4')

        # Webcam (cuando funcione)
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.get_logger().error('No se pudo abrir la webcam')
            return

        self.create_timer(0.033, self.process_frame)
        self.get_logger().info('WebcamDetector YOLO iniciado')

    def process_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        results = self.model(frame, conf=0.5, verbose=False)
        annotated = results[0].plot()

        detections = []
        for box in results[0].boxes:
            cls = self.model.names[int(box.cls)]
            conf = float(box.conf)
            detections.append(f'{cls}:{conf:.2f}')

        if detections:
            msg = String()
            msg.data = ', '.join(detections)
            self.publisher.publish(msg)
            self.get_logger().info(f'YOLO detectado: {msg.data}')

        cv2.imshow('A1AN YOLO - Webcam', annotated)
        cv2.waitKey(1)

    def destroy_node(self):
        self.cap.release()
        cv2.destroyAllWindows()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = WebcamDetector()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
