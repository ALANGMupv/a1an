"""
a1an_world.launch.py
=====================
Launch file que levanta el entorno de simulación completo del robot A1AN en Gazebo.

Pasos que ejecuta:
1. Configura la variable de entorno ``TURTLEBOT3_MODEL`` a ``burger_cam``.
2. Añade las rutas de modelos y mundos a ``GZ_SIM_RESOURCE_PATH``.
3. Lanza Gazebo con el mundo ``small_house_fixed.world``.
4. Lanza el nodo ``robot_state_publisher`` del paquete turtlebot3_gazebo.
5. Hace spawn del TurtleBot3 en la posición inicial (-2.0, -1.0).

Uso:
    ros2 launch a1an_world a1an_world.launch.py
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import AppendEnvironmentVariable, IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    """
    Genera el LaunchDescription con el entorno de simulación completo.

    Resuelve rutas de paquetes, configura variables de entorno para Gazebo
    y combina los launches de simulación, robot state publisher y spawn.

    Returns:
        LaunchDescription: Descripción de lanzamiento con todos los componentes.
    """
    # --- Rutas de paquetes ---
    a1an_pkg = get_package_share_directory('a1an_world')
    tb3_pkg = get_package_share_directory('turtlebot3_gazebo')
    ros_gz_sim = get_package_share_directory('ros_gz_sim')

    launch_file_dir = os.path.join(tb3_pkg, 'launch')

    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    x_pose = LaunchConfiguration('x_pose', default='-2.0')
    y_pose = LaunchConfiguration('y_pose', default='-1.0')

    # Mundo personalizado del proyecto
    world = os.path.join(a1an_pkg, 'worlds', 'small_house_fixed.world')

    # --- Variables de entorno ---
    set_tb3_model = SetEnvironmentVariable(
        name='TURTLEBOT3_MODEL',
        value='burger_cam'
    )

    # Añade los directorios de modelos y mundos al path de recursos de Gazebo
    set_env_vars_resources = AppendEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=':'.join([
            os.path.join(a1an_pkg, 'models'),   # Modelos del proyecto
            os.path.join(a1an_pkg, 'worlds'),   # Mundo del proyecto
            os.path.join(a1an_pkg, 'urdf'),
            os.path.join(tb3_pkg, 'models')     # Modelos del TurtleBot3
        ])
    )

    # --- Lanzamiento de Gazebo con el mundo personalizado ---
    gz_sim_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={'gz_args': f'-r -v 2 {world}'}.items()
    )

    # --- Robot State Publisher (TF y descripción URDF) ---
    robot_state_publisher_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(launch_file_dir, 'robot_state_publisher.launch.py')
        ),
        launch_arguments={'use_sim_time': use_sim_time}.items()
    )

    # --- Spawn del TurtleBot3 en la posición inicial ---
    spawn_turtlebot_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(launch_file_dir, 'spawn_turtlebot3.launch.py')
        ),
        launch_arguments={
            'x_pose': '-2.0',
            'y_pose': '-1.0'
        }.items()
    )

    # --- Construcción del LaunchDescription en orden de dependencia ---
    ld = LaunchDescription()

    ld.add_action(set_tb3_model)
    ld.add_action(set_env_vars_resources)
    ld.add_action(gz_sim_cmd)
    ld.add_action(robot_state_publisher_cmd)
    ld.add_action(spawn_turtlebot_cmd)

    return ld