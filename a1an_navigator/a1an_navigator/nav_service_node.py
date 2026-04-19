#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
from std_msgs.msg import Float64MultiArray, Bool


class NavService(Node):
    def __init__(self):
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

        # Suscriptor al topic /nav_cancel — recibe true para cancelar
        self.create_subscription(
            Bool,
            '/nav_cancel',
            self.cancel_callback,
            10
        )

        self.get_logger().info('NavService node listo. Escuchando en /nav_goal y /nav_cancel')

    def nav_goal_callback(self, msg):
        if len(msg.data) < 2:
            self.get_logger().error('Mensaje inválido, se esperan 2 valores [x, y]')
            return

        x = msg.data[0]
        y = msg.data[1]
        self.get_logger().info(f'Goal recibido: x={x}, y={y}')
        self.send_goal(x, y)

    def cancel_callback(self, msg):
        if msg.data and self._goal_handle:
            self.get_logger().info('Cancelando navegación...')
            self._goal_handle.cancel_goal_async()
        else:
            self.get_logger().info('No hay goal activo para cancelar')

    def send_goal(self, x, y):
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

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().info('Goal rechazado')
            return
        self._goal_handle = goal_handle
        self.get_logger().info('Goal aceptado, navegando...')
        goal_handle.get_result_async().add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):
        self._goal_handle = None
        self.get_logger().info('¡Llegamos al destino!')

    def feedback_callback(self, feedback_msg):
        feedback = feedback_msg.feedback
        self.get_logger().info(f'Distancia restante: {feedback.distance_remaining:.2f} m')


def main(args=None):
    rclpy.init(args=args)
    node = NavService()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == '__main__':
    main()