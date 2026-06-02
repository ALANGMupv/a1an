#!/usr/bin/env python3
"""
a1an_vision — Nodo de detección de objetos con YOLO11 (ultralytics).

Mantiene la misma interfaz de topics que el detector anterior:
  - /a1an_vision/detected_objects  (std_msgs/String  — JSON)
  - /a1an_vision/status            (std_msgs/String  — texto)
  - /a1an_vision/debug_image       (sensor_msgs/Image — imagen anotada BGR8)

Suscribe:
  - /camera/image_raw              (sensor_msgs/Image)
"""

import json
import os

import cv2
import rclpy
from cv_bridge import CvBridge, CvBridgeError
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
from ultralytics import YOLO

# Mapeo clase YOLO → nombre en español (para compatibilidad con la web)
CLASS_LABELS_ES = {
    'waterbottle': 'Botella',
    'remote':      'Mando',
    'cellphone':   'Telefono',
    'person':      'Persona',
}

# Colores BGR por clase para los bounding boxes
CLASS_COLORS = {
    'waterbottle': (255, 120,   0),   # naranja
    'remote':      (  0, 200, 255),   # amarillo cian
    'cellphone':   (255, 255,   0),   # amarillo
    'person':      (  0, 255, 128),   # verde claro
}

DEFAULT_COLOR = (200, 200, 200)


class AssistiveObjectDetector(Node):
    """Detector de objetos domésticos mediante YOLO11."""

    def __init__(self):
        super().__init__('assistive_object_detector')

        # ── Parámetros ──────────────────────────────────────────────────────
        self.declare_parameter('image_topic', '/camera/image_raw')
        self.declare_parameter('show_window', False)
        self.declare_parameter('confidence_threshold', 0.50)
        self.declare_parameter('process_every_n_frames', 2)
        self.declare_parameter(
            'model_path',
            os.path.join(
                os.path.dirname(__file__),
                '..', '..', 'model', 'best.pt',
            ),
        )

        self.image_topic = self.get_parameter('image_topic').value
        self.show_window = bool(self.get_parameter('show_window').value)
        self.conf_threshold = float(self.get_parameter('confidence_threshold').value)
        self.process_every_n_frames = max(
            1, int(self.get_parameter('process_every_n_frames').value)
        )
        model_path = str(self.get_parameter('model_path').value)

        # ── Cargar modelo ────────────────────────────────────────────────────
        try:
            self.model = YOLO(model_path)
            self.get_logger().info(f'Modelo YOLO11 cargado desde: {model_path}')
        except Exception as exc:
            self.get_logger().fatal(f'No se pudo cargar el modelo YOLO: {exc}')
            raise

        # ── ROS ──────────────────────────────────────────────────────────────
        self.bridge = CvBridge()
        self.frame_count = 0
        self.last_message = ''

        self.detections_pub = self.create_publisher(String, '/a1an_vision/detected_objects', 10)
        self.status_pub     = self.create_publisher(String, '/a1an_vision/status', 10)
        self.debug_image_pub = self.create_publisher(Image, '/a1an_vision/debug_image', 10)
        self.create_subscription(Image, self.image_topic, self.camera_callback, 10)

        self.get_logger().info(
            f'Detector listo. Escuchando {self.image_topic} | '
            f'Confianza mínima: {self.conf_threshold}'
        )

    # ── Callback principal ───────────────────────────────────────────────────

    def camera_callback(self, msg: Image) -> None:
        """Procesa cada frame de la cámara y publica resultados."""
        self.frame_count += 1
        if self.frame_count % self.process_every_n_frames != 0:
            return

        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except CvBridgeError as exc:
            self.get_logger().error(f'Error convirtiendo imagen: {exc}')
            return

        detections, debug_frame = self._run_inference(frame)
        self._publish_results(detections, frame.shape)
        self._publish_debug_image(debug_frame, msg.header)

        if self.show_window:
            cv2.imshow('A1AN — Detección YOLO11', debug_frame)
            cv2.waitKey(1)

    # ── Inferencia ───────────────────────────────────────────────────────────

    def _run_inference(self, frame):
        """Ejecuta YOLO11 sobre el frame y devuelve detecciones + imagen anotada."""
        output = frame.copy()
        detections = []
        height, width = frame.shape[:2]

        try:
            results = self.model(frame, conf=self.conf_threshold, verbose=False)
        except Exception as exc:
            self.get_logger().error(f'Error en inferencia YOLO: {exc}')
            return detections, output

        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue

            for box in boxes:
                cls_id = int(box.cls[0])
                conf   = float(box.conf[0])
                label  = self.model.names[cls_id]          # nombre inglés del modelo
                label_es = CLASS_LABELS_ES.get(label, label)
                color  = CLASS_COLORS.get(label, DEFAULT_COLOR)

                x1, y1, x2, y2 = map(int, box.xyxy[0])
                bw = x2 - x1
                bh = y2 - y1
                cx = x1 + bw // 2
                cy = y1 + bh // 2

                detection = {
                    'label':      label_es,
                    'label_en':   label,
                    'confidence': round(conf, 2),
                    'center_x':   cx,
                    'center_y':   cy,
                    'bbox':       [x1, y1, bw, bh],
                    'position':   self._position_name(cx, cy, frame.shape),
                }
                detections.append(detection)

                # Dibujar bounding box
                cv2.rectangle(output, (x1, y1), (x2, y2), color, 2)
                cv2.circle(output, (cx, cy), 5, color, -1)
                cv2.putText(
                    output,
                    f'{label_es} {int(conf * 100)}%',
                    (x1, max(25, y1 - 8)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    color,
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

    # ── Publicación ──────────────────────────────────────────────────────────

    def _publish_results(self, detections: list, shape: tuple) -> None:
        """Publica el JSON de detecciones y el mensaje de estado."""
        height, width = shape[:2]
        payload = {
            'detected':      bool(detections),
            'message':       (
                'Objetos relevantes detectados'
                if detections
                else 'No se han detectado objetos relevantes en la escena'
            ),
            'image_width':   width,
            'image_height':  height,
            'objects':       detections,
        }
        text = json.dumps(payload, ensure_ascii=False)
        self.detections_pub.publish(String(data=text))
        self.status_pub.publish(String(data=payload['message']))

        if text != self.last_message:
            self.get_logger().info(payload['message'])
            self.last_message = text

    def _publish_debug_image(self, image, header) -> None:
        """Publica la imagen anotada para web_video_server."""
        try:
            img_msg = self.bridge.cv2_to_imgmsg(image, encoding='bgr8')
        except CvBridgeError as exc:
            self.get_logger().error(f'Error publicando imagen procesada: {exc}')
            return
        img_msg.header = header
        self.debug_image_pub.publish(img_msg)

    # ── Utilidades ───────────────────────────────────────────────────────────

    @staticmethod
    def _position_name(cx: int, cy: int, shape: tuple) -> str:
        """Devuelve la posición relativa del objeto en la imagen."""
        height, width = shape[:2]
        h = 'izquierda' if cx < width / 3 else 'derecha' if cx > 2 * width / 3 else 'centro'
        v = 'arriba'    if cy < height / 3 else 'abajo'  if cy > 2 * height / 3 else 'centro'
        return f'{v}-{h}'

    def destroy_node(self) -> None:
        if self.show_window:
            cv2.destroyAllWindows()
        super().destroy_node()


# ── Entrypoint ───────────────────────────────────────────────────────────────

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
