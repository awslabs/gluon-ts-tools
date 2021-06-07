import os
from setuptools import setup, find_packages

setup(
    name="qi",
    packages=find_packages("."),
    install_requires=[
        "boto3",
        "click",
        "toolz",
        "pydantic",
        "rich",
        # local dependency to gtstlib
        f"gtstlib @ file://localhost/{os.getcwd()}/../gtstlib/",
    ],
    entry_points={
        "console_scripts": ["qi=qi.__main__:main"],
    },
)
