from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    camera_index = LaunchConfiguration('camera_index')
    mirror_image = LaunchConfiguration('mirror_image')
    model_complexity = LaunchConfiguration('model_complexity')

    return LaunchDescription([
        DeclareLaunchArgument(
            'camera_index',
            default_value='0',
            description='OpenCV camera index. Usually 0 for the laptop webcam.',
        ),
        DeclareLaunchArgument(
            'mirror_image',
            default_value='true',
            description='Mirror the image so the webcam preview behaves like a mirror.',
        ),
        DeclareLaunchArgument(
            'model_complexity',
            default_value='1',
            description='MediaPipe Pose model complexity: 0, 1, or 2.',
        ),
        Node(
            package='a1an_perception',
            executable='webcam_pose_node',
            name='webcam_pose_node',
            output='screen',
            parameters=[{
                'camera_index': camera_index,
                'mirror_image': mirror_image,
                'model_complexity': model_complexity,
            }],
        ),
    ])
