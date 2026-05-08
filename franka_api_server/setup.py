import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'franka_api_server'

# Gather all static files
static_files = []
for root, dirs, files in os.walk('static'):
    for file in files:
        file_path = os.path.join(root, file)
        static_files.append((os.path.join('share', package_name, root), [file_path]))

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob(os.path.join('launch', '*launch.[pxy][yma]*'))),
        (os.path.join('share', package_name, 'config'), glob(os.path.join('config', '*.yaml'))),
    ] + static_files,
    install_requires=['setuptools', 'fastapi', 'uvicorn', 'pydantic'],
    zip_safe=True,
    maintainer='root',
    maintainer_email='13403433315@139.com',
    description='REST API and Web UI server for Franka ROS2',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
            'pytest-playwright',
            'httpx',
            'pytest-asyncio',
        ],
    },
    entry_points={
        'console_scripts': [
            'api_server = franka_api_server.main:main'
        ],
    },
)
