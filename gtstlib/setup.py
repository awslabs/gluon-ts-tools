from setuptools import find_packages, setup

setup(
    name="gtstlib",
    version="0.1.0",
    author="Amazon",
    packages=find_packages("."),
    description="Gluonts tool library package",
    include_package_data=True,
    install_requires=["boto3", "pydantic", "toolz"],
    entry_points={},
)
