import launch
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='franka_api_server',
            executable='api_server',
            name='franka_api_server',
            output='screen',
            emulate_tty=True
        )
    ])
