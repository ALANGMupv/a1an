import os
from glob import glob

from setuptools import setup

package_name = 'a1an_perception'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Alan Guevara Martinez',
    maintainer_email='alanguevara36@gmail.com',
    description='Vision and human pose perception for A1AN rehabilitation assistance.',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'webcam_pose_node = a1an_perception.webcam_pose_node:main',
        ],
    },
)
