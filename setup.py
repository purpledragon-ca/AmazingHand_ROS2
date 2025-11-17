from setuptools import setup

package_name = "amazing_hand_ros2"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    data_files=[
        (
            "share/ament_index/resource_index/packages",
            [f"resource/{package_name}"],
        ),
        (f"share/{package_name}", ["package.xml"]),
    ],
    install_requires=[
        "setuptools",
        "rclpy",
        "std_msgs",
        "sensor_msgs",
        "numpy",
        "rustypot",
    ],
    zip_safe=True,
    maintainer="purpledragon",
    maintainer_email="purpledragon.robotic@gmail.com",
    description="ROS2 keyboard and gesture interface for the Amazing Hand demos.",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "amazing_hand_node = amazing_hand_ros2.hand_node:main",
            "amazing_hand_keyboard = amazing_hand_ros2.keyboard_controller:main",
        ],
    },
)
