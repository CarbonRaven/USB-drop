from setuptools import setup, find_packages

setup(
    name="usb-drop-cli",
    version="1.0.0",
    description="CLI tool for USB Drop Campaign Management",
    author="Security Research Team",
    packages=find_packages(),
    install_requires=[
        "click>=8.1.0",
        "requests>=2.31.0",
        "rich>=13.0.0",
        "pyyaml>=6.0",
        "questionary>=2.0.0",
    ],
    entry_points={
        "console_scripts": [
            "usb-drop=usb_drop.cli:cli",
        ],
    },
    python_requires=">=3.9",
)
