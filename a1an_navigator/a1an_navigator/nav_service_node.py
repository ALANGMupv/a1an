#!/usr/bin/env python3
"""
nav_service_node.py
====================
Nodo ROS 2 que actúa como servicio de navegación autónoma para el robot A1AN.

Escucha dos topics:
- ``/nav_goal``   (Float64MultiArray) — Recibe un goal de navegación ``[x, y]``
  y lo envía al action server ``navigate_to_pose`` de Nav2.
- ``/nav_cancel`` (Bool)             — Cancela la navegación activa si se
  recibe ``True``.

El nodo es completamente reactivo: no bloquea el hilo principal y gestiona
el ciclo de vida de las acciones mediante callbacks asincrónicos.

Uso:
    ros2 run a1an_navigator nav_service_node
"""

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
from std_msgs.msg import Float64MultiArray, Bool


class NavService(Node):
    """
    Nodo de servicio de navegación basado en el action client de Nav2.

    Recibe goals y cancelaciones a través de topics ROS 2 y los traduce
    a llamadas asíncronas al action server ``navigate_to_pose``.
    """

    def __init__(self):
        """Inicializa el nodo, el action client y las suscripciones."""
        super().__init__('nav_service_node')

        self._action_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        self._goal_handle = None

        # Suscriptor al topic /nav_goal — recibe [x, y]
        self.create_subscription(
            Float64MultiArray,
            '/nav_goal',
            self.nav_goal_callback,
            10
        )

        # Suscriptor al topic /nav_cancel — recibe True para cancelar
        self.create_subscription(
            Bool,
            '/nav_cancel',
            self.cancel_callback,
            10
        )

        self.get_logger().info('NavService node listo. Escuchando en /nav_goal y /nav_cancel')

    # ------------------------------------------------------------------
    # Callbacks de suscripción
    # ------------------------------------------------------------------

    def nav_goal_callback(self, msg):
        """
        Callback ejecutado al recibir un goal en ``/nav_goal``.

        Valida que el mensaje contenga al menos dos valores [x, y]
        y lanza la navegación hacia esa posición.

        Args:
            msg (Float64MultiArray): Mensaje con las coordenadas [x, y].
        """
        if len(msg.data) < 2:
            self.get_logger().error('Mensaje inválido, se esperan 2 valores [x, y]')
            return

        x = msg.data[0]
        y = msg.data[1]
        self.get_logger().info(f'Goal recibido: x={x}, y={y}')

        try:
            self.send_goal(x, y)
        except Exception as e:
            self.get_logger().error(f'Error al enviar el goal de navegación: {e}')

    def cancel_callback(self, msg):
        """
        Callback ejecutado al recibir una señal en ``/nav_cancel``.

        Cancela el goal activo si existe y si el mensaje es ``True``.

        Args:
            msg (Bool): ``True`` para cancelar la navegación activa.
        """
        if msg.data and self._goal_handle:
            self.get_logger().info('Cancelando navegación...')
            try:
                self._goal_handle.cancel_goal_async()
            except Exception as e:
                self.get_logger().error(f'Error al cancelar el goal: {e}')
        else:
            self.get_logger().info('No hay goal activo para cancelar')

    # ------------------------------------------------------------------
    # Lógica de envío de goal
    # ------------------------------------------------------------------

    def send_goal(self, x, y):
        """
        Construye y envía un goal de navegación al action server de Nav2.

        Espera a que el action server esté disponible antes de enviar.

        Args:
            x (float): Coordenada X del destino en el frame ``map``.
            y (float): Coordenada Y del destino en el frame ``map``.
        """
        goal_msg = NavigateToPose.Goal()
        goal_pose = PoseStamped()
        goal_pose.header.frame_id = 'map'
        goal_pose.header.stamp = self.get_clock().now().to_msg()
        goal_pose.pose.position.x = x
        goal_pose.pose.position.y = y
        goal_pose.pose.orientation.w = 1.0
        goal_msg.pose = goal_pose

        self.get_logger().info('Esperando al action server...')
        self._action_client.wait_for_server()
        self.get_logger().info('Enviando goal...')

        self._action_client.send_goal_async(
            goal_msg,
            feedback_callback=self.feedback_callback
        ).add_done_callback(self.goal_response_callback)

    # ------------------------------------------------------------------
    # Callbacks del action client
    # ------------------------------------------------------------------

    def goal_response_callback(self, future):
        """
        Callback ejecutado cuando el action server acepta o rechaza el goal.

        Args:
            future: Future con el handle del goal enviado.
        """
        try:
            goal_handle = future.result()
        except Exception as e:
            self.get_logger().error(f'Error al obtener respuesta del goal: {e}')
            return

        if not goal_handle.accepted:
            self.get_logger().info('Goal rechazado')
            return

        self._goal_handle = goal_handle
        self.get_logger().info('Goal aceptado, navegando...')
        goal_handle.get_result_async().add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):
        """
        Callback ejecutado cuando el robot llega al destino o falla.

        Args:
            future: Future con el resultado final de la acción.
        """
        self._goal_handle = None
        try:
            future.result()
            self.get_logger().info('¡Llegamos al destino!')
        except Exception as e:
            self.get_logger().error(f'La navegación terminó con error: {e}')

    def feedback_callback(self, feedback_msg):
        """
        Callback de feedback periódico durante la navegación.

        Args:
            feedback_msg: Mensaje de feedback con la distancia restante al goal.
        """
        feedback = feedback_msg.feedback
        self.get_logger().info(f'Distancia restante: {feedback.distance_remaining:.2f} m')


def main(args=None):
    """Punto de entrada principal: inicializa ROS 2 y mantiene el nodo activo."""
    rclpy.init(args=args)
    node = NavService()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Nodo interrumpido por el usuario.')
    except Exception as e:
        node.get_logger().error(f'Error inesperado en el nodo: {e}')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()