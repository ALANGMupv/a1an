import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    model_path = os.path.join(
        get_package_share_directory('a1an_vision'),
        'model', 'best.pt',
    )

    return LaunchDescription([
        Node(
            package='a1an_vision',
            executable='assistive_object_detector',
            name='assistive_object_detector',
            output='screen',
            parameters=[{
                'image_topic':            '/camera/image_raw',
                'show_window':            False,
                'confidence_threshold':   0.50,
                'process_every_n_frames': 2,
                'model_path':             model_path,
            }],
        )
    ])
