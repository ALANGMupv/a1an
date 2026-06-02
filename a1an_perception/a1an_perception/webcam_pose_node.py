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
        self.declare_parameter('target_repetitions', 10)

        self.camera_index = int(self.get_parameter('camera_index').value)
        self.mirror_image = self._as_bool(self.get_parameter('mirror_image').value)
        self.model_complexity = int(self.get_parameter('model_complexity').value)
        self.frame_width = int(self.get_parameter('frame_width').value)
        self.frame_height = int(self.get_parameter('frame_height').value)
        self.camera_fps = int(self.get_parameter('camera_fps').value)
        self.camera_fourcc = str(self.get_parameter('camera_fourcc').value).upper()
        self.target_repetitions = int(self.get_parameter('target_repetitions').value)

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
        self.exercise_status = {
            'state': 'Preparacion',
            'feedback': 'Colocate frente a la camara',
            'detail': 'Mantente de pie y visible de cintura hacia arriba',
            'color': (184, 178, 83),
        }

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
            self.exercise_status = self._analyze_arm_raise(results.pose_landmarks.landmark)
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
            status_msg.data = (
                f"person_detected repetitions={self.repetitions} "
                f"state={self.exercise_status['state']} "
                f"feedback={self.exercise_status['feedback']} "
                f"visible_landmarks={visible_landmarks}"
            )
        else:
            status_msg.data = 'no_person_detected'
            self.arms_were_up = False
            visible_landmarks = 0
            self.exercise_status = {
                'state': 'Sin deteccion',
                'feedback': 'No se detecta a la persona',
                'detail': 'Colocate centrado y visible de cintura hacia arriba',
                'color': (184, 178, 83),
            }

        self.pose_status_pub.publish(status_msg)
        self._draw_rehab_overlay(frame, visible_landmarks)
        self.cv2.imshow(self.window_name, frame)

        key = self.cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            self.get_logger().info('Cierre solicitado desde la ventana de OpenCV.')
            rclpy.shutdown()
        elif key == ord('r'):
            self.repetitions = 0
            self.arms_were_up = False
            self.get_logger().info('Contador de rehabilitacion reiniciado.')

    def _analyze_arm_raise(self, landmarks):
        pose_landmark = self.mp_pose.PoseLandmark
        required_landmarks = [
            pose_landmark.LEFT_SHOULDER,
            pose_landmark.RIGHT_SHOULDER,
            pose_landmark.LEFT_WRIST,
            pose_landmark.RIGHT_WRIST,
        ]

        if not self._landmarks_are_visible(landmarks, required_landmarks):
            return {
                'state': 'Ajuste',
                'feedback': 'Mejora la posicion',
                'detail': 'Necesito ver hombros y manos para evaluar el movimiento',
                'color': (184, 178, 83),
            }

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

        if self.repetitions >= self.target_repetitions:
            if both_arms_down:
                self.arms_were_up = False
            return {
                'state': 'Completado',
                'feedback': 'Sesion completada',
                'detail': 'Objetivo alcanzado. Buen control del ejercicio',
                'color': (129, 185, 16),
            }

        if both_arms_up and not self.arms_were_up:
            self.repetitions += 1
            self.arms_were_up = True
            return {
                'state': 'Correcto',
                'feedback': 'Repeticion valida',
                'detail': 'Buen rango de movimiento. Baja despacio',
                'color': (129, 185, 16),
            }
        elif both_arms_up:
            return {
                'state': 'Control',
                'feedback': 'Manteniendo posicion',
                'detail': 'Mantente estable y evita movimientos bruscos',
                'color': (129, 185, 16),
            }
        elif both_arms_down:
            self.arms_were_up = False
            return {
                'state': 'Preparado',
                'feedback': 'Listo para continuar',
                'detail': 'Eleva ambos brazos hasta superar los hombros',
                'color': (184, 178, 83),
            }
        elif left_arm_up and not right_arm_up:
            return {
                'state': 'Correccion',
                'feedback': 'Solo hay un brazo elevado',
                'detail': 'Sube el otro brazo para trabajar de forma simetrica',
                'color': (11, 158, 245),
            }
        elif right_arm_up and not left_arm_up:
            return {
                'state': 'Correccion',
                'feedback': 'Solo hay un brazo elevado',
                'detail': 'Sube el otro brazo para trabajar de forma simetrica',
                'color': (11, 158, 245),
            }
        else:
            return {
                'state': 'En progreso',
                'feedback': 'Eleva ambos brazos',
                'detail': 'Busca un movimiento lento, estable y completo',
                'color': (184, 178, 83),
            }

    def _landmarks_are_visible(self, landmarks, required_landmarks):
        return all(
            landmarks[landmark.value].visibility >= 0.5
            for landmark in required_landmarks
        )

    def _draw_rehab_overlay(self, frame, visible_landmarks):
        if frame.shape[1] >= 900:
            self._draw_rehab_sidebar(frame, visible_landmarks)
            return

        self._draw_rehab_compact_panel(frame, visible_landmarks)

    def _draw_rehab_sidebar(self, frame, visible_landmarks):
        status = self.exercise_status
        frame_h, frame_w = frame.shape[:2]
        panel_w = 360
        panel_h = frame_h - 32
        panel_x = frame_w - panel_w - 16
        panel_y = 16

        colors = self._brand_colors()
        self._draw_filled_box(frame, panel_x, panel_y, panel_w, panel_h, colors['bg'])
        self.cv2.rectangle(
            frame,
            (panel_x, panel_y),
            (panel_x + panel_w, panel_y + panel_h),
            colors['border'],
            1,
        )

        self._draw_filled_box(frame, panel_x, panel_y, panel_w, 92, colors['primary'])
        self.cv2.putText(
            frame,
            'Safe&Sound Robotics',
            (panel_x + 22, panel_y + 34),
            self.cv2.FONT_HERSHEY_SIMPLEX,
            0.56,
            colors['white'],
            1,
            self.cv2.LINE_AA,
        )
        self.cv2.putText(
            frame,
            'A1AN Rehab',
            (panel_x + 22, panel_y + 70),
            self.cv2.FONT_HERSHEY_SIMPLEX,
            0.92,
            colors['white'],
            2,
            self.cv2.LINE_AA,
        )

        card_x = panel_x + 22
        card_w = panel_w - 44
        reps_card_y = panel_y + 122
        self._draw_card(frame, card_x, reps_card_y, card_w, 142)
        self.cv2.putText(
            frame,
            'Progreso del ejercicio',
            (card_x + 16, reps_card_y + 28),
            self.cv2.FONT_HERSHEY_SIMPLEX,
            0.48,
            colors['gray'],
            1,
            self.cv2.LINE_AA,
        )
        self.cv2.putText(
            frame,
            f'{self.repetitions}/{self.target_repetitions}',
            (card_x + 16, reps_card_y + 76),
            self.cv2.FONT_HERSHEY_SIMPLEX,
            1.18,
            colors['primary'],
            3,
            self.cv2.LINE_AA,
        )
        self.cv2.putText(
            frame,
            'repeticiones',
            (card_x + 18, reps_card_y + 102),
            self.cv2.FONT_HERSHEY_SIMPLEX,
            0.46,
            colors['gray'],
            1,
            self.cv2.LINE_AA,
        )
        self._draw_progress_bar(
            frame,
            card_x + 16,
            reps_card_y + 116,
            card_w - 32,
            12,
            self.repetitions / max(1, self.target_repetitions),
            colors['accent'],
        )

        feedback_y = reps_card_y + 164
        self._draw_card(frame, card_x, feedback_y, card_w, 172)
        self.cv2.putText(
            frame,
            'Feedback',
            (card_x + 16, feedback_y + 28),
            self.cv2.FONT_HERSHEY_SIMPLEX,
            0.48,
            colors['gray'],
            1,
            self.cv2.LINE_AA,
        )
        self._put_wrapped_text(
            frame,
            status['feedback'],
            card_x + 16,
            feedback_y + 62,
            card_w - 32,
            0.6,
            status['color'],
            2,
        )
        self._put_wrapped_text(
            frame,
            status['detail'],
            card_x + 16,
            feedback_y + 108,
            card_w - 32,
            0.45,
            colors['text'],
            1,
        )

        metric_y = feedback_y + 194
        self._draw_card(frame, card_x, metric_y, card_w, 112)
        self.cv2.putText(
            frame,
            'Seguimiento',
            (card_x + 16, metric_y + 28),
            self.cv2.FONT_HERSHEY_SIMPLEX,
            0.48,
            colors['gray'],
            1,
            self.cv2.LINE_AA,
        )
        self._draw_metric(frame, card_x + 16, metric_y + 62, 'Puntos visibles', str(visible_landmarks))
        self._draw_metric(frame, card_x + 164, metric_y + 62, 'Camara', f'{self.camera_fps} FPS')

        footer_y = panel_y + panel_h - 70
        self.cv2.line(
            frame,
            (panel_x + 22, footer_y - 16),
            (panel_x + panel_w - 22, footer_y - 16),
            colors['border'],
            1,
        )
        self._draw_key_hint(frame, panel_x + 22, footer_y - 1, 'q', 'salir')
        self._draw_key_hint(frame, panel_x + 140, footer_y - 1, 'r', 'reiniciar')
        self._draw_mini_dot(frame, panel_x + 24, footer_y + 32, colors['accent'])
        self.cv2.putText(
            frame,
            self.exercise_name,
            (panel_x + 40, footer_y + 38),
            self.cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            colors['secondary'],
            1,
            self.cv2.LINE_AA,
        )

    def _draw_rehab_compact_panel(self, frame, visible_landmarks):
        status = self.exercise_status
        colors = self._brand_colors()
        panel_x, panel_y = 12, 12
        panel_w, panel_h = 610, 188
        self._draw_filled_box(frame, panel_x, panel_y, panel_w, panel_h, colors['bg'])
        self.cv2.rectangle(
            frame,
            (panel_x, panel_y),
            (panel_x + panel_w, panel_y + panel_h),
            colors['border'],
            1,
        )

        self.cv2.putText(
            frame,
            'A1AN Rehab',
            (panel_x + 18, panel_y + 34),
            self.cv2.FONT_HERSHEY_SIMPLEX,
            0.85,
            colors['primary'],
            2,
            self.cv2.LINE_AA,
        )
        self.cv2.putText(
            frame,
            self.exercise_name,
            (panel_x + 20, panel_y + 66),
            self.cv2.FONT_HERSHEY_SIMPLEX,
            0.58,
            colors['gray'],
            1,
            self.cv2.LINE_AA,
        )

        self._draw_status_chip(frame, panel_x + panel_w - 178, panel_y + 18, status)

        reps_text = f'{self.repetitions}/{self.target_repetitions} repeticiones'
        self.cv2.putText(
            frame,
            reps_text,
            (panel_x + 20, panel_y + 104),
            self.cv2.FONT_HERSHEY_SIMPLEX,
            0.72,
            colors['primary'],
            2,
            self.cv2.LINE_AA,
        )
        self._draw_progress_bar(
            frame,
            panel_x + 20,
            panel_y + 120,
            panel_w - 40,
            14,
            self.repetitions / max(1, self.target_repetitions),
            colors['accent'],
        )

        self.cv2.putText(
            frame,
            status['feedback'],
            (panel_x + 20, panel_y + 158),
            self.cv2.FONT_HERSHEY_SIMPLEX,
            0.68,
            status['color'],
            2,
            self.cv2.LINE_AA,
        )
        self.cv2.putText(
            frame,
            status['detail'],
            (panel_x + 20, panel_y + 181),
            self.cv2.FONT_HERSHEY_SIMPLEX,
            0.47,
            colors['text'],
            1,
            self.cv2.LINE_AA,
        )

        footer = f'Puntos visibles: {visible_landmarks}   q: salir   r: reiniciar'
        self._draw_filled_box(frame, 12, frame.shape[0] - 42, 430, 30, colors['bg'])
        self.cv2.putText(
            frame,
            footer,
            (26, frame.shape[0] - 20),
            self.cv2.FONT_HERSHEY_SIMPLEX,
            0.48,
            colors['gray'],
            1,
            self.cv2.LINE_AA,
        )

    def _draw_status_chip(self, frame, x, y, status):
        colors = self._brand_colors()
        self._draw_filled_box(frame, x, y, 158, 34, colors['chip'])
        self.cv2.rectangle(frame, (x, y), (x + 158, y + 34), colors['border'], 1)
        self.cv2.circle(frame, (x + 19, y + 17), 6, status['color'], -1)
        self.cv2.putText(
            frame,
            status['state'],
            (x + 34, y + 23),
            self.cv2.FONT_HERSHEY_SIMPLEX,
            0.48,
            colors['primary'],
            1,
            self.cv2.LINE_AA,
        )

    def _draw_progress_bar(self, frame, x, y, width, height, progress, color):
        progress = max(0.0, min(1.0, progress))
        colors = self._brand_colors()
        self._draw_filled_box(frame, x, y, width, height, colors['border'])
        fill_width = int(width * progress)
        if fill_width > 0:
            self._draw_filled_box(frame, x, y, fill_width, height, color)

    def _draw_key_hint(self, frame, x, y, key, label):
        colors = self._brand_colors()
        self._draw_filled_box(frame, x, y, 28, 24, colors['accent'])
        self.cv2.putText(
            frame,
            key,
            (x + 8, y + 17),
            self.cv2.FONT_HERSHEY_SIMPLEX,
            0.48,
            colors['white'],
            1,
            self.cv2.LINE_AA,
        )
        self.cv2.putText(
            frame,
            label,
            (x + 38, y + 17),
            self.cv2.FONT_HERSHEY_SIMPLEX,
            0.48,
            colors['gray'],
            1,
            self.cv2.LINE_AA,
        )

    def _draw_filled_box(self, frame, x, y, width, height, color):
        self.cv2.rectangle(frame, (x, y), (x + width, y + height), color, -1)

    def _draw_card(self, frame, x, y, width, height):
        colors = self._brand_colors()
        self._draw_filled_box(frame, x + 2, y + 3, width, height, (222, 226, 232))
        self._draw_filled_box(frame, x, y, width, height, colors['white'])
        self.cv2.rectangle(frame, (x, y), (x + width, y + height), colors['border'], 1)

    def _draw_metric(self, frame, x, y, label, value):
        colors = self._brand_colors()
        self.cv2.putText(
            frame,
            value,
            (x, y),
            self.cv2.FONT_HERSHEY_SIMPLEX,
            0.72,
            colors['primary'],
            2,
            self.cv2.LINE_AA,
        )
        self.cv2.putText(
            frame,
            label,
            (x, y + 26),
            self.cv2.FONT_HERSHEY_SIMPLEX,
            0.39,
            colors['gray'],
            1,
            self.cv2.LINE_AA,
        )

    def _put_wrapped_text(self, frame, text, x, y, max_width, scale, color, thickness):
        words = text.split()
        line = ''
        line_height = int(28 * scale) + 11
        for word in words:
            candidate = word if not line else f'{line} {word}'
            size = self.cv2.getTextSize(
                candidate,
                self.cv2.FONT_HERSHEY_SIMPLEX,
                scale,
                thickness,
            )[0]
            if size[0] > max_width and line:
                self.cv2.putText(
                    frame,
                    line,
                    (x, y),
                    self.cv2.FONT_HERSHEY_SIMPLEX,
                    scale,
                    color,
                    thickness,
                    self.cv2.LINE_AA,
                )
                y += line_height
                line = word
            else:
                line = candidate
        if line:
            self.cv2.putText(
                frame,
                line,
                (x, y),
                self.cv2.FONT_HERSHEY_SIMPLEX,
                scale,
                color,
                thickness,
                self.cv2.LINE_AA,
            )

    def _brand_colors(self):
        return {
            'primary': (83, 50, 29),
            'secondary': (146, 92, 42),
            'accent': (184, 178, 83),
            'white': (255, 255, 255),
            'bg': (250, 247, 245),
            'text': (55, 41, 31),
            'gray': (128, 114, 107),
            'border': (235, 231, 229),
            'chip': (250, 243, 219),
        }

    def _draw_mini_dot(self, frame, x, y, color):
        self.cv2.circle(frame, (x, y), 5, color, -1)

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
