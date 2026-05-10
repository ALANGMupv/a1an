from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='a1an_vision',
            executable='assistive_object_detector',
            name='assistive_object_detector',
            output='screen',
            parameters=[{
                'image_topic': '/camera/image_raw',
                'show_window': False,
                'min_area': 250,
                'process_every_n_frames': 2,
            }],
        )
    ])
