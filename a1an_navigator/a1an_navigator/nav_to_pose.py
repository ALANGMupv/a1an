#!/usr/bin/env python3
"""
nav_to_pose.py
===============
Cliente ROS 2 de acción que envía un único goal de navegación al action server
``navigate_to_pose`` de Nav2 y espera a que el robot llegue al destino.

Las coordenadas del goal se pasan como argumentos de línea de comandos.

Uso:
    ros2 run a1an_navigator nav_to_pose <x> <y>

Ejemplo:
    ros2 run a1an_navigator nav_to_pose 1.5 -0.8
"""

import sys

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose


class NavigateToPoseClient(Node):
    """
    Cliente de acción para enviar un goal puntual a Nav2.

    Envía un único ``NavigateToPose`` goal y cierra el nodo cuando
    el robot llega al destino o se produce un error.
    """

    def __init__(self):
        """Inicializa el nodo y el action client de ``navigate_to_pose``."""
        super().__init__('nav_to_pose_client')
        self._action_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')

    def send_goal(self, x, y, theta=0.0):
        """
        Construye y envía el goal de navegación al action server.

        Espera a que el server esté disponible antes de enviar el mensaje.

        Args:
            x     (float): Coordenada X del destino en el frame ``map``.
            y     (float): Coordenada Y del destino en el frame ``map``.
            theta (float): Componente Z del quaternion de orientación (yaw).
                           Por defecto 0.0 (mirando hacia adelante).
        """
        goal_msg = NavigateToPose.Goal()

        goal_pose = PoseStamped()
        goal_pose.header.frame_id = 'map'
        goal_pose.header.stamp = self.get_clock().now().to_msg()
        goal_pose.pose.position.x = x
        goal_pose.pose.position.y = y
        goal_pose.pose.orientation.w = 1.0
        goal_pose.pose.orientation.z = theta

        goal_msg.pose = goal_pose

        self.get_logger().info('Esperando al servidor de accion NavigateToPose...')
        self._action_client.wait_for_server()

        self.get_logger().info(f'Enviando objetivo de navegación: x={x}, y={y}')
        self._send_goal_future = self._action_client.send_goal_async(
            goal_msg,
            feedback_callback=self.feedback_callback
        )
        self._send_goal_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        """Callback ejecutado cuando el action server acepta o rechaza el goal."""
        try:
            goal_handle = future.result()
        except Exception as e:
            self.get_logger().error(f'Error al recibir respuesta del servidor: {e}')
            rclpy.shutdown()
            return

        if not goal_handle.accepted:
            self.get_logger().info('Objetivo rechazado :(')
            rclpy.shutdown()
            return

        self.get_logger().info('Objetivo aceptado, calculando e iniciando ruta...')
        self._get_result_future = goal_handle.get_result_async()
        self._get_result_future.add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):
        """Callback ejecutado cuando el robot alcanza el destino o falla la acción."""
        try:
            future.result()
            self.get_logger().info('Mision completada. ¡Llegamos a la meta!')
        except Exception as e:
            self.get_logger().error(f'La navegación terminó con error: {e}')
        finally:
            rclpy.shutdown()

    def feedback_callback(self, feedback_msg):
        """Callback de feedback periódico durante la navegación."""
        feedback = feedback_msg.feedback
        self.get_logger().info(f'Distancia restante: {feedback.distance_remaining:.2f} m')


def main(args=None):
    """Punto de entrada principal: parsea argumentos y lanza el cliente."""
    rclpy.init(args=args)

    if len(sys.argv) < 3:
        print('Uso: ros2 run a1an_navigator nav_to_pose <x> <y>')
        rclpy.shutdown()
        return

    try:
        x = float(sys.argv[1])
        y = float(sys.argv[2])
    except ValueError:
        print('Error: los argumentos <x> e <y> deben ser números decimales.')
        rclpy.shutdown()
        return

    action_client = NavigateToPoseClient()

    try:
        action_client.send_goal(x, y, 0.0)
        rclpy.spin(action_client)
    except KeyboardInterrupt:
        action_client.get_logger().info('Navegación cancelada por el usuario.')
    except Exception as e:
        action_client.get_logger().error(f'Error inesperado: {e}')
    finally:
        action_client.destroy_node()


if __name__ == '__main__':
    main()
