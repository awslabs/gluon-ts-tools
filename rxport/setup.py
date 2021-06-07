from setuptools import find_packages, setup

setup(
    name="gtst-rxport",
    version="0.1.0",
    author="Amazon",
    packages=find_packages(".", exclude=["test"]),
)
