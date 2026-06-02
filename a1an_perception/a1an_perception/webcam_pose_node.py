#!/usr/bin/env python3

import importlib

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class WebcamPoseNode(Node):
    """Open the computer webcam and draw MediaPipe human pose landmarks."""

    def __init__(self):
        super().__init__('webcam_pose_node')

        self.declare_parameter('camera_index', 0)
        self.declare_parameter('mirror_image', True)
        self.declare_parameter('model_complexity', 1)
        self.declare_parameter('frame_width', 640)
        self.declare_parameter('frame_height', 480)
        self.declare_parameter('camera_fps', 15)

        self.camera_index = int(self.get_parameter('camera_index').value)
        self.mirror_image = self._as_bool(self.get_parameter('mirror_image').value)
        self.model_complexity = int(self.get_parameter('model_complexity').value)
        self.frame_width = int(self.get_parameter('frame_width').value)
        self.frame_height = int(self.get_parameter('frame_height').value)
        self.camera_fps = int(self.get_parameter('camera_fps').value)

        self.cv2 = self._import_required_module(
            'cv2',
            'No se pudo importar OpenCV. Instala la dependencia con: pip install opencv-python',
        )
        self.mp = self._import_required_module(
            'mediapipe',
            'No se pudo importar MediaPipe. Instala la dependencia con: pip install mediapipe',
        )

        self.pose_status_pub = self.create_publisher(String, '/a1an/pose_status', 10)
        self.window_name = 'A1AN - Deteccion de pose humana'

        self.cap = self.cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            raise RuntimeError(f'No se pudo abrir la webcam con indice {self.camera_index}')

        self.cap.set(self.cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
        self.cap.set(self.cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
        self.cap.set(self.cv2.CAP_PROP_FPS, self.camera_fps)

        self.mp_pose = self.mp.solutions.pose
        self.mp_drawing = self.mp.solutions.drawing_utils
        self.mp_styles = self.mp.solutions.drawing_styles
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=self.model_complexity,
            enable_segmentation=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

        self.timer = self.create_timer(1.0 / self.camera_fps, self.process_frame)
        self.get_logger().info(
            'Webcam iniciada a '
            f'{self.frame_width}x{self.frame_height}@{self.camera_fps}fps. '
            'Pulsa q en la ventana de OpenCV para cerrar.'
        )

    def _import_required_module(self, module_name, error_message):
        try:
            return importlib.import_module(module_name)
        except ImportError as exc:
            raise RuntimeError(error_message) from exc

    def _as_bool(self, value):
        if isinstance(value, bool):
            return value
        return str(value).lower() in ('1', 'true', 'yes', 'on')

    def process_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            self.get_logger().warning('No se pudo leer un frame de la webcam.')
            return

        if self.mirror_image:
            frame = self.cv2.flip(frame, 1)

        rgb_frame = self.cv2.cvtColor(frame, self.cv2.COLOR_BGR2RGB)
        rgb_frame.flags.writeable = False
        results = self.pose.process(rgb_frame)
        rgb_frame.flags.writeable = True

        status_msg = String()
        if results.pose_landmarks:
            self.mp_drawing.draw_landmarks(
                frame,
                results.pose_landmarks,
                self.mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=self.mp_styles.get_default_pose_landmarks_style(),
            )
            visible_landmarks = sum(
                1
                for landmark in results.pose_landmarks.landmark
                if landmark.visibility >= 0.5
            )
            status_msg.data = f'person_detected visible_landmarks={visible_landmarks}'
            overlay_text = f'Persona detectada - puntos visibles: {visible_landmarks}'
        else:
            status_msg.data = 'no_person_detected'
            overlay_text = 'Sin persona detectada'

        self.pose_status_pub.publish(status_msg)
        self._draw_overlay(frame, overlay_text)
        self.cv2.imshow(self.window_name, frame)

        key = self.cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            self.get_logger().info('Cierre solicitado desde la ventana de OpenCV.')
            rclpy.shutdown()

    def _draw_overlay(self, frame, text):
        self.cv2.rectangle(frame, (8, 8), (470, 46), (20, 20, 20), -1)
        self.cv2.putText(
            frame,
            text,
            (18, 34),
            self.cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (80, 230, 120),
            2,
            self.cv2.LINE_AA,
        )

    def destroy_node(self):
        if hasattr(self, 'pose'):
            self.pose.close()
        if hasattr(self, 'cap'):
            self.cap.release()
        if hasattr(self, 'cv2'):
            self.cv2.destroyAllWindows()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = WebcamPoseNode()
        rclpy.spin(node)
    except ImportError as exc:
        print(f'Error importando dependencia: {exc}')
        print('Instala las dependencias con: pip install opencv-python mediapipe')
    except RuntimeError as exc:
        print(f'Error iniciando webcam_pose_node: {exc}')
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
