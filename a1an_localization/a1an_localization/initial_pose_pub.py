"""
initial_pose_pub.py
====================
Nodo ROS 2 que publica periódicamente la pose inicial del robot en el topic
``/initialpose`` usando el tipo de mensaje ``PoseWithCovarianceStamped``.

Su función principal es informar al stack de localización (AMCL) dónde
se encuentra el robot al arrancar, evitando que AMCL comience sin referencia.

Uso:
    ros2 run a1an_localization initial_pose_pub
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseWithCovarianceStamped


class InitialPosePub(Node):
    """
    Nodo publicador de la pose inicial del robot.

    Publica un mensaje ``PoseWithCovarianceStamped`` en ``/initialpose``
    una vez por segundo con la posición (0, 0) y orientación neutra.
    """

    def __init__(self):
        """Inicializa el nodo, el publicador y el temporizador periódico."""
        super().__init__('initial_pose_pub_node')
        self.publisher_ = self.create_publisher(PoseWithCovarianceStamped, '/initialpose', 10)
        timer_period = 1.0  # segundos
        self.timer = self.create_timer(timer_period, self.timer_callback)
        self.get_logger().info('Initial Pose Publisher Node Started.')

    def timer_callback(self):
        """
        Construye y publica la pose inicial en cada tick del temporizador.

        La posición se fija en el origen del mapa (x=0, y=0) con orientación
        neutra (quaternion w=1). Los valores de covarianza corresponden a los
        defaults recomendados por Nav2 para AMCL.
        """
        try:
            msg = PoseWithCovarianceStamped()

            msg.header.frame_id = 'map'
            msg.header.stamp = self.get_clock().now().to_msg()

            msg.pose.pose.position.x = 0.0
            msg.pose.pose.position.y = 0.0
            msg.pose.pose.position.z = 0.0

            msg.pose.pose.orientation.x = 0.0
            msg.pose.pose.orientation.y = 0.0
            msg.pose.pose.orientation.z = 0.0
            msg.pose.pose.orientation.w = 1.0

            # Covarianza diagonal: posición xy y yaw (valores estándar AMCL)
            msg.pose.covariance[0] = 0.25
            msg.pose.covariance[7] = 0.25
            msg.pose.covariance[35] = 0.06853892326654787

            self.publisher_.publish(msg)
            self.get_logger().info('Publishing Initial Pose')

        except Exception as e:
            self.get_logger().error(f'Error al publicar la pose inicial: {e}')


def main(args=None):
    """Punto de entrada principal: inicializa ROS 2 y mantiene el nodo activo."""
    rclpy.init(args=args)
    node = InitialPosePub()

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
