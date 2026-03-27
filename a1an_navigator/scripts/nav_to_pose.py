#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.time import Time
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
import sys

class NavigateToPoseClient(Node):

    def __init__(self):
        super().__init__('nav_to_pose_client')
        self._action_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')

    def send_goal(self, x, y, theta):
        goal_msg = NavigateToPose.Goal()

        goal_pose = PoseStamped()
        goal_pose.header.frame_id = 'map'
        goal_pose.header.stamp = self.get_clock().now().to_msg()
        goal_pose.pose.position.x = x
        goal_pose.pose.position.y = y
        goal_pose.pose.orientation.w = 1.0 # Simple facing forward
        goal_pose.pose.orientation.z = theta

        goal_msg.pose = goal_pose

        self.get_logger().info('Esperando al servidor de accion NavigateToPose...')
        self._action_client.wait_for_server()

        self.get_logger().info('Enviando objetivo de navegacion...')
        self._send_goal_future = self._action_client.send_goal_async(goal_msg, feedback_callback=self.feedback_callback)
        self._send_goal_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().info('Objetivo rechazado :(')
            return

        self.get_logger().info('Objetivo aceptado, calculando e iniciando ruta...')

        self._get_result_future = goal_handle.get_result_async()
        self._get_result_future.add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):
        result = future.result().result
        self.get_logger().info('Mision completada. ¡Llegamos a la meta!')
        rclpy.shutdown()

    def feedback_callback(self, feedback_msg):
        feedback = feedback_msg.feedback
        self.get_logger().info(f'Distancia restante: {feedback.distance_remaining:.2f} m')

def main(args=None):
    rclpy.init(args=args)

    if len(sys.argv) < 3:
        print("Uso: ros2 run a1an_navigator nav_to_pose.py <x> <y>")
        return

    action_client = NavigateToPoseClient()
    x = float(sys.argv[1])
    y = float(sys.argv[2])
    action_client.send_goal(x, y, 0.0)

    rclpy.spin(action_client)

if __name__ == '__main__':
    main()
