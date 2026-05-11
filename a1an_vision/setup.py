import os
from glob import glob

from setuptools import find_packages, setup


package_name = 'a1an_vision'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Grupo02',
    maintainer_email='user@todo.todo',
    description='Procesado de imagenes para detectar objetos domesticos de asistencia en A1AN.',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'camera_viewer = a1an_vision.camera_viewer:main',
            'assistive_object_detector = a1an_vision.assistive_object_detector:main',
        ],
    },
)
