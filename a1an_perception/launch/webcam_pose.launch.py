from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    camera_index = LaunchConfiguration('camera_index')
    mirror_image = LaunchConfiguration('mirror_image')
    model_complexity = LaunchConfiguration('model_complexity')
    frame_width = LaunchConfiguration('frame_width')
    frame_height = LaunchConfiguration('frame_height')
    camera_fps = LaunchConfiguration('camera_fps')
    camera_fourcc = LaunchConfiguration('camera_fourcc')
    target_repetitions = LaunchConfiguration('target_repetitions')

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
        DeclareLaunchArgument(
            'frame_width',
            default_value='640',
            description='Requested webcam frame width.',
        ),
        DeclareLaunchArgument(
            'frame_height',
            default_value='480',
            description='Requested webcam frame height.',
        ),
        DeclareLaunchArgument(
            'camera_fps',
            default_value='15',
            description='Requested webcam frames per second.',
        ),
        DeclareLaunchArgument(
            'camera_fourcc',
            default_value='MJPG',
            description='Requested OpenCV webcam FOURCC format, for example MJPG or YUYV.',
        ),
        DeclareLaunchArgument(
            'target_repetitions',
            default_value='10',
            description='Target repetitions for the rehabilitation exercise.',
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
                'frame_width': frame_width,
                'frame_height': frame_height,
                'camera_fps': camera_fps,
                'camera_fourcc': camera_fourcc,
                'target_repetitions': target_repetitions,
            }],
        ),
    ])
