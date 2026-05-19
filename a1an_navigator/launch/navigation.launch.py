<<<<<<< Updated upstream
=======
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

>>>>>>> Stashed changes
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
<<<<<<< Updated upstream
    # Ruta al archivo de parametros de burger.yaml (que tiene config de Nav2)
    nav2_yaml = os.path.join(get_package_share_directory('a1an_localization'), 'param', 'burger.yaml')
    
    # Ruta al archivo navigation_launch.py de nav2_bringup (lanza bt_navigator, planner, controller, recoveries...)
=======
    """
    Genera el LaunchDescription que incluye el launch de navegación de Nav2.

    Configura ``params_file``, ``use_sim_time`` y ``autostart`` para adaptar
    Nav2 a la configuración del robot A1AN en simulación.

    Returns:
        LaunchDescription: Descripción de lanzamiento con Nav2 completo.
    """
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')

    # Ruta al archivo de parámetros de Nav2 para el burger
    nav2_yaml = os.path.join(
        get_package_share_directory('a1an_localization'), 'param', 'burger.yaml'
    )

    # Incluye el launch principal de Nav2 (bt_navigator, planner, controller...)
>>>>>>> Stashed changes
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')
    navigation_launch_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_bringup_dir, 'launch', 'navigation_launch.py')
        ),
<<<<<<< Updated upstream
        launch_arguments={'params_file': nav2_yaml,
                          'use_sim_time': 'true',
                          'autostart': 'true'}.items()
=======
        launch_arguments={
            'params_file': nav2_yaml,
            'use_sim_time': use_sim_time,
            'autostart': 'true'
        }.items()
>>>>>>> Stashed changes
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Usar reloj de simulación (true) o reloj real (false)'),
        navigation_launch_cmd
    ])
