import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import AppendEnvironmentVariable
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_launch_description():
    pkg_share = get_package_share_directory('a1an_world')
    ros_gz_sim = get_package_share_directory('ros_gz_sim')

    world = os.path.join(
        pkg_share,
        'worlds',
        'small_house_fixed.world'
    )

    set_env_vars_resources = AppendEnvironmentVariable(
        'GZ_SIM_RESOURCE_PATH',
        os.path.join(pkg_share, 'models')
    )

    gz_sim_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={
            'gz_args': ['-r -v 2 ', world],
            'on_exit_shutdown': 'true'
        }.items()
    )

    ld = LaunchDescription()
    ld.add_action(set_env_vars_resources)
    ld.add_action(gz_sim_cmd)

    return ld