"""
real_robot.launch.py
=====================
Launch del stack de navegación del A1AN para el ROBOT REAL.

Lanza:
- map_server  + amcl + lifecycle_manager (localización con mapa estático)
- Nav2 completo (planner, controller, bt_navigator, recoveries)
- nav_service_node (puente web → /navigate_to_pose)
- ROSBridge (WebSocket para la web)
- RViz2 (opcional, use_rviz:=false para desactivar)

NO incluye cámara ni visión. El bringup del robot debe estar lanzado en la
Raspberry Pi por SSH antes (ros2 launch turtlebot3_bringup robot.launch.py).

Uso:
    ros2 launch a1an_navigator real_robot.launch.py
    ros2 launch a1an_navigator real_robot.launch.py map:=/ruta/al/otro_mapa.yaml
    ros2 launch a1an_navigator real_robot.launch.py use_rviz:=false
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    # ── Rutas de paquetes ───────────────────────────────────────────────────
    localization_pkg = get_package_share_directory('a1an_localization')
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')

    nav2_yaml = os.path.join(localization_pkg, 'param', 'burger.yaml')
    default_map = os.path.join(localization_pkg, 'map', 'my_map_real.yaml')
    rviz_config = os.path.join(localization_pkg, 'rviz', 'tb3_navigation2.rviz')

    # ── Argumentos de lanzamiento ───────────────────────────────────────────
    use_rviz = LaunchConfiguration('use_rviz', default='true')
    map_file = LaunchConfiguration('map', default=default_map)

    # ── LaunchDescription ───────────────────────────────────────────────────
    ld = LaunchDescription()

    ld.add_action(DeclareLaunchArgument(
        'use_rviz', default_value='true',
        description='Lanzar RViz2 para visualización (true/false)'))

    ld.add_action(DeclareLaunchArgument(
        'map', default_value=default_map,
        description='Ruta completa al archivo .yaml del mapa'))

    # ════════════════════════════════════════════════════════════════════════
    # 1. MAP SERVER — carga el mapa estático del entorno real
    # ════════════════════════════════════════════════════════════════════════
    map_server_node = Node(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        output='screen',
        parameters=[
            nav2_yaml,
            {
                'use_sim_time': False,
                'yaml_filename': map_file,
            }
        ],
    )
    ld.add_action(map_server_node)

    # ════════════════════════════════════════════════════════════════════════
    # 2. AMCL — localización probabilística (Monte Carlo)
    # ════════════════════════════════════════════════════════════════════════
    amcl_node = Node(
        package='nav2_amcl',
        executable='amcl',
        name='amcl',
        output='screen',
        parameters=[
            nav2_yaml,
            {'use_sim_time': False}
        ],
    )
    ld.add_action(amcl_node)

    # ════════════════════════════════════════════════════════════════════════
    # 3. LIFECYCLE MANAGER — gestiona map_server y amcl
    # ════════════════════════════════════════════════════════════════════════
    lifecycle_manager_localization = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_localization',
        output='screen',
        parameters=[
            {'use_sim_time': False},
            {'autostart': True},
            {'node_names': ['map_server', 'amcl']}
        ],
    )
    ld.add_action(lifecycle_manager_localization)

    # ════════════════════════════════════════════════════════════════════════
    # 4. NAV2 NAVIGATION — stack completo (planner, controller, bt_navigator…)
    # ════════════════════════════════════════════════════════════════════════
    navigation_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_bringup_dir, 'launch', 'navigation_launch.py')
        ),
        launch_arguments={
            'params_file': nav2_yaml,
            'use_sim_time': 'false',
            'autostart': 'true'
        }.items()
    )
    ld.add_action(navigation_cmd)

    # ════════════════════════════════════════════════════════════════════════
    # 5. NAV SERVICE NODE — puente web → /navigate_to_pose
    # ════════════════════════════════════════════════════════════════════════
    nav_service_node = Node(
        package='a1an_navigator',
        executable='nav_service_node',
        name='nav_service_node',
        output='screen',
        parameters=[{'use_sim_time': False}]
    )
    ld.add_action(nav_service_node)

    # ════════════════════════════════════════════════════════════════════════
    # 6. ROSBRIDGE — WebSocket para la interfaz web
    # ════════════════════════════════════════════════════════════════════════
    rosbridge_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('rosbridge_server'),
                'launch', 'rosbridge_websocket_launch.xml'
            )
        ),
        launch_arguments={
            'delay_between_messages': '0.0',
        }.items()
    )
    ld.add_action(rosbridge_cmd)

    # ════════════════════════════════════════════════════════════════════════
    # 7. RVIZ2 — visualización (opcional)
    # ════════════════════════════════════════════════════════════════════════
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': False}],
        output='screen',
        condition=IfCondition(use_rviz)
    )
    ld.add_action(rviz_node)

    return ld
