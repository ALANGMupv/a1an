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
        self.declare_parameter('camera_fourcc', 'MJPG')

        self.camera_index = int(self.get_parameter('camera_index').value)
        self.mirror_image = self._as_bool(self.get_parameter('mirror_image').value)
        self.model_complexity = int(self.get_parameter('model_complexity').value)
        self.frame_width = int(self.get_parameter('frame_width').value)
        self.frame_height = int(self.get_parameter('frame_height').value)
        self.camera_fps = int(self.get_parameter('camera_fps').value)
        self.camera_fourcc = str(self.get_parameter('camera_fourcc').value).upper()

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
        self.exercise_name = 'Elevacion de brazos'
        self.repetitions = 0
        self.arms_were_up = False
        self.last_feedback = 'Colocate frente a la camara'

        self.cap = self.cv2.VideoCapture(self.camera_index, self.cv2.CAP_V4L2)
        if not self.cap.isOpened():
            self.cap = self.cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            raise RuntimeError(f'No se pudo abrir la webcam con indice {self.camera_index}')

        if len(self.camera_fourcc) == 4:
            fourcc = self.cv2.VideoWriter_fourcc(*self.camera_fourcc)
            self.cap.set(self.cv2.CAP_PROP_FOURCC, fourcc)
        self.cap.set(self.cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
        self.cap.set(self.cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
        self.cap.set(self.cv2.CAP_PROP_FPS, self.camera_fps)
        self.cap.set(self.cv2.CAP_PROP_BUFFERSIZE, 1)

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
            f'{self.frame_width}x{self.frame_height}@{self.camera_fps}fps '
            f'({self.camera_fourcc}). '
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
            exercise_feedback = self._analyze_arm_raise(results.pose_landmarks.landmark)
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
            overlay_lines = [
                f'Ejercicio: {self.exercise_name}',
                f'Repeticiones: {self.repetitions}',
                exercise_feedback,
                f'Puntos visibles: {visible_landmarks}',
            ]
        else:
            status_msg.data = 'no_person_detected'
            self.arms_were_up = False
            overlay_lines = [
                f'Ejercicio: {self.exercise_name}',
                f'Repeticiones: {self.repetitions}',
                'Sin persona detectada',
            ]

        self.pose_status_pub.publish(status_msg)
        self._draw_overlay(frame, overlay_lines)
        self.cv2.imshow(self.window_name, frame)

        key = self.cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            self.get_logger().info('Cierre solicitado desde la ventana de OpenCV.')
            rclpy.shutdown()

    def _analyze_arm_raise(self, landmarks):
        pose_landmark = self.mp_pose.PoseLandmark
        required_landmarks = [
            pose_landmark.LEFT_SHOULDER,
            pose_landmark.RIGHT_SHOULDER,
            pose_landmark.LEFT_WRIST,
            pose_landmark.RIGHT_WRIST,
        ]

        if not self._landmarks_are_visible(landmarks, required_landmarks):
            self.last_feedback = 'Acercate o mejora la iluminacion'
            return self.last_feedback

        left_shoulder = landmarks[pose_landmark.LEFT_SHOULDER.value]
        right_shoulder = landmarks[pose_landmark.RIGHT_SHOULDER.value]
        left_wrist = landmarks[pose_landmark.LEFT_WRIST.value]
        right_wrist = landmarks[pose_landmark.RIGHT_WRIST.value]

        shoulder_y = (left_shoulder.y + right_shoulder.y) / 2.0
        margin = 0.06
        left_arm_up = left_wrist.y < shoulder_y - margin
        right_arm_up = right_wrist.y < shoulder_y - margin
        both_arms_up = left_arm_up and right_arm_up
        both_arms_down = (
            left_wrist.y > shoulder_y + margin
            and right_wrist.y > shoulder_y + margin
        )

        if both_arms_up and not self.arms_were_up:
            self.repetitions += 1
            self.arms_were_up = True
            self.last_feedback = 'Correcto: brazos elevados'
        elif both_arms_up:
            self.last_feedback = 'Manteniendo brazos arriba'
        elif both_arms_down:
            self.arms_were_up = False
            self.last_feedback = 'Baja controlada, prepara la siguiente'
        elif left_arm_up and not right_arm_up:
            self.last_feedback = 'Sube mas el brazo derecho'
        elif right_arm_up and not left_arm_up:
            self.last_feedback = 'Sube mas el brazo izquierdo'
        else:
            self.last_feedback = 'Sube ambos brazos por encima de los hombros'

        return self.last_feedback

    def _landmarks_are_visible(self, landmarks, required_landmarks):
        return all(
            landmarks[landmark.value].visibility >= 0.5
            for landmark in required_landmarks
        )

    def _draw_overlay(self, frame, lines):
        panel_height = 30 + 28 * len(lines)
        self.cv2.rectangle(frame, (8, 8), (560, panel_height), (20, 20, 20), -1)
        for index, line in enumerate(lines):
            color = (80, 230, 120) if index != 2 else (80, 210, 255)
            self.cv2.putText(
                frame,
                line,
                (18, 36 + index * 28),
                self.cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                color,
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
