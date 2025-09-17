import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, Command
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():

    pkg_bme_ros2_simple_arm = get_package_share_directory('bme_ros2_simple_arm')

    gazebo_models_path, ignore_last_dir = os.path.split(pkg_bme_ros2_simple_arm)
    os.environ["GZ_SIM_RESOURCE_PATH"] += os.pathsep + gazebo_models_path

    repo_path_arg = DeclareLaunchArgument(
        "repo_path",
        default_value="/root/hand_controller",
        description="Path (absolute) to hand_controller repo."
    )
    blaze_target_arg = DeclareLaunchArgument(
        "blaze_target",
        default_value="blaze_tflite",
        description="blaze target implementation."
    )       
    blaze_model1_arg = DeclareLaunchArgument(
        "blaze_model1",
        default_value="palm_detection_lite.tflite",
        description="Name of blaze detection model."
    )       
    blaze_model2_arg = DeclareLaunchArgument(
        "blaze_model2",
        default_value="hand_landmark_lite.tflite",
        description="Name of blaze landmark model."
    )
    
    rviz_launch_arg = DeclareLaunchArgument(
        'rviz', default_value='true',
        description='Open RViz'
    )

    rviz_config_arg = DeclareLaunchArgument(
        'rviz_config', default_value='rviz.rviz',
        description='RViz config file'
    )

    world_arg = DeclareLaunchArgument(
        'world', default_value='world.sdf',
        description='Name of the Gazebo world file to load'
    )

    model_arg = DeclareLaunchArgument(
        'model', default_value='mogi_arm.xacro',
        description='Name of the URDF description to load'
    )

    x_arg = DeclareLaunchArgument(
        'x', default_value='0.0',
        description='x coordinate of spawned robot'
    )

    y_arg = DeclareLaunchArgument(
        'y', default_value='0.0',
        description='y coordinate of spawned robot'
    )

    z_arg = DeclareLaunchArgument(
        'z', default_value='1.04',
        description='z coordinate of spawned robot'
    )

    yaw_arg = DeclareLaunchArgument(
        'yaw', default_value='0.0',
        description='yaw angle of spawned robot'
    )

    sim_time_arg = DeclareLaunchArgument(
        'use_sim_time', default_value='True',
        description='Flag to enable use_sim_time'
    )

    # Define the path to your URDF or Xacro file
    urdf_file_path = PathJoinSubstitution([
        pkg_bme_ros2_simple_arm,  # Replace with your package name
        "urdf",
        LaunchConfiguration('model')  # Replace with your URDF or Xacro file
    ])

    gz_bridge_params_path = os.path.join(
        get_package_share_directory('bme_ros2_simple_arm'),
        'config',
        'gz_bridge.yaml'
    )

    robot_controllers = PathJoinSubstitution(
        [
            get_package_share_directory('bme_ros2_simple_arm'),
            'config',
            'controller_position.yaml',
        ]
    )

    world_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_bme_ros2_simple_arm, 'launch', 'world.launch.py'),
        ),
        launch_arguments={
        'world': LaunchConfiguration('world'),
        }.items()
    )

    # Launch ASL controller
    usbcam_publisher_node = Node(
        package='v4l2_camera',
        executable='v4l2_camera_node',
        name="usbcam_publisher",
        remappings=[("image_raw", "usbcam_image")]            
    )
    hand_controller_node = Node(
        package='hand_controller',
        executable='hand_controller_asl_joints_node',
        name="hand_controller",
        parameters=[
               {"repo_path":LaunchConfiguration("repo_path")},
               {"blaze_target":LaunchConfiguration("blaze_target")},
               {"blaze_model1":LaunchConfiguration("blaze_model1")},
               {"blaze_model2":LaunchConfiguration("blaze_model2")},
               {"verbose":True},
               {"use_imshow":True}
        ],
        remappings=[
           ("image_raw", "usbcam_image"),
           ("/arm_controller/joint_trajectory", "/arm_controller/joint_trajectory")
        ]
    )

    # Launch rviz
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', PathJoinSubstitution([pkg_bme_ros2_simple_arm, 'rviz', LaunchConfiguration('rviz_config')])],
        condition=IfCondition(LaunchConfiguration('rviz')),
        parameters=[
            {'use_sim_time': LaunchConfiguration('use_sim_time')},
        ]
    )

    # Spawn the URDF model using the `/world/<world_name>/create` service
    spawn_urdf_node = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-name", "mogi_arm",
            "-topic", "robot_description",
            "-x", LaunchConfiguration('x'), "-y", LaunchConfiguration('y'), "-z", LaunchConfiguration('z'), "-Y", LaunchConfiguration('yaw')  # Initial spawn position
        ],
        output="screen",
        parameters=[
            {'use_sim_time': LaunchConfiguration('use_sim_time')},
        ]
    )

    # Node to bridge /cmd_vel and /odom
    gz_bridge_node = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            '--ros-args', '-p',
            f'config_file:={gz_bridge_params_path}'
        ],
        output="screen",
        parameters=[
            {'use_sim_time': LaunchConfiguration('use_sim_time')},
        ]
    )

    # Node to bridge camera topics
    gz_image_bridge_node = Node(
        package="ros_gz_image",
        executable="image_bridge",
        arguments=[
            "/gripper_camera/image",
            "/table_camera/image",
        ],
        output="screen",
        parameters=[
            {'use_sim_time': LaunchConfiguration('use_sim_time'),
             'gripper_camera.image.compressed.jpeg_quality': 75,
             'table_camera.image.compressed.jpeg_quality': 75,},
        ],
    )

    # Relay node to republish camera_info to image/camera_info
    relay_gripper_camera_info_node = Node(
        package='topic_tools',
        executable='relay',
        name='relay_camera_info',
        output='screen',
        arguments=['gripper_camera/camera_info', 'gripper_camera/image/camera_info'],
        parameters=[
            {'use_sim_time': LaunchConfiguration('use_sim_time')},
        ]
    )

    # Relay node to republish camera_info to image/camera_info
    relay_table_camera_info_node = Node(
        package='topic_tools',
        executable='relay',
        name='relay_camera_info',
        output='screen',
        arguments=['table_camera/camera_info', 'table_camera/image/camera_info'],
        parameters=[
            {'use_sim_time': LaunchConfiguration('use_sim_time')},
        ]
    )

    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[
            {'robot_description': Command(['xacro', ' ', urdf_file_path]),
             'use_sim_time': LaunchConfiguration('use_sim_time')},
        ],
        remappings=[
            ('/tf', 'tf'),
            ('/tf_static', 'tf_static')
        ]
    )
    joint_state_publisher_gui_node = Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
    )

    joint_state_broadcaster_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster'],
        parameters=[
            {'use_sim_time': LaunchConfiguration('use_sim_time')},
        ]
    )

    joint_trajectory_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'arm_controller',
            'gripper_controller',
            '--param-file',
            robot_controllers,
            ],
        parameters=[
            {'use_sim_time': LaunchConfiguration('use_sim_time')},
        ]
    )

    launchDescriptionObject = LaunchDescription()

    launchDescriptionObject.add_action(repo_path_arg)
    launchDescriptionObject.add_action(blaze_target_arg)
    launchDescriptionObject.add_action(blaze_model1_arg)
    launchDescriptionObject.add_action(blaze_model2_arg)
    launchDescriptionObject.add_action(rviz_launch_arg)
    launchDescriptionObject.add_action(rviz_config_arg)
    launchDescriptionObject.add_action(world_arg)
    launchDescriptionObject.add_action(model_arg)
    launchDescriptionObject.add_action(x_arg)
    launchDescriptionObject.add_action(y_arg)
    launchDescriptionObject.add_action(z_arg)
    launchDescriptionObject.add_action(yaw_arg)
    launchDescriptionObject.add_action(sim_time_arg)
    launchDescriptionObject.add_action(world_launch)
    launchDescriptionObject.add_action(usbcam_publisher_node)
    launchDescriptionObject.add_action(hand_controller_node)    
    launchDescriptionObject.add_action(rviz_node)
    launchDescriptionObject.add_action(spawn_urdf_node)
    launchDescriptionObject.add_action(gz_bridge_node)
    launchDescriptionObject.add_action(gz_image_bridge_node)
    launchDescriptionObject.add_action(relay_gripper_camera_info_node)
    launchDescriptionObject.add_action(relay_table_camera_info_node)
    launchDescriptionObject.add_action(robot_state_publisher_node)
    #launchDescriptionObject.add_action(joint_state_publisher_gui_node)
    launchDescriptionObject.add_action(joint_state_broadcaster_spawner)
    launchDescriptionObject.add_action(joint_trajectory_controller_spawner)

    return launchDescriptionObject
