import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    # Ruta al archivo de parametros de burger.yaml (que tiene config de Nav2)
    nav2_yaml = os.path.join(get_package_share_directory('a1an_localization'), 'param', 'burger.yaml')
    
    # Ruta al archivo navigation_launch.py de nav2_bringup (lanza bt_navigator, planner, controller, recoveries...)
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')
    navigation_launch_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_bringup_dir, 'launch', 'navigation_launch.py')
        ),
        launch_arguments={'params_file': nav2_yaml,
                          'use_sim_time': 'true',
                          'autostart': 'true'}.items()
    )

    return LaunchDescription([
        navigation_launch_cmd
    ])
