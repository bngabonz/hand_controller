from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'hand_controller'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # Include all launch files.
        (os.path.join('share', package_name, 'launch'), glob(os.path.join('launch', '*launch.[pxy][yma]*'))),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='AlbertaBeef',
    maintainer_email='grouby177@gmail.com',
    description='Hand Controller using mediapipe models and ASL.',
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'usbcam_publisher_node = hand_controller.usbcam_publisher_node:main',        
            'usbcam_subscriber_node = hand_controller.usbcam_subscriber_node:main',          
            'hand_controller_asl_twist_node = hand_controller.hand_controller_asl_twist_node:main', 
            'hand_controller_asl_joints_node = hand_controller.hand_controller_asl_joints_node:main', 
            'hand_controller_asl_pose_node = hand_controller.hand_controller_asl_pose_node:main', 
            'hand_controller_mp1dials_twist_node = hand_controller.hand_controller_mp1dials_twist_node:main', 
            'hand_controller_mp1dials_joints_node = hand_controller.hand_controller_mp1dials_joints_node:main', 
            'hand_controller_mp1dials_pose_node = hand_controller.hand_controller_mp1dials_pose_node:main', 
        ],
    },
)
