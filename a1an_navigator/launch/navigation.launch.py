"""
navigation.launch.py
=====================
Launch file que arranca el stack completo de navegación de Nav2 para el A1AN.

Incluye ``navigation_launch.py`` de ``nav2_bringup``, que levanta:
bt_navigator, planner_server, controller_server y los nodos de recuperación.

Los parámetros se leen de ``param/burger.yaml`` del paquete ``a1an_localization``.

Uso:
    ros2 launch a1an_navigator navigation.launch.py
    ros2 launch a1an_navigator navigation.launch.py use_sim_time:=false
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    """
    Genera el LaunchDescription que incluye el launch de navegación de Nav2.

    Configura ``params_file``, ``use_sim_time`` y ``autostart``. Por defecto
    arranca en modo simulación (use_sim_time=true); para robot real pasar
    ``use_sim_time:=false`` desde fuera.

    Returns:
        LaunchDescription: Descripción de lanzamiento con Nav2 completo.
    """
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')

    # Ruta al archivo de parámetros de Nav2 para el burger
    nav2_yaml = os.path.join(
        get_package_share_directory('a1an_localization'), 'param', 'burger.yaml'
    )

    # Incluye el launch principal de Nav2 (bt_navigator, planner, controller...)
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')
    navigation_launch_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_bringup_dir, 'launch', 'navigation_launch.py')
        ),
        launch_arguments={
            'params_file': nav2_yaml,
            'use_sim_time': use_sim_time,
            'autostart': 'true'
        }.items()
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Usar reloj de simulación (true) o reloj real (false)'),
        navigation_launch_cmd
    ])
