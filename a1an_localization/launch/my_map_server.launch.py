"""
my_map_server.launch.py
========================
Launch file que levanta el stack de localización estática para el robot A1AN.

Nodos lanzados:
- ``map_server``              — Carga y publica el mapa (.yaml/.pgm) para Nav2.
- ``amcl``                    — Localización probabilística (Monte Carlo).
- ``lifecycle_manager``       — Gestiona el ciclo de vida de map_server y amcl.
- ``rviz2``                   — Visualización con la configuración del paquete.

Todos los nodos usan los parámetros definidos en ``param/burger.yaml``.

Uso:
    ros2 launch a1an_localization my_map_server.launch.py
    ros2 launch a1an_localization my_map_server.launch.py use_sim_time:=false
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    """
    Genera el LaunchDescription con todos los nodos del stack de localización.

    Por defecto arranca en modo simulación (use_sim_time=true); para robot real
    pasar ``use_sim_time:=false`` desde fuera.

    Returns:
        LaunchDescription: Descripción de lanzamiento con los cuatro nodos.
    """
    pkg_share = get_package_share_directory('a1an_localization')

    nav2_yaml = os.path.join(pkg_share, 'param', 'burger.yaml')
    map_file = os.path.join(pkg_share, 'map', 'my_map.yaml')
    rviz_config_dir = os.path.join(pkg_share, 'rviz', 'tb3_navigation2.rviz')

    use_sim_time = LaunchConfiguration('use_sim_time', default='true')

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Usar reloj de simulación (true) o reloj real (false)'),
        # Servidor de mapas: carga el mapa estático para Nav2
        Node(
            package='nav2_map_server',
            executable='map_server',
            name='map_server',
            output='screen',
            parameters=[nav2_yaml, {'yaml_filename': map_file, 'use_sim_time': use_sim_time}]
        ),
        Node(
            package='nav2_amcl',
            executable='amcl',
            name='amcl',
            output='screen',
            parameters=[nav2_yaml, {'use_sim_time': use_sim_time}]
        ),
        Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_localization',
            output='screen',
            parameters=[
                {'use_sim_time': use_sim_time},
                {'autostart': True},
                {'node_names': ['map_server', 'amcl']}
            ]
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', rviz_config_dir],
            parameters=[{'use_sim_time': use_sim_time}],
            output='screen'
        )
    ])
