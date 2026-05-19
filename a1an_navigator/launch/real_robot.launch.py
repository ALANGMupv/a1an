import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    # ── Argumentos de lanzamiento ───────────────────────────────────────────
    use_rviz = LaunchConfiguration('use_rviz', default='true')
    map_arg = LaunchConfiguration('map', default='')
    slam_arg = LaunchConfiguration('slam', default='false')

    # ── Rutas de paquetes ───────────────────────────────────────────────────
    localization_pkg = get_package_share_directory('a1an_localization')
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')

    nav2_yaml = os.path.join(localization_pkg, 'param', 'burger.yaml')
    default_map = os.path.join(localization_pkg, 'map', 'my_map.yaml')
    rviz_config = os.path.join(localization_pkg, 'rviz', 'tb3_navigation2.rviz')

    # ── Archivo de mapa: usa el argumento 'map' si se da, o el mapa por defecto ──
    map_file = LaunchConfiguration('map', default=default_map)

    # ── LaunchDescription ───────────────────────────────────────────────────
    ld = LaunchDescription()

    ld.add_action(DeclareLaunchArgument(
        'use_rviz', default_value='true',
        description='Lanzar RViz2 para visualización (true/false)'))

    ld.add_action(DeclareLaunchArgument(
        'map', default_value=default_map,
        description='Ruta completa al archivo .yaml del mapa'))
        
    ld.add_action(DeclareLaunchArgument(
        'slam', default_value='false',
        description='Lanzar SLAM para mapear (true) o solo navegación (false)'))

    # ════════════════════════════════════════════════════════════════════════
    # 1. MAP SERVER — carga el mapa (SOLO si slam=false)
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
        condition=UnlessCondition(slam_arg)
    )
    ld.add_action(map_server_node)

    # ════════════════════════════════════════════════════════════════════════
    # 2. AMCL — localización probabilística (SOLO si slam=false)
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
        condition=UnlessCondition(slam_arg)
    )
    ld.add_action(amcl_node)

    # ════════════════════════════════════════════════════════════════════════
    # 3. LIFECYCLE MANAGER — para map_server y amcl (SOLO si slam=false)
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
        condition=UnlessCondition(slam_arg)
    )
    ld.add_action(lifecycle_manager_localization)

    # ════════════════════════════════════════════════════════════════════════
    # 3.5. SLAM TOOLBOX — para mapear y localizar a la vez (SOLO si slam=true)
    # ════════════════════════════════════════════════════════════════════════
    slam_toolbox_node = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[
            {'use_sim_time': False},
            {'odom_frame': 'odom'},
            {'map_frame': 'map'},
            {'base_frame': 'base_footprint'},
            {'scan_topic': '/scan'},
            {'mode': 'mapping'}
        ],
        condition=IfCondition(slam_arg)
    )
    ld.add_action(slam_toolbox_node)

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
    # 5. NAV SERVICE NODE — servicio de navegación para la web
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
    # 7. VISION — detección de objetos asistivos con la cámara
    # ════════════════════════════════════════════════════════════════════════
    vision_node = Node(
        package='a1an_vision',
        executable='assistive_object_detector',
        name='assistive_object_detector',
        output='screen',
        parameters=[{
            'use_sim_time': False,
            'image_topic': '/camera/image_raw',
            'show_window': False,
            'min_area': 120,
            'process_every_n_frames': 2,
        }]
    )
    ld.add_action(vision_node)

    # ════════════════════════════════════════════════════════════════════════
    # 8. WEB VIDEO SERVER — streaming de la cámara por HTTP
    # ════════════════════════════════════════════════════════════════════════
    web_video_server_node = Node(
        package='web_video_server',
        executable='web_video_server',
        name='web_video_server',
        output='screen',
        parameters=[{
            'use_sim_time': False,
            'port': 8081,
        }]
    )
    ld.add_action(web_video_server_node)

    # ════════════════════════════════════════════════════════════════════════
    # 9. RVIZ2 — visualización (opcional)
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
